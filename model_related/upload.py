from pathlib import Path
from dotenv import load_dotenv
import boto3

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "model_catalog.json"
BUCKET = "jev-exps"
KEY = "model_catalog.json"


def upload_to_s3(path: Path, bucket: str, key: str) -> None:
    s3 = boto3.client("s3")
    s3.upload_file(str(path), bucket, key, ExtraArgs={"ContentType": "application/json"})


if __name__ == "__main__":
    upload_to_s3(CATALOG_PATH, BUCKET, KEY)
    print(f"uploaded {CATALOG_PATH.name} to s3://{BUCKET}/{KEY}")