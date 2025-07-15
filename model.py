from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.regression import LinearRegression ,RandomForestRegressor
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator
from pyspark.sql.functions import count
import pickle


spark = SparkSession.builder.appName("RetailModelTrainingSimplified").getOrCreate()


df = spark.read.csv("new_retail_data.csv", header=True, inferSchema=True)

df = df.fillna({
    "Age": 0, "Total_Purchases": 0, "Ratings": 0.0, "Total_Amount": 0.0,
    "Gender": "Unknown", "Income": "Unknown", "Product_Category": "Unknown",
    "Product_Brand": "Unknown", "Product_Type": "Unknown", 
    "Shipping_Method": "Unknown", "Customer_Segment": "Unknown"
})


from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

print("🔧 Clustering Users by Payment Behavior...")

cat_cols = ["Customer_Segment", "Shipping_Method", "Income","Gender"]
num_cols = ["Total_Amount","Age"]

# Encode categorical features
indexers = [StringIndexer(inputCol=c, outputCol=c+"_idx", handleInvalid="keep") for c in cat_cols]
features = [c + "_idx" for c in cat_cols] + num_cols

# Prepare data
df_cluster = df.dropna(subset=num_cols)
for indexer in indexers:
    df_cluster = indexer.fit(df_cluster).transform(df_cluster)

assembler = VectorAssembler(inputCols=features, outputCol="features", handleInvalid="skip")
df_cluster = assembler.transform(df_cluster)

# KMeans clustering
kmeans = KMeans(k=3, seed=1, featuresCol="features", predictionCol="cluster")
model = kmeans.fit(df_cluster)

# Predict clusters
clustered_df = model.transform(df_cluster)

# Evaluate
evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette", distanceMeasure="squaredEuclidean")
silhouette = evaluator.evaluate(clustered_df)
print(f"📊 KMeans Silhouette Score: {silhouette:.4f}")

# Optional: Analyze clusters vs payment method
clustered_df.select("cluster", "Payment_Method").groupBy("cluster", "Payment_Method").count().orderBy("cluster").show()
# Group by cluster and Income level
income_distribution = clustered_df.groupBy("cluster", "Income").agg(count("*").alias("count"))

# Sort for readability
income_distribution.orderBy("cluster", "count", ascending=False).show(truncate=False)


from pyspark.ml.regression import RandomForestRegressor
rev_features = ["Age", "Total_Purchases", "Ratings", "Customer_Segment"]
rev_indexers = [StringIndexer(inputCol="Customer_Segment", outputCol="Customer_Segment_idx", handleInvalid="keep")]
rev_feat_cols = ["Age", "Total_Purchases", "Ratings", "Customer_Segment_idx"]

# Filter rows with required columns
df_revenue = df.dropna(subset=["Age", "Total_Purchases", "Ratings"])

rev_assembler = VectorAssembler(inputCols=rev_feat_cols, outputCol="features", handleInvalid="skip")
rev_eval = RegressionEvaluator(labelCol="Total_Amount", predictionCol="prediction")

print("🌲 Training Revenue Predictor with Random Forest...")

rf = RandomForestRegressor(featuresCol="features", labelCol="Total_Amount", numTrees=50, maxDepth=8)

rf_pipeline = Pipeline(stages=rev_indexers + [rev_assembler, rf])
rf_model = rf_pipeline.fit(df_revenue)
rf_model.write().overwrite().save("models/revenue_model_rf")

# Evaluate
rf_preds = rf_model.transform(df_revenue)
rf_rmse = rev_eval.setMetricName("rmse").evaluate(rf_preds)
rf_r2 = rev_eval.setMetricName("r2").evaluate(rf_preds)

print(f"🌲 RF Revenue Prediction RMSE: {rf_rmse:.2f}")
print(f"📊 RF Revenue Prediction R²: {rf_r2:.4f}")



# -------------------------------
# 📚 PRODUCT RECOMMENDER (ALS)
# -------------------------------
print("🔧 Training Recommender Model...")

# Index users/items
user_indexer = StringIndexer(inputCol="Customer_ID", outputCol="user", handleInvalid="keep")
item_indexer = StringIndexer(inputCol="Product_Type", outputCol="item", handleInvalid="keep")

df_recommender = df.dropna(subset=["Ratings"])  # ALS requires no nulls in ratings

df_recommender = user_indexer.fit(df_recommender).transform(df_recommender)
item_indexer_model = item_indexer.fit(df_recommender)
df_recommender = item_indexer_model.transform(df_recommender)

# Save mapping from item index to product name
item_labels = item_indexer_model.labels
with open("models/item_index_to_name.pkl", "wb") as f:
    pickle.dump(item_labels, f)

als = ALS(userCol="user", itemCol="item", ratingCol="Ratings", coldStartStrategy="drop", nonnegative=True, rank=10, maxIter=10)
als_model = als.fit(df_recommender)
als_model.write().overwrite().save("models/recommender_model")

# Evaluate
als_preds = als_model.transform(df_recommender)
als_eval = RegressionEvaluator(metricName="rmse", labelCol="Ratings", predictionCol="prediction")
print(f"🧠 Recommender Model RMSE: {als_eval.evaluate(als_preds):.2f}")

def get_recommendations_for_customer(customer_id, num_recs=5):
    from pyspark.ml.recommendation import ALSModel
    from pyspark.sql import Row
    als_model = ALSModel.load("models/recommender_model")
    user_df = spark.createDataFrame([Row(user=float(customer_id))])
    recs = als_model.recommendForUserSubset(user_df, num_recs).collect()
    # Load mapping
    with open("models/item_index_to_name.pkl", "rb") as f:
        item_labels = pickle.load(f)
    if recs:
        recommended = [item_labels[int(row["item"])] for row in recs[0]["recommendations"]]
        return recommended
    return []




