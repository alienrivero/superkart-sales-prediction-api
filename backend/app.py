# Import necessary libraries
import joblib  # For loading the serialized model
import pandas as pd  # For data manipulation
from flask import Flask, request, jsonify  # For creating the Flask API

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Predictor")

# Load the trained machine learning pipeline (preprocessing + model)
model = joblib.load("superkart_model.joblib")

# Feature columns the pipeline was trained on
FEATURE_COLUMNS = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]


def missing_features(columns):
    """Return the required feature columns that are absent from `columns`."""
    return [col for col in FEATURE_COLUMNS if col not in columns]


@superkart_api.get("/")
def home():
    """Health / welcome endpoint."""
    return "Welcome to the SuperKart Sales Prediction API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """
    Online inference endpoint.
    Expects a JSON payload with the engineered feature columns and returns
    the predicted Product_Store_Sales_Total. Invalid requests get HTTP 400.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object with the feature values."}), 400

    missing = missing_features(data)
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    # Keep only the expected features so extra keys in the payload are ignored
    input_data = pd.DataFrame([{col: data[col] for col in FEATURE_COLUMNS}])

    try:
        prediction = round(float(model.predict(input_data)[0]), 2)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid feature values: {exc}"}), 400

    return jsonify({"Predicted Sales": prediction})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """
    Batch inference endpoint.
    Expects a CSV file upload (multipart form field name: 'file') containing
    the same feature columns used during training. Returns a JSON object
    mapping each row index to its predicted sales value.
    """
    file = request.files.get("file")
    if file is None:
        return jsonify({"error": "Upload a CSV file in the multipart form field 'file'."}), 400

    try:
        input_data = pd.read_csv(file)
    except Exception as exc:  # empty or malformed CSV
        return jsonify({"error": f"Could not read the CSV file: {exc}"}), 400

    if input_data.empty:
        return jsonify({"error": "The CSV file has no data rows."}), 400

    missing = missing_features(input_data.columns)
    if missing:
        return jsonify({"error": f"Missing required columns: {missing}"}), 400

    try:
        predictions = [round(float(p), 2) for p in model.predict(input_data[FEATURE_COLUMNS])]
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"Invalid feature values: {exc}"}), 400

    # Keys are row indices so the client can align predictions with input rows
    return jsonify(dict(zip(range(len(predictions)), predictions)))


if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860)
