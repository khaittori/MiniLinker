# BEFORE (Sudah cukup baik, tapi bisa lebih cepat)
# FROM node:16-alpine as build
# WORKDIR /app
# COPY package*.json ./
# RUN npm install
# COPY . .
# RUN npm run build

# AFTER (Lebih Cepat)
# Build stage
FROM node:16-alpine as build
WORKDIR /app

# 1. Salin HANYA file package.json dan package-lock.json
COPY package*.json ./

# 2. Instal dependensi. Lapisan ini hanya akan berjalan ulang JIKA file package*.json berubah.
RUN npm install

# 3. Sekarang salin sisa kode aplikasi React.
COPY . .

# 4. Jalankan build. Ini hanya akan berjalan ulang jika kode sumber Anda berubah.
RUN npm run build

# Production stage (Ini sudah optimal)
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]