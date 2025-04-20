FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --cache-dir=/tmp/pip_cache -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
