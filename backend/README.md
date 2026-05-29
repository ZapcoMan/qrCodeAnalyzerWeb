# QR Code Analyzer Backend

二维码解析器后端服务

## 技术栈

- Python 3.11+
- Flask 3.0+
- pyzxing (二维码解码)
- Redis (缓存/限流)
- gunicorn + gevent (生产环境)

## 快速开始

### 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py
```

### 生产环境

#### 使用 Docker (推荐)

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 使用 Gunicorn

```bash
# 安装生产依赖
pip install -r requirements-prod.txt

# 启动服务
gunicorn --workers=4 --threads=2 --bind=0.0.0.0:5000 --worker-class=gevent "app:create_app('production')"
```

## API 接口

### 上传图片解析二维码

**POST** `/api/decode`

```bash
curl -X POST -F "file=@qrcode.png" http://localhost:5000/api/decode
```

### 通过URL解析二维码

**POST** `/api/decode_url`

```bash
curl -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com/qrcode.png"}' http://localhost:5000/api/decode_url
```

### API 文档

访问 `http://localhost:5000/swagger` 查看 Swagger API 文档

### 健康检查

**GET** `/health`

```bash
curl http://localhost:5000/health
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| FLASK_ENV | development | 运行环境 (development/production) |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接地址 |
| SECRET_KEY | dev-secret-key | 安全密钥 |
| MAX_CONTENT_LENGTH | 16777216 | 最大上传文件大小 (字节) |

## 项目结构

```
backend/
├── app.py                 # 应用入口
├── config.py              # 配置管理
├── requirements.txt       # 开发依赖
├── requirements-prod.txt  # 生产依赖
├── Dockerfile            # Docker 配置
├── docker-compose.yml    # Docker Compose 配置
├── start.sh              # 启动脚本
└── src/
    ├── routes/           # 路由模块
    │   └── qrcode.py     # 二维码路由
    ├── services/         # 业务逻辑
    │   └── decoder.py    # 解码器服务
    ├── utils/            # 工具函数
    │   ├── logger.py     # 日志配置
    │   ├── image.py      # 图片处理
    │   ├── url.py        # URL处理
    │   ├── security.py   # 安全工具
    │   └── cache.py      # 缓存管理
    └── schemas/          # 数据模型
        └── response.py   # 响应格式
```