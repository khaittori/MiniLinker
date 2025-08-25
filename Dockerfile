# Gunakan Python 3.9 slim sebagai base image
FROM python:3.9-slim

# Set direktori kerja di dalam kontainer
WORKDIR /app

# Salin file requirements dari folder backend
COPY backend/requirements.txt .

# Instal dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh isi folder backend
COPY backend/ .

# Perintah untuk menjalankan aplikasi saat kontainer dimulai
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
