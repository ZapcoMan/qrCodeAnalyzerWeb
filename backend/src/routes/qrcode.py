import os
from flask import Blueprint, request, jsonify
from io import BytesIO
from PIL import Image

from src.services.decoder import QRCodeDecoder
from src.utils.url import download_image
from src.schemas.response import APIResponse
from src.utils.logger import setup_logger

logger = setup_logger()
qrcode_bp = Blueprint('qrcode', __name__)
decoder = QRCodeDecoder()

@qrcode_bp.route('/decode', methods=['POST'])
def decode_qr_endpoint():
    try:
        if 'file' not in request.files:
            return jsonify(APIResponse.error_response('没有上传文件', 400).to_dict()), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(APIResponse.error_response('没有选择文件', 400).to_dict()), 400
        
        if file:
            img_bytes = file.read()
            img_buffer = BytesIO(img_bytes)
            
            img = Image.open(img_buffer)
            
            temp_path = "temp_uploaded_qr.png"
            img.save(temp_path)
            
            try:
                result = decoder.decode_full(temp_path)
                
                if result:
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
    try:
        data = request.json
        if not data or 'url' not in data:
            return jsonify(APIResponse.error_response('缺少URL参数', 400).to_dict()), 400
        
        url = data['url']
        downloaded_path = download_image(url)
        
        if not downloaded_path:
            return jsonify(APIResponse.error_response('无法下载图片', 400).to_dict()), 400
        
        try:
            result = decoder.decode_full(downloaded_path)
            
            if result:
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