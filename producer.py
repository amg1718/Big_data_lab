import pandas as pd
import json
import time
from kafka import KafkaProducer
from pymongo import MongoClient

# Load the dataset
df = pd.read_csv('new_retail_data.csv')  # update with your dataset file name


def get_database():
    # Provide the MongoDB connection string
    connection_string = "mongodb+srv://learninguser:learninguser1234@cluster0.85cr5.mongodb.net/Recomdation_bds"
    client = MongoClient(connection_string)
    return client['Recomdation_bds']



# Kafka Producer setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Simulate real-time by sending one record at a time
for index, row in df.iterrows():
    message = row.to_dict()
    print(f"Sending: {message}")
    producer.send('retail_topic', value=message)
    time.sleep(1)  # Delay to simulate streaming
