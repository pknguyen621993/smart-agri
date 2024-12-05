import json
import time
from kafka import KafkaProducer
from datetime import datetime
import pandas as pd
import math

# Kafka setup
KAFKA_TOPIC = 'weather-sensor'
KAFKA_SERVER = 'localhost:9092'
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to simulate weather data
def generate_weather_data():
    df = pd.read_csv('simulate-data.csv', usecols=[0,1,2,3,4,6,7])
    df.rename(columns={'Times': 'collected_time', 'Mua': 'rainfall',
                       'NhietDo': 'temperature', 'DoAm': 'humidity',
                       'KhiAp': 'air_pressure', 'TDoGioAvg10': 'wind_speed',
                       'HGioAvg10': 'wind_direction'}, inplace=True)
    
    df['collected_time'] = pd.to_datetime(df['collected_time'], format='%d/%m/%Y %H:%M')

    df['day'] = df['collected_time'].dt.day
    df['hour'] = df['collected_time'].dt.hour
    df['minute'] = df['collected_time'].dt.minute

    now = datetime.now()
    today = now.day
    hour = now.hour
    minute = math.floor(now.minute / 10) * 10
    formatted_day = str(today).rjust(2, '0')
    formatted_month = str(now.month).rjust(2, '0')
    formatted_hour = str(hour).rjust(2, '0')
    formatted_minute = str(minute).rjust(2, '0')

    collected_time = f'{now.year}-{formatted_month}-{formatted_day} {formatted_hour}:{formatted_minute}:00'

    df = df[(df['day'] == today) & (df['hour'] == hour) & (df['minute'] == minute)]
    df['sensor_id'] = 'A1'
    df['collected_time'] = collected_time

    result_df = df[['sensor_id', 'collected_time', 'rainfall', 'temperature', 'humidity', 'air_pressure', 'wind_speed', 'wind_direction']]
    
    row = result_df.iloc[0]

    weather_data = {
        'sensor_id': row['sensor_id'],
        'collected_time': row['collected_time'],
        'rainfall': float(row['rainfall']),
        'temperature': float(row['temperature']),
        'humidity': int(row['humidity']),
        'air_pressure': float(row['air_pressure']),
        'wind_speed': float(row['wind_speed']),
        'wind_direction': int(row['wind_direction'])
    }

    return weather_data

# Sending data to Kafka every minute
def send_weather_data():
    while True:
        weather_data = generate_weather_data()
        print(f"Sending: {weather_data}")
        producer.send(KAFKA_TOPIC, weather_data)
        producer.flush()
        time.sleep(6000)

if __name__ == "__main__":
    send_weather_data()