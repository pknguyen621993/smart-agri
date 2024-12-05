from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_utc_timestamp, to_timestamp, year, month, dayofmonth
from pyspark.sql.types import StructType, StringType, FloatType, IntegerType

# Initialize SparkSession with Kafka and Cassandra integration
spark = SparkSession.builder \
    .master("local[*]") \
    .appName("Kafka-Cassandra-WeatherData") \
    .config("spark.cassandra.connection.host","172.18.0.4") \
    .config("spark.cassandra.connection.port","9042") \
    .config("spark.cassandra.auth.username","root") \
    .config("spark.cassandra.auth.password","root") \
    .config("spark.driver.host", "localhost") \
    .getOrCreate()

# Define the schema for the weather data
weather_schema = StructType() \
    .add("sensor_id", StringType()) \
    .add("collected_time", StringType()) \
    .add("rainfall", FloatType()) \
    .add("temperature", FloatType()) \
    .add("humidity", IntegerType()) \
    .add("air_pressure", FloatType()) \
    .add("wind_speed", FloatType()) \
    .add("wind_direction", IntegerType())

# Read from Kafka topic
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "172.18.0.3:9093") \
    .option("subscribe", "weather-sensor") \
    .option("startingOffsets", "latest") \
    .load()

# Deserialize the Kafka value (JSON string) into columns
weather_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), weather_schema).alias("data")) \
    .select("data.*")

weather_df = weather_df.withColumn("collected_time", to_utc_timestamp(to_timestamp(col("collected_time"), "yyyy-MM-dd HH:mm:ss"), "GMT+7")) \
                    .withColumn("year", year(col("collected_time"))) \
                    .withColumn("month", month(col("collected_time"))) \
                    .withColumn("day", dayofmonth(col("collected_time")))

# Write the streaming data to Cassandra
def write_to_cassandra(batch_df, batch_id):
    batch_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode("append") \
        .option("keyspace", "weather_data") \
        .option("table", "weather_sensor") \
        .save()

# Start the streaming query and save to Cassandra
query = weather_df.writeStream \
    .foreachBatch(write_to_cassandra) \
    .outputMode("update") \
    .start()

# Await termination of the streaming query
query.awaitTermination()

# # Write the streaming data to the console
# query = weather_df.writeStream \
#     .outputMode("append") \
#     .format("console") \
#     .option("truncate", "false") \
#     .start()

# # Await termination of the streaming query
# query.awaitTermination()