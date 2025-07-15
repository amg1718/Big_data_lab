from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from bson.json_util import dumps
import pandas as pd
from model import get_recommendations_for_customer

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://learninguser:learninguser1234@cluster0.85cr5.mongodb.net/Recomdation_bds")
db = client["Recomdation_bds"]
collection = db["Recomdation_bds"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_data():
    # Get the last 20 documents sorted by timestamp or _id
    data = collection.find().sort("_id", -1).limit(20)
    return dumps(data)  # Send as JSON

@app.route("/historical_sales")
def historical_sales():
    start = request.args.get("start")
    end = request.args.get("end")
    category = request.args.get("category")
    data = list(collection.find())
    df = pd.DataFrame(data)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce')
        df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors='coerce')
        if start and end:
            start_date = pd.to_datetime(start, format="%Y-%m-%d", errors='coerce')
            end_date = pd.to_datetime(end, format="%Y-%m-%d", errors='coerce')
            df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        if category:
            df = df[df["Product_Type"] == category]
        sales_by_day = df.groupby(df["Date"].dt.date)["Total_Amount"].sum().reset_index()
        sales_by_day.columns = ["Date", "Total_Amount"]
        return sales_by_day.to_json(orient="records")
    return jsonify([])

@app.route("/product_popularity")
def product_popularity():
    start = request.args.get("start")
    end = request.args.get("end")
    data = list(collection.find())
    df = pd.DataFrame(data)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce')
        df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors='coerce')
        if start and end:
            start_date = pd.to_datetime(start, format="%Y-%m-%d", errors='coerce')
            end_date = pd.to_datetime(end, format="%Y-%m-%d", errors='coerce')
            df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        pop = df.groupby("Product_Type")["Total_Amount"].sum().reset_index()
        pop = pop.sort_values(by="Total_Amount", ascending=False)
        pop = pop.rename(columns={"Product_Type": "product", "Total_Amount": "total_sales"})
        return pop.to_json(orient="records")
    return jsonify([])

@app.route("/recommend/<customer_id>")
def recommend(customer_id):
    try:
        recommendations = get_recommendations_for_customer(customer_id)
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/top_customers")
def top_customers():
    data = list(collection.find())
    df = pd.DataFrame(data)
    if not df.empty:
        df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors='coerce')
        top = df.groupby(["Customer_ID", "Name"])["Total_Amount"].sum().reset_index()
        top = top.sort_values(by="Total_Amount", ascending=False).head(10)
        return top.to_json(orient="records")
    return jsonify([])

@app.route("/avg_order_value")
def avg_order_value():
    data = list(collection.find())
    df = pd.DataFrame(data)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce')
        df["Total_Amount"] = pd.to_numeric(df["Total_Amount"], errors='coerce')
        avg = df.groupby(df["Date"].dt.date)["Total_Amount"].mean().reset_index()
        avg.columns = ["Date", "Avg_Order_Value"]
        return avg.to_json(orient="records")
    return jsonify([])

@app.route("/order_status_dist")
def order_status_dist():
    data = list(collection.find())
    df = pd.DataFrame(data)
    if not df.empty:
        dist = df["Order_Status"].value_counts().reset_index()
        dist.columns = ["Order_Status", "Count"]
        return dist.to_json(orient="records")
    return jsonify([])

if __name__ == "__main__":
    app.run(debug=True)
