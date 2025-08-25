# BEFORE (Lambat)
# FROM python:3.9-slim
# WORKDIR /app
# COPY . .
# RUN pip install --no-cache-dir -r requirements.txt
# CMD ["python", "app.py"]

# AFTER (Cepat)
FROM python:3.9-slim

WORKDIR /app

# 1. Salin HANYA file dependensi
COPY requirements.txt .

# 2. Instal dependensi. Lapisan ini hanya akan berjalan ulang JIKA requirements.txt berubah.
RUN pip install --no-cache-dir -r requirements.txt

# 3. Sekarang salin sisa kode. Jika hanya kode .py yang berubah, build akan dimulai dari sini dan sangat cepat.
COPY . .

CMD ["python", "app.py"]