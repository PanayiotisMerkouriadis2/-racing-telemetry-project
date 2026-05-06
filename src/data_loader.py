import streamlit as st
import boto3
import pandas as pd

# =====================================================
# STREAMLIT-CACHED DATA LOADER (FAST + SAFE)
# =====================================================

@st.cache_data(show_spinner="Loading telemetry from AWS S3...")
def load_data():

    # =================================================
    # AWS CREDENTIALS (STREAMLIT SECRETS)
    # =================================================
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
    AWS_REGION = st.secrets["AWS_DEFAULT_REGION"]

    # =================================================
    # S3 CONFIG
    # =================================================
    BUCKET_NAME = "racing-telemetry-pany-01"
    FILE_NAME = "amg_gt3_brands.parquet"

    # =================================================
    # CONNECT TO AWS S3
    # =================================================
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)

    df = pd.read_csv(obj["Body"])

    # =================================================
    # CLEAN COLUMN NAMES (COMMON STREAMLIT ISSUE FIX)
    # =================================================
    df.columns = df.columns.str.strip()

    # =================================================
    # BASIC SAFETY CONVERSIONS
    # =================================================
    numeric_cols = ["rpm", "throttle", "brake", "lapNum"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["rpm", "throttle", "brake", "lapNum"])

    return df