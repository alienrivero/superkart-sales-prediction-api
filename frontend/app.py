import os

import pandas as pd
import requests
import streamlit as st

# Base URL of the Flask backend (Docker network alias by default; override with BACKEND_URL)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:7860")

# Feature columns expected by the deployed model
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

# Reference year used to compute Store_Age_Years during training
REFERENCE_YEAR = 2025

# Each store has one fixed size / city tier / type in the training data, so the user picks a
# store and its attributes are filled in, which avoids store profiles the model has never seen
STORES = {
    "OUT001": {"Store_Size": "High", "Store_Location_City_Type": "Tier 2", "Store_Type": "Supermarket Type1", "Established": 1987},
    "OUT002": {"Store_Size": "Small", "Store_Location_City_Type": "Tier 3", "Store_Type": "Food Mart", "Established": 1998},
    "OUT003": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 1", "Store_Type": "Departmental Store", "Established": 1999},
    "OUT004": {"Store_Size": "Medium", "Store_Location_City_Type": "Tier 2", "Store_Type": "Supermarket Type2", "Established": 2009},
}
KNOWN_STORE_PROFILES = {
    (s["Store_Size"], s["Store_Location_City_Type"], s["Store_Type"]) for s in STORES.values()
}

# Product type determines the Product_Id prefix (FD = food, DR = drinks, NC = non-consumable)
# and the perishable category, exactly as engineered in the training notebook
DRINKS = ["Hard Drinks", "Soft Drinks"]
NON_CONSUMABLES = ["Health and Hygiene", "Household", "Others"]
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]
PRODUCT_TYPES = sorted(
    DRINKS + NON_CONSUMABLES + PERISHABLES
    + ["Baking Goods", "Canned", "Frozen Foods", "Snack Foods", "Starchy Foods"]
)


def product_id_char(product_type):
    """Product_Id prefix implied by the product type."""
    if product_type in DRINKS:
        return "DR"
    if product_type in NON_CONSUMABLES:
        return "NC"
    return "FD"


st.set_page_config(page_title="SuperKart Sales Forecast", layout="wide")
st.title("SuperKart Sales Forecast")
st.write(
    "Forecast product–store sales revenue with the deployed SuperKart model. "
    "Use **Online prediction** for a single product in a store, or **Batch prediction** "
    "to score many rows from a CSV file."
)

tab_online, tab_batch = st.tabs(["Online prediction", "Batch prediction"])

# -------------------- Online Prediction --------------------
with tab_online:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Store**")
        store_id = st.selectbox(
            "Store",
            list(STORES),
            index=3,
            format_func=lambda s: f"{s} – {STORES[s]['Store_Type']}",
        )
        store = STORES[store_id]
        store_age = REFERENCE_YEAR - store["Established"]
        st.caption(
            f"Size: **{store['Store_Size']}** · City: **{store['Store_Location_City_Type']}** · "
            f"Established: **{store['Established']}** (age {store_age} years)"
        )

    with col2:
        st.markdown("**Product**")
        product_type = st.selectbox("Product type", PRODUCT_TYPES, index=PRODUCT_TYPES.index("Frozen Foods"))
        id_char = product_id_char(product_type)
        # Non-consumables are always "No Sugar"; food and drinks are "Low Sugar" or "Regular"
        sugar_options = ["No Sugar"] if id_char == "NC" else ["Low Sugar", "Regular"]
        sugar_content = st.selectbox("Sugar content", sugar_options)

    col3, col4, col5 = st.columns(3)
    with col3:
        weight = st.number_input("Product weight", min_value=4.0, max_value=22.0, value=12.66, step=0.01,
                                 help="Range seen in training: 4 – 22")
    with col4:
        allocated_area = st.number_input("Allocated display area", min_value=0.004, max_value=0.298, value=0.027,
                                         step=0.001, format="%.3f", help="Share of the store's display area (0.004 – 0.298)")
    with col5:
        mrp = st.number_input("Product MRP", min_value=31.0, max_value=266.0, value=117.08, step=0.01,
                              help="Range seen in training: 31 – 266")

    input_data = {
        "Product_Weight": weight,
        "Product_Sugar_Content": sugar_content,
        "Product_Allocated_Area": allocated_area,
        "Product_MRP": mrp,
        "Store_Size": store["Store_Size"],
        "Store_Location_City_Type": store["Store_Location_City_Type"],
        "Store_Type": store["Store_Type"],
        "Product_Id_char": id_char,
        "Store_Age_Years": store_age,
        "Product_Type_Category": "Perishables" if product_type in PERISHABLES else "Non Perishables",
    }

    with st.expander("Features sent to the API"):
        st.json(input_data)

    if st.button("Predict", type="primary"):
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=input_data, timeout=30)
            if response.status_code == 200:
                prediction = response.json()["Predicted Sales"]
                st.success(f"Predicted Sales: {prediction:,.2f}")
            else:
                st.error(f"API error ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Unable to connect to the prediction API: {exc}")

# -------------------- Batch Prediction --------------------
with tab_batch:
    st.write("Upload a CSV file with these columns:")
    st.markdown(", ".join(f"`{col}`" for col in FEATURE_COLUMNS))

    uploaded_file = st.file_uploader("Upload CSV file for batch prediction", type=["csv"])

    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)
        missing = [col for col in FEATURE_COLUMNS if col not in batch_df.columns]

        if missing:
            st.error(f"The file is missing required columns: {missing}")
        else:
            st.write(f"Preview of uploaded data ({len(batch_df)} rows):")
            st.dataframe(batch_df.head())

            if st.button("Predict Batch", type="primary"):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/v1/predictbatch",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                        timeout=120,
                    )
                    if response.status_code == 200:
                        predictions = response.json()
                        results = batch_df.copy()
                        results["Predicted_Sales"] = [predictions[str(i)] for i in range(len(results))]
                        # Flag rows describing a store profile that does not exist in the training data
                        results["Known_Store_Profile"] = [
                            profile in KNOWN_STORE_PROFILES
                            for profile in zip(results["Store_Size"], results["Store_Location_City_Type"], results["Store_Type"])
                        ]

                        st.success(f"Batch predictions completed for {len(results)} rows")
                        m1, m2 = st.columns(2)
                        m1.metric("Total predicted sales", f"{results['Predicted_Sales'].sum():,.2f}")
                        m2.metric("Average per row", f"{results['Predicted_Sales'].mean():,.2f}")
                        # Show the prediction and the profile flag first, then the input features
                        st.dataframe(results[["Predicted_Sales", "Known_Store_Profile"] + FEATURE_COLUMNS])

                        n_unknown = int((~results["Known_Store_Profile"]).sum())
                        if n_unknown:
                            st.warning(
                                f"{n_unknown} row(s) describe a store size / city tier / store type combination "
                                "that does not exist in the training data. Treat those predictions with caution."
                            )

                        st.download_button(
                            "Download predictions as CSV",
                            results.to_csv(index=False),
                            file_name="superkart_batch_predictions.csv",
                            mime="text/csv",
                        )
                    else:
                        st.error(f"API error ({response.status_code}): {response.text}")
                except requests.exceptions.RequestException as exc:
                    st.error(f"Unable to connect to the prediction API: {exc}")
