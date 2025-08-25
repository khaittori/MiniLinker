import os
from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
import shortuuid
from werkzeug.utils import secure_filename

# Inisialisasi aplikasi Flask dan aktifkan CORS
app = Flask(__name__)
CORS(app)

# --- Konfigurasi Folder Upload ---
# Direktori untuk menyimpan file gambar thumbnail
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Buat folder 'uploads' jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Konfigurasi Database MongoDB ---
# Kode ini akan membaca MONGO_URI dari environment variable yang disediakan oleh platform hosting (Koyeb)
mongo_uri = os.environ.get('MONGO_URI')

# Periksa apakah MONGO_URI ada. Jika tidak, aplikasi tidak bisa berjalan di produksi.
if not mongo_uri:
    # Ini akan menghentikan aplikasi jika MONGO_URI tidak ditemukan di lingkungan hosting.
    raise RuntimeError("FATAL ERROR: MONGO_URI environment variable is not set.")

app.config["MONGO_URI"] = mongo_uri

# Inisialisasi PyMongo dengan konfigurasi aplikasi
mongo = PyMongo(app)


# --- API Endpoints ---

# Endpoint untuk membuat URL pendek baru
@app.route('/shorten', methods=['POST'])
def shorten_url():
    if 'long_url' not in request.form:
        return jsonify({"error": "URL panjang diperlukan"}), 400

    long_url = request.form['long_url']
    description = request.form.get('description', '')
    short_id = shortuuid.uuid()[:8] # Buat ID pendek yang unik

    thumbnail_filename = ''
    # Cek apakah ada file thumbnail yang di-upload
    if 'thumbnail' in request.files:
        file = request.files['thumbnail']
        if file.filename != '':
            thumbnail_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
            file.save(file_path)

    # Masukkan data baru ke dalam koleksi 'urls' di database
    mongo.db.urls.insert_one({
        'short_id': short_id,
        'long_url': long_url,
        'description': description,
        'thumbnail': thumbnail_filename
    })

    # Buat URL pendek yang lengkap untuk dikirim kembali ke frontend
    short_url = request.host_url + short_id
    return jsonify({
        "short_url": short_url,
        "description": description,
        "thumbnail": thumbnail_filename
    }), 201 # Kode 201 berarti 'Created'

# Endpoint untuk mengarahkan dari URL pendek ke URL asli
@app.route('/<short_id>')
def redirect_to_url(short_id):
    # Cari data URL di database berdasarkan short_id
    url_data = mongo.db.urls.find_one_or_404({'short_id': short_id})
    return redirect(url_data['long_url'])

# Endpoint untuk menyajikan file thumbnail yang sudah di-upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Endpoint untuk mendapatkan semua URL yang sudah diperpendek
@app.route('/api/urls')
def get_all_urls():
    urls = []
    try:
        # Ambil semua dokumen dari koleksi 'urls'
        for url in mongo.db.urls.find():
            urls.append({
                'short_id': url['short_id'],
                'short_url': request.host_url + url['short_id'],
                'long_url': url['long_url'],
                'description': url.get('description', ''),
                'thumbnail_url': request.host_url + 'uploads/' + url['thumbnail'] if url.get('thumbnail') else ''
            })
        return jsonify(urls)
    except Exception as e:
        # Kirim pesan error yang jelas jika database tidak bisa diakses
        return jsonify({"error": f"Database query failed: {e}"}), 500

# Endpoint untuk menghapus URL pendek
@app.route('/api/urls/<short_id>', methods=['DELETE'])
def delete_url(short_id):
    try:
        result = mongo.db.urls.delete_one({'short_id': short_id})
        if result.deleted_count > 0:
            return jsonify({"message": "URL berhasil dihapus"}), 200
        else:
            return jsonify({"error": "URL tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": f"Database query failed: {e}"}), 500

# Blok ini hanya akan berjalan jika Anda menjalankan 'python app.py' secara langsung
# Gunicorn (yang digunakan Koyeb) tidak akan menjalankan blok ini
if __name__ == '__main__':
    # 'debug=True' hanya untuk pengembangan lokal, jangan gunakan di produksi
    app.run(host='0.0.0.0', port=5000, debug=True)
