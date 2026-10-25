# Import necessary libraries
import joblib  # For loading the serialized model
import pandas as pd  # For data manipulation
from flask import Flask, request, jsonify  # For creating the Flask API

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Predictor")

# Load the trained machine learning pipeline (preprocessing + model)
model = joblib.load("superkart_model.joblib")


@superkart_api.get("/")
def home():
    """Health / welcome endpoint."""
    return "Welcome to the SuperKart Sales Prediction API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """
    Online inference endpoint.
    Expects a JSON payload with the engineered feature columns and returns
    the predicted Product_Store_Sales_Total.
    """
    data = request.get_json()

    sample = {
        "Product_Weight": data["Product_Weight"],
        "Product_Sugar_Content": data["Product_Sugar_Content"],
        "Product_Allocated_Area": data["Product_Allocated_Area"],
        "Product_MRP": data["Product_MRP"],
        "Store_Size": data["Store_Size"],
        "Store_Location_City_Type": data["Store_Location_City_Type"],
        "Store_Type": data["Store_Type"],
        "Product_Id_char": data["Product_Id_char"],
        "Store_Age_Years": data["Store_Age_Years"],
        "Product_Type_Category": data["Product_Type_Category"],
    }

    input_data = pd.DataFrame([sample])
    prediction = round(float(model.predict(input_data)[0]), 2)

    return jsonify({"Predicted Sales": prediction})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """
    Batch inference endpoint.
    Expects a CSV file upload (multipart form field name: 'file') containing
    the same feature columns used during training. Returns a JSON object
    mapping each row index to its predicted sales value.
    """
    file = request.files["file"]
    input_data = pd.read_csv(file)

    predictions = [round(float(p), 2) for p in model.predict(input_data).tolist()]
    # Keys are row indices so the client can align predictions with input rows
    return dict(zip(range(len(predictions)), predictions))


if __name__ == "__main__":
    superkart_api.run(debug=True)
