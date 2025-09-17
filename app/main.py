# app/main.py
from io import BytesIO
import os
import random
import json
import urllib.request
import datetime
from datetime import timezone

import jwt
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends, Cookie, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse
from pydantic import BaseModel
from PIL import Image

from app.api.controllers import set_user_prediction
from app.aws_related import dynamo, s3
from app.utils import preprocess_image
from app.model import detector
from app.schemas import DetectionResponse


app = FastAPI(
    title="AI Image Detector",
    description="API for detecting if an image is real or AI-generated ",
    version="0.0.1",
)

app.secret_key = "e9aae26be08551392be664d620fb422350a30349899fc254a0f37bfa1b945e36ff20d25b12025e1067f9b69e8b8f2ef0f767f6fff6279e5755668bf4bae88588"


try:
    dynamo.ensure_all()
    dynamo.bootstrap_default_users()
except Exception as e:
    print(f"[warn] bootstrap failed: {e}")


_base_dir = os.path.dirname(os.path.abspath(__file__))
_candidate_in_app = os.path.join(_base_dir, "public")
_candidate_root = os.path.normpath(os.path.join(_base_dir, "..", "public"))
directory_path = _candidate_in_app if os.path.isdir(_candidate_in_app) else _candidate_root

app.mount("/public", StaticFiles(directory=directory_path), name="public")
templates = Jinja2Templates(directory=directory_path)


def generate_access_token(id: str, username: str) -> str:
    payload = {
        "id": id,
        "username": username,
        "exp": datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=30),
    }
    token = jwt.encode(payload, app.secret_key, algorithm="HS256")
    return token


def browser_auth(authToken: str | None = Cookie(default=None)):
    if not authToken:
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login"})
    try:
        user = jwt.decode(authToken, app.secret_key, algorithms=["HS256"])
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=307, detail="Redirect", headers={"Location": "/login"})


def authenticate_token(authToken: str | None = Cookie(default=None)):
    if not authToken:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        user = jwt.decode(authToken, app.secret_key, algorithms=["HS256"])
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    user_id = dynamo.users_get_id_by_credentials(username, password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    token = generate_access_token(user_id, username)
    response = JSONResponse(content={"message": "Logged in"})
    response.set_cookie(key="authToken", value=token, httponly=True, max_age=1800, samesite="lax")
    return response


class FeedbackRequest(BaseModel):
    image_id: str
    model_prediction: str
    user_agrees: bool


@app.post("/user/set_feedback")
async def set_user_feedback(feedback: FeedbackRequest, user=Depends(authenticate_token)):
    try:
        return set_user_prediction(feedback.image_id, feedback.model_prediction, feedback.user_agrees)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/detect")
async def detect_page(user=Depends(browser_auth)):
    return FileResponse(os.path.join(directory_path, "index.html"))


@app.post("/detect", response_model=DetectionResponse)
async def detect_image(request: Request, user=Depends(authenticate_token), file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=401, detail="No image file attached")
        content_type = file.content_type
        if content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Invalid image format. Only PNG/JPEG allowed.")
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB).")

        tensor = preprocess_image(file_content)
        label, confidence = detector.predict(tensor)

        image_id = dynamo.images_insert(file.filename, "", user["id"], label, confidence).get("id")
        s3_key = s3.put_image_to_s3(file.filename, image_id, file_content)
        dynamo.images_update_s3_key(image_id, s3_key)

        referer = request.headers.get("Referer", "")
        main_page_url = request.url_for("main_page")
        if referer.startswith(str(main_page_url)):
            return RedirectResponse(url=f"/result/{image_id}", status_code=303)
        return DetectionResponse(prediction=label, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect-image", response_model=DetectionResponse)
async def detect_image_simple(request: Request, file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=401, detail="No image file attached")
        content_type = file.content_type
        if content_type not in ["image/png", "image/jpeg", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Invalid image format. Only PNG/JPEG allowed.")
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB).")

        tensor = preprocess_image(file_content)
        label, confidence = detector.predict(tensor)
        return DetectionResponse(prediction=label, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def extract_s3_key(s3_url: str) -> str:
    return urlparse(s3_url).path.lstrip("/")


@app.get("/result/{image_id}", response_class=HTMLResponse)
async def result_page(image_id: str, request: Request, user=Depends(browser_auth)):
    image_data = dynamo.images_get_by_id(image_id)
    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")
    s3_key = image_data["s3_key"]
    presigned_url = s3.get_image_from_s3_presigned_url(s3_key)
    if not presigned_url:
        raise HTTPException(status_code=404, detail="Image not found")
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "image_id": image_id,
            "image_url": presigned_url,
            "prediction": image_data["prediction"],
            "confidence": image_data["confidence"],
            "user_prediction": image_data.get("user_prediction"),
        },
    )


@app.get("/login")
async def login_page():
    return FileResponse(os.path.join(directory_path, "login.html"))


@app.get("/")
async def main_page():
    return FileResponse(os.path.join(directory_path, "index.html"))


@app.get("/admin")
async def admin_page(user=Depends(browser_auth)):
    is_admin = dynamo.users_is_admin(user["id"])
    if not is_admin:
        raise HTTPException(status_code=403, detail="Unauthorised user requested admin content.")
    return FileResponse(os.path.join(directory_path, "admin.html"))


@app.get("/admin/uploads")
async def admin_uploads(
    user=Depends(browser_auth),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("uploaded_at"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    username: str | None = None,
    prediction: str | None = None,
):
    is_admin = dynamo.users_is_admin(user["id"])
    if not is_admin:
        raise HTTPException(status_code=403, detail="Unauthorised user requested admin content.")
    allowed_sort_fields = ["uploaded_at", "id", "filename", "prediction", "image_id"]
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    images = dynamo.images_list(limit, offset, sort_by, order, username, prediction)
    for img in images:
        img["image_url"] = s3.get_image_from_s3_presigned_url(img["s3_key"])
        uid = img.get("user_id")
        img["username"] = dynamo.users_get_username_by_id(uid) if uid else None
    return images


@app.get("/game/image")
def get_game_image(user=Depends(browser_auth)):
    sources = [("https://thispersondoesnotexist.com", "ai"), ("https://randomuser.me/api/?inc=picture", "real")]
    url, answer = random.choice(sources)
    if answer == "real":
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read().decode())
            image_url = data["results"][0]["picture"]["large"]
            with urllib.request.urlopen(image_url) as img_res:
                data = img_res.read()
    else:
        with urllib.request.urlopen(url) as res:
            data = res.read()

    img = Image.open(BytesIO(data)).convert("RGB")
    img = img.resize((200, 200))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    response = StreamingResponse(buf, media_type="image/jpeg")
    response.headers["user_id"] = str(user["id"])
    response.headers["answer"] = answer
    return response


@app.get("/game")
async def game_page(user=Depends(browser_auth)):
    return FileResponse(os.path.join(directory_path, "game.html"))


@app.post("/user/save_accuracy")
async def save_accuracy(request: Request, user=Depends(browser_auth)):
    data = await request.json()
    accuracy = float(data.get("accuracy", 0))
    try:
        result = dynamo.put_accuracy(user["id"], accuracy)
        return {"status": "updated" if result.get("updated") else "error"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")


@app.get("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie(key="authToken", path="/")
    return response