import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource

from config import config_map
from src.routes.qrcode import qrcode_bp
from src.schemas.response import APIResponse
from src.utils.logger import setup_logger

logger = setup_logger()

def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    
    app.config.from_object(config_map[config_name])
    
    CORS(app)
    
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
    
    return app

if __name__ == "__main__":
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(host='0.0.0.0', port=5000)