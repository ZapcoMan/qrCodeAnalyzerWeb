#!/bin/bash

# 检查是否设置了环境变量
if [ -z "$FLASK_ENV" ]; then
    export FLASK_ENV=production
fi

if [ -z "$REDIS_URL" ]; then
    export REDIS_URL=redis://localhost:6379/0
fi

if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

# 启动应用
gunicorn --workers=4 --threads=2 --bind=0.0.0.0:5000 --worker-class=gevent "app:create_app('$FLASK_ENV')"