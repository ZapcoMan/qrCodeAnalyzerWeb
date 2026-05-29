import os
import uuid
from typing import Optional
from flask import current_app

def allowed_file(filename: str) -> bool:
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())

def generate_safe_filename(original_filename: str) -> str:
    _, ext = os.path.splitext(original_filename)
    safe_name = str(uuid.uuid4())[:16] + ext.lower()
    return safe_name

def sanitize_path(path: str) -> str:
    path = os.path.normpath(path)
    if path.startswith('..') or '/' in path or '\\' in path:
        raise ValueError("路径包含非法字符")
    return path