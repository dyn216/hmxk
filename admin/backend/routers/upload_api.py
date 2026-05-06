"""
文件上传路由
- 提供给三端共用的图片/文件上传接口
- 文件存储于 backend/uploads/ 目录，并通过 /uploads 静态目录对外访问
"""
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Header

from schemas import UploadResponse
from utils import get_current_user_id

router = APIRouter()


# 上传目录：backend/uploads/
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片扩展名
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
# 单文件大小上限：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def _save_file(file: UploadFile, subdir: str, allowed_exts: set) -> dict:
    """统一的文件保存逻辑，返回 url 与元信息"""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if allowed_exts and ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    # 读取并校验大小
    content = file.file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过限制")

    # 按日期分目录存储，避免单目录文件过多
    date_dir = datetime.now().strftime("%Y%m%d")
    target_dir = UPLOAD_DIR / subdir / date_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"{uuid.uuid4().hex}{ext}"
    target_path = target_dir / new_name
    with open(target_path, "wb") as f:
        f.write(content)

    relative_url = f"/uploads/{subdir}/{date_dir}/{new_name}"
    return {
        "url": relative_url,
        "filename": new_name,
        "size": len(content)
    }


@router.post("/image", response_model=UploadResponse)
def upload_image(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """上传图片（头像、商品图、处方图等通用）"""
    # 上传必须登录，防止匿名滥用
    get_current_user_id(authorization)
    return _save_file(file, "image", ALLOWED_IMAGE_EXTS)


@router.post("/file", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """上传通用文件（不限扩展，仍受大小限制约束）"""
    get_current_user_id(authorization)
    return _save_file(file, "file", set())
