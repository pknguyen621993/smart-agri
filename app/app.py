import streamlit as st
import requests
from minio import Minio
from minio.error import S3Error
import io

# Set up the page structure
st.set_page_config(page_title="Image Classification & Feature Prediction App", layout="wide")

# Define the API URLs
image_api_url = 'http://127.0.0.1:5000/predict_image'
features_api_url = 'http://127.0.0.1:5000/predict_features'

# Define a function to call the image classification API
def predict_image(image_file):
    files = {'file': image_file}
    response = requests.post(image_api_url, files=files)
    return response.json()

# Define a function to call the features prediction API
def predict_features(data):
    response = requests.post(features_api_url, json=data)
    return response.json()

# Initialize MinIO client
minio_client = Minio(
    "localhost:9000",  # Your MinIO server URL and port
    access_key="BmH28TYs8KDfglenqYGA",  # MinIO access key
    secret_key="rJaNSs5pNnXrR7aOmtc7P11LQVvXQDgqA5eMAdpI",  # MinIO secret key
    secure=False  # Set to True if using HTTPS
)

# Bucket where the images will be stored
bucket_name = "rice-leaf-diease"

# Function to upload image to MinIO
def upload_to_minio(image_data, folder_name, file_name):
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Create the object name with the folder
        object_name = f"{folder_name}/{file_name}"

        # Upload the image to the specified folder in MinIO
        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(image_data.read()),  # Convert the uploaded file to bytes
            length=image_data.size,
            content_type=image_data.type
        )
        st.success(f"Image successfully uploaded to MinIO in folder: {folder_name}")
    except S3Error as err:
        st.error(f"MinIO error: {err}")

# Add page navigation
page = st.sidebar.selectbox("Choose a page", ["Feature Prediction", "Image Classification"])

# Page 1: Feature Prediction
if page == "Feature Prediction":
    st.title("Feature Prediction")
    st.write("Input the following features to make a prediction:")

    # Feature input fields
    temperature = st.number_input("Temperature (°C)", value=30.5)
    humidity = st.number_input("Humidity (%)", value=88.0)
    rainfall = st.number_input("Rainfall (mm)", value=25.0)
    ph = st.number_input("Soil pH", value=5.8)
    light = st.number_input("Light (hours)", value=7.2)
    wind_speed = st.number_input("Wind Speed (km/h)", value=6.0)

    # When the button is clicked, call the feature prediction API
    if st.button("Predict"):
        # Prepare the data to be sent to the API
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "rainfall": rainfall,
            "ph": ph,
            "light": light,
            "wind_speed": wind_speed
        }

        # Call the feature prediction API
        with st.spinner("Predicting..."):
            result = predict_features(data)

        if 'y_pred_new' in result:
            # prediction = "Positive" if result['y_pred_new'] else "Negative"
            # st.success(f"Prediction: {prediction} (Probability: {result['y_proba_new']})")
            st.success(f"Probability: {result['y_proba_new']}")
        else:
            st.error(f"Error: {result.get('error', 'Unknown error occurred')}")

# Page 2: Image Classification
elif page == "Image Classification":
    st.title("Image Classification")
    st.write("Upload an image to classify.")

    uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])

    if uploaded_file is not None:
        st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)

        if st.button("Classify Image"):
            # Call the image classification API
            with st.spinner("Classifying..."):
                result = predict_image(uploaded_file)

            if 'predicted_label' in result:
                predicted_label = result['predicted_label']
                st.success(f"Predicted Label: {predicted_label}")

                # Convert the predicted label into a folder-friendly format
                folder_name = predicted_label.lower().replace(" ", "-")

                # Reset the file pointer again before uploading to MinIO
                uploaded_file.seek(0)

                # Upload the image to MinIO in the corresponding folder
                upload_to_minio(uploaded_file, folder_name, uploaded_file.name)
            else:
                st.error(f"Error: {result.get('error', 'Unknown error occurred')}")

