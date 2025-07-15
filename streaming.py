from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, DoubleType





spark = SparkSession.builder \
    .appName("KafkaStreamToMongo") \
    .master("local[*]") \
    .config("spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1,"
        "org.mongodb.spark:mongo-spark-connector_2.13:10.3.0") \
    .getOrCreate()

# Define the schema matching Kafka JSON data
schema = StructType() \
    .add("Transaction_ID", DoubleType()) \
    .add("Customer_ID", DoubleType()) \
    .add("Name", StringType()) \
    .add("Email", StringType()) \
    .add("Phone", DoubleType()) \
    .add("Address", StringType()) \
    .add("City", StringType()) \
    .add("State", StringType()) \
    .add("Zipcode", DoubleType()) \
    .add("Country", StringType()) \
    .add("Age", DoubleType()) \
    .add("Gender", StringType()) \
    .add("Income", StringType()) \
    .add("Customer_Segment", StringType()) \
    .add("Date", StringType()) \
    .add("Year", DoubleType()) \
    .add("Month", StringType()) \
    .add("Time", StringType()) \
    .add("Total_Purchases", DoubleType()) \
    .add("Amount", DoubleType()) \
    .add("Total_Amount", DoubleType()) \
    .add("Product_Category", StringType()) \
    .add("Product_Brand", StringType()) \
    .add("Product_Type", StringType()) \
    .add("Feedback", StringType()) \
    .add("Shipping_Method", StringType()) \
    .add("Payment_Method", StringType()) \
    .add("Order_Status", StringType()) \
    .add("Ratings", DoubleType()) \
    .add("products", StringType())




# Read streaming data from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "retail_topic") \
    .option("startingOffsets", "earliest") \
    .load()

# Extract the JSON string from Kafka and parse it using the defined schema
parsed_df = df.selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), schema).alias("data")) \
    .select("data.*")

# Write the parsed data to the console in append mode
query = parsed_df.writeStream \
    .format("mongodb") \
    .option("spark.mongodb.connection.uri", "mongodb+srv://learninguser:learninguser1234@cluster0.85cr5.mongodb.net/Recomdation_bds.Recomdation_bds") \
    .option("spark.mongodb.database", "Recomdation_bds") \
    .option("spark.mongodb.collection", "Recomdation_bds") \
    .option("checkpointLocation", "/tmp/spark_checkpoint") \
    .outputMode("append") \
    .start()
print(spark.version)





# Keep the stream running
query.awaitTermination()

# =============================
# REAL-TIME PREDICTION PIPELINE
# =============================

# from pyspark.sql import SparkSession
# from pyspark.sql.functions import from_json, col, to_json, struct
# from pyspark.sql.types import StructType, StringType, DoubleType
# from pyspark.ml import PipelineModel

# # 1. Create Spark Session
# spark = SparkSession.builder \
#     .appName("KafkaStreamWithMLlibPrediction") \
#     .master("local[*]") \
#     .config("spark.jars.packages", \
#             "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1," \
#             "org.mongodb.spark:mongo-spark-connector_2.13:10.3.0") \
#     .getOrCreate()

# # 2. Define JSON Schema
# schema = StructType() \
#     .add("Transaction_ID", DoubleType()) \
#     .add("Customer_ID", DoubleType()) \
#     .add("Name", StringType()) \
#     .add("Email", StringType()) \
#     .add("Phone", DoubleType()) \
#     .add("Address", StringType()) \
#     .add("City", StringType()) \
#     .add("State", StringType()) \
#     .add("Zipcode", DoubleType()) \
#     .add("Country", StringType()) \
#     .add("Age", DoubleType()) \
#     .add("Gender", StringType()) \
#     .add("Income", StringType()) \
#     .add("Customer_Segment", StringType()) \
#     .add("Date", StringType()) \
#     .add("Year", DoubleType()) \
#     .add("Month", StringType()) \
#     .add("Time", StringType()) \
#     .add("Total_Purchases", DoubleType()) \
#     .add("Amount", DoubleType()) \
#     .add("Total_Amount", DoubleType()) \
#     .add("Product_Category", StringType()) \
#     .add("Product_Brand", StringType()) \
#     .add("Product_Type", StringType()) \
#     .add("Feedback", StringType()) \
#     .add("Shipping_Method", StringType()) \
#     .add("Payment_Method", StringType()) \
#     .add("Order_Status", StringType()) \
#     .add("Ratings", DoubleType()) \
#     .add("products", StringType())

# # 3. Read from Kafka
# df = spark.readStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("subscribe", "retail_topic") \
#     .option("startingOffsets", "earliest") \
#     .load()

# # 4. Parse Kafka JSON
# data_df = df.selectExpr("CAST(value AS STRING) as json_string") \
#     .select(from_json(col("json_string"), schema).alias("data")) \
#     .select("data.*")

# # 5. Load Trained MLlib Model
# model = PipelineModel.load("mllib_model")

# # 6. Select Features Required for Prediction
# features_df = data_df.select("Age", "Gender", "Product_Category")

# # 7. Generate Predictions
# predicted_df = model.transform(features_df)

# # 8. Combine with Original Data
# final_df = data_df.join(predicted_df.select("Age", "Gender", "Product_Category", "prediction"),
#                         on=["Age", "Gender", "Product_Category"],
#                         how="left")

# # 9. Save Predictions to MongoDB
# mongo_query = final_df.writeStream \
#     .format("mongodb") \
#     .option("spark.mongodb.connection.uri", "mongodb+srv://learninguser:learninguser1234@cluster0.85cr5.mongodb.net/Recomdation_bds.Predicted_Records") \
#     .option("spark.mongodb.database", "Recomdation_bds") \
#     .option("spark.mongodb.collection", "Predicted_Records") \
#     .option("checkpointLocation", "/tmp/spark_predict_checkpoint") \
#     .outputMode("append") \
#     .start()

# # 10. [Optional] Write Back to Kafka
# to_kafka_df = final_df.selectExpr("to_json(struct(*)) AS value")
# kafka_output = to_kafka_df.writeStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("topic", "predicted_topic") \
#     .option("checkpointLocation", "/tmp/kafka_output_checkpoint") \
#     .outputMode("append") \
#     .start()

# # 11. Keep Streams Running
# spark.streams.awaitAnyTermination()



