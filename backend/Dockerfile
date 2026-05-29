FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_ENV=production

CMD ["gunicorn", "--workers=4", "--threads=2", "--bind=0.0.0.0:5000", "--worker-class=gevent", "app:create_app('production')"]