import streamlit as st
import pandas as pd
import requests

# Base URL of the Flask backend (Docker DNS name = container name)
BACKEND_URL = "http://backend:7860"

st.title("SuperKart Sales Prediction")
st.write(
    "Forecast product–store sales revenue using the deployed SuperKart model. "
    "Use **Online Prediction** for a single product–store pair, or **Batch Prediction** "
    "to score many rows from a CSV."
)

# -------------------- Online Prediction --------------------
st.subheader("Online Prediction")

col1, col2 = st.columns(2)

with col1:
    Product_Weight = st.number_input("Product Weight", min_value=0.0, value=12.66, step=0.01)
    Product_Sugar_Content = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
    Product_Allocated_Area = st.number_input(
        "Product Allocated Area", min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f"
    )
    Product_MRP = st.number_input("Product MRP", min_value=0.0, value=117.08, step=0.01)
    Store_Size = st.selectbox("Store Size", ["High", "Medium", "Small"])

with col2:
    Store_Location_City_Type = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"])
    Store_Type = st.selectbox(
        "Store Type",
        ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"],
    )
    Product_Id_char = st.selectbox("Product Id Character (FD / DR / NC)", ["FD", "DR", "NC"])
    Store_Age_Years = st.number_input("Store Age (Years)", min_value=0, value=16, step=1)
    Product_Type_Category = st.selectbox("Product Type Category", ["Perishables", "Non Perishables"])

input_data = {
    "Product_Weight": Product_Weight,
    "Product_Sugar_Content": Product_Sugar_Content,
    "Product_Allocated_Area": Product_Allocated_Area,
    "Product_MRP": Product_MRP,
    "Store_Size": Store_Size,
    "Store_Location_City_Type": Store_Location_City_Type,
    "Store_Type": Store_Type,
    "Product_Id_char": Product_Id_char,
    "Store_Age_Years": Store_Age_Years,
    "Product_Type_Category": Product_Type_Category,
}

if st.button("Predict", type="primary"):
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=input_data, timeout=30)
        if response.status_code == 200:
            prediction = response.json()["Predicted Sales"]
            st.success(f"Predicted Sales: {prediction}")
        else:
            st.error(f"API error ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as exc:
        st.error(f"Unable to connect to the prediction API: {exc}")

# -------------------- Batch Prediction --------------------
st.subheader("Batch Prediction")
st.caption(
    "Upload a CSV with columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
    "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
    "Store_Age_Years, Product_Type_Category"
)

uploaded_file = st.file_uploader("Upload CSV file for batch prediction", type=["csv"])

if uploaded_file is not None:
    preview = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded data:")
    st.dataframe(preview.head())
    # Reset file pointer so it can be sent to the API
    uploaded_file.seek(0)

    if st.button("Predict Batch", type="primary"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/v1/predictbatch",
                files={"file": uploaded_file},
                timeout=120,
            )
            if response.status_code == 200:
                st.write("Batch predictions (row index → predicted sales):")
                st.json(response.json())
            else:
                st.error(f"API error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Unable to connect to the prediction API: {exc}")
