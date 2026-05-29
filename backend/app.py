import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_map
from src.routes.qrcode import qrcode_bp
from src.schemas.response import APIResponse
from src.utils.logger import setup_logger
from src.utils.cache import cache_manager

logger = setup_logger()

def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    
    app.config.from_object(config_map[config_name])
    
    CORS(app)
    
    cache_manager.init_app(app)
    
    limiter = Limiter(
        get_remote_address,
        app=app,
        storage_uri=app.config.get('RATELIMIT_STORAGE_URI'),
        default_limits=[app.config.get('RATELIMIT_DEFAULT')]
    )
    
    api = Api(
        app,
        version='1.0',
        title='二维码解析器 API',
        description='用于解析二维码的 RESTful API',
        doc='/swagger/'
    )
    
    app.register_blueprint(qrcode_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return jsonify(APIResponse.success_response({
            'message': 'QR Code Analyzer API',
            'endpoints': {
                '/api/decode': 'POST - 上传图片解析二维码',
                '/api/decode_url': 'POST - 通过URL解析二维码',
                '/swagger': 'Swagger API 文档'
            }
        }).to_dict())
    
    @app.route('/health')
    def health_check():
        return jsonify(APIResponse.success_response({'status': 'healthy'}).to_dict())
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify(APIResponse.error_response('上传文件大小超过限制（最大16MB）', 413).to_dict()), 413
    
    return app

if __name__ == "__main__":
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=5000)