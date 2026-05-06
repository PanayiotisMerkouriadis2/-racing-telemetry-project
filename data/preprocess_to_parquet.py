import boto3
import pandas as pd



s3 = boto3.client("s3")

BUCKET = "racing-telemetry-pany-01"
INPUT_FILE = "AMGGT3-BRANDSHATCH.csv"
OUTPUT_FILE = "AMGGT3.parquet"



obj = s3.get_object(Bucket=BUCKET, Key=INPUT_FILE)
df = pd.read_csv(obj["Body"])

print("Loaded raw CSV")



cols = ["rpm", "throttle", "brake", "lapNum"]

for c in cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna(subset=cols)



df.to_parquet(OUTPUT_FILE, index=False)

print("Saved as parquet")



s3.upload_file(OUTPUT_FILE, BUCKET, OUTPUT_FILE)

print("Uploaded parquet to S3")