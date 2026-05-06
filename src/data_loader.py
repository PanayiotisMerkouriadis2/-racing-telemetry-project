import io
import boto3
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner="Loading telemetry from AWS S3...")
def load_data():
    AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
    AWS_REGION = st.secrets["AWS_DEFAULT_REGION"]

    BUCKET_NAME = "racing-telemetry-pany-01"
    FILE_NAME = "amg_gt3_brands.parquet"  # update path if in a subfolder e.g. "data/amg_gt3_brands.parquet"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    # List files so you can see exact keys if it still fails
    try:
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
    except s3.exceptions.NoSuchKey:
        keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET_NAME).get("Contents", [])]
        raise FileNotFoundError(
            f"'{FILE_NAME}' not found in bucket '{BUCKET_NAME}'.\n"
            f"Available keys: {keys}"
        )

    # Read parquet correctly
    buffer = io.BytesIO(obj["Body"].read())
    df = pd.read_parquet(buffer)

    df.columns = df.columns.str.strip()

    numeric_cols = ["rpm", "throttle", "brake", "lapNum"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["rpm", "throttle", "brake", "lapNum"])
    return df