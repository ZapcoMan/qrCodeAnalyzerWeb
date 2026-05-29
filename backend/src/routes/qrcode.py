import os
import uuid
import json
from flask import Blueprint, request, jsonify
from io import BytesIO
from PIL import Image

from src.services.decoder import QRCodeDecoder
from src.utils.url import download_image
from src.utils.security import allowed_file
from src.utils.cache import cache_manager
from src.schemas.response import APIResponse
from src.utils.logger import setup_logger

logger = setup_logger()
qrcode_bp = Blueprint('qrcode', __name__)
decoder = QRCodeDecoder()

def generate_temp_filename() -> str:
    return f"temp_{uuid.uuid4().hex[:16]}.png"

@qrcode_bp.route('/decode', methods=['POST'])
def decode_qr_endpoint():
    """
    解析上传图片中的二维码
    ---
    tags:
      - 二维码解析
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: 包含二维码的图片文件（支持PNG、JPG、GIF、BMP、WebP格式）
    responses:
      200:
        description: 解析成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                result:
                  type: string
                  example: https://example.com
                type:
                  type: string
                  example: QRCODE
            code:
              type: integer
              example: 200
      400:
        description: 请求参数错误或无法解析二维码
      500:
        description: 服务器内部错误
    """
    try:
        if 'file' not in request.files:
            return jsonify(APIResponse.error_response('没有上传文件', 400).to_dict()), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(APIResponse.error_response('没有选择文件', 400).to_dict()), 400
        
        if file:
            if not allowed_file(file.filename):
                return jsonify(APIResponse.error_response('不支持的文件类型', 400).to_dict()), 400
            
            img_bytes = file.read()
            
            cache_key = cache_manager.generate_key(img_bytes)
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info("命中缓存")
                result = json.loads(cached_result)
                return jsonify(APIResponse.success_response({
                    'result': result['data'],
                    'type': result['type']
                }).to_dict())
            
            img_buffer = BytesIO(img_bytes)
            
            try:
                img = Image.open(img_buffer)
            except Exception as e:
                logger.error(f"无效的图片文件: {e}")
                return jsonify(APIResponse.error_response('无效的图片文件', 400).to_dict()), 400
            
            temp_path = generate_temp_filename()
            img.save(temp_path)
            
            try:
                result = decoder.decode_full(temp_path)
                
                if result:
                    cache_manager.set(cache_key, json.dumps(result))
                    return jsonify(APIResponse.success_response({
                        'result': result['data'],
                        'type': result['type']
                    }).to_dict())
                else:
                    return jsonify(APIResponse.error_response('无法解析二维码，请确保图片清晰且包含有效的二维码', 400).to_dict()), 400
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
    except Exception as e:
        logger.error(f"解析二维码时发生错误: {e}")
        return jsonify(APIResponse.error_response(f'解析过程中发生错误: {str(e)}', 500).to_dict()), 500

@qrcode_bp.route('/decode_url', methods=['POST'])
def decode_qr_from_url():
    """
    通过URL解析图片中的二维码
    ---
    tags:
      - 二维码解析
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              example: https://example.com/qrcode.png
              description: 包含二维码的图片URL
    responses:
      200:
        description: 解析成功
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                result:
                  type: string
                  example: https://example.com
                type:
                  type: string
                  example: QRCODE
            code:
              type: integer
              example: 200
      400:
        description: 请求参数错误或无法解析二维码
      500:
        description: 服务器内部错误
    """
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify(APIResponse.error_response('缺少URL参数', 400).to_dict()), 400
        
        url = data['url']
        
        cache_key = cache_manager.generate_key(url.encode('utf-8'))
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info("命中缓存")
            result = json.loads(cached_result)
            return jsonify(APIResponse.success_response({
                'result': result['data'],
                'type': result['type']
            }).to_dict())
        
        downloaded_path = download_image(url)
        
        if not downloaded_path:
            return jsonify(APIResponse.error_response('无法下载图片', 400).to_dict()), 400
        
        try:
            result = decoder.decode_full(downloaded_path)
            
            if result:
                cache_manager.set(cache_key, json.dumps(result))
                return jsonify(APIResponse.success_response({
                    'result': result['data'],
                    'type': result['type']
                }).to_dict())
            else:
                return jsonify(APIResponse.error_response('无法从URL中的图片解析二维码', 400).to_dict()), 400
        finally:
            if downloaded_path and os.path.exists(downloaded_path):
                os.remove(downloaded_path)
                
    except Exception as e:
        logger.error(f"通过URL解析二维码时发生错误: {e}")
        return jsonify(APIResponse.error_response(f'解析过程中发生错误: {str(e)}', 500).to_dict()), 500