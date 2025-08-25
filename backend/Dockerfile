FROM python:3.9-slim

WORKDIR /app

# Salin file requirements dari root
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file di root (sekarang sudah backend) ke kontainer
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
