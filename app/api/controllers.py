from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from api.models import (
    get_uploaded_images,
    insert_user,
    insert_image,
    update_user_prediction,
    delete_image as delete_image_row,
    get_image_by_id,
)
from aws_related.s3 import delete_image_from_s3
from urllib.parse import urlparse

router = APIRouter()

def _extract_s3_key_from_url(s3_url: str) -> str:
    return urlparse(s3_url).path.lstrip('/')

def get_images():
    try:
        return JSONResponse(content=get_uploaded_images())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_user(request: Request):
    data = await request.json()
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    try:
        is_admin = data.get("is_admin")
        return insert_user(username, 0 if not is_admin else is_admin)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def upload_image(request: Request):
    data = await request.json()
    filename = data.get("filename")
    user_id = data.get("user_id")
    prediction = data.get("prediction")
    confidence = data.get("confidence")
    s3_key = data.get("s3_key")
    s3_url = data.get("s3_url")
    if not filename or not user_id:
        raise HTTPException(status_code=400, detail="filename and user_id are required")
    if not s3_key and s3_url:
        s3_key = _extract_s3_key_from_url(s3_url)
    try:
        return insert_image(filename, s3_key or "", user_id, prediction, confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def delete_image(image_id: str):
    try:
        image = get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        result = delete_image_row(image_id)
        if not result.get("deleted"):
            raise HTTPException(status_code=404, detail="Image not found")
        delete_image_from_s3(image.get("filename"), image_id)
        return {"message": "Image deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def set_user_prediction(image_id: str, model_prediction: str, user_agrees: bool):
    try:
        user_prediction = model_prediction if user_agrees else ("AI-generated" if model_prediction == "Real" else "Real")
        result = update_user_prediction(image_id, user_prediction)
        if not result.get("updated"):
            raise HTTPException(status_code=404, detail="Image not found")
        return {"status": "success", "message": "User prediction updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))