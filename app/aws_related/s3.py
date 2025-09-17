import os
import re
import io
import boto3
from botocore.exceptions import ClientError
import torch

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
MODEL_KEY = os.getenv("AWS_S3_MODEL_KEY", "model/model.pth")

_session = boto3.session.Session(region_name=AWS_REGION)
_s3 = _session.client("s3")

def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name or "file")

def put_image_to_s3(filename: str, image_id: str, data: bytes) -> str:
    key = f"uploads/{image_id}/{_safe_filename(filename)}"
    _s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType="image/jpeg")
    return key

def get_image_from_s3_presigned_url(key: str, expires: int = 3600) -> str | None:
    if not key:
        return None
    try:
        return _s3.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires)
    except ClientError:
        return None

def delete_image_from_s3(filename: str, image_id: str):
    key = f"uploads/{image_id}/{_safe_filename(filename)}"
    try:
        _s3.delete_object(Bucket=S3_BUCKET, Key=key)
    except ClientError:
        pass

def load_model():
    buf = io.BytesIO()
    obj = _s3.get_object(Bucket=S3_BUCKET, Key=MODEL_KEY)
    buf.write(obj["Body"].read())
    buf.seek(0)
    state = torch.load(buf, map_location="cpu")
    return state