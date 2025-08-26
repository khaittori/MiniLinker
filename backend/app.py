import os
from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
import shortuuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# --- Konfigurasi Folder Upload ---
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Konfigurasi Database MongoDB ---
mongo_uri = os.environ.get('MONGO_URI')

# Debugging: Cetak MONGO_URI untuk verifikasi ABSOLUT
print(f"Attempting to connect with MONGO_URI: {mongo_uri}")

# Periksa apakah MONGO_URI ada. Jika tidak, hentikan aplikasi.
if not mongo_uri:
    print("FATAL ERROR: MONGO_URI environment variable is not set. Application cannot start.")
    # Menggunakan sys.exit() agar lebih jelas menghentikan aplikasi
    import sys
    sys.exit(1) # Keluar dengan kode error

app.config["MONGO_URI"] = mongo_uri

# Inisialisasi PyMongo
try:
    print("Initializing PyMongo...")
    mongo = PyMongo(app) 
    
    # Coba lakukan operasi yang pasti akan gagal jika koneksi tidak ada
    # Ini akan memicu pengecekan koneksi yang lebih dalam.
    # Mengakses db.name saja mungkin belum cukup. Mari coba ping lagi.
    # Jika mongo.client tidak ada, itu berarti PyMongo gagal diinisialisasi.
    if mongo and mongo.client:
        mongo.client.admin.command('ping') 
        print("MongoDB connection successful.")
    else:
        # Jika PyMongo diinisialisasi tapi mongo.client adalah None
        raise Exception("PyMongo client is None after initialization.")

except Exception as e:
    print(f"FATAL ERROR: Failed to connect to MongoDB during initialization: {e}")
    # Pastikan mongo adalah None jika terjadi error saat inisialisasi
    mongo = None 

# --- API Endpoints ---
# Pastikan semua endpoint yang menggunakan 'mongo' memiliki pemeriksaan tambahan
@app.route('/shorten', methods=['POST'])
def shorten_url():
    if not mongo: # Periksa jika koneksi gagal saat startup
        return jsonify({"error": "Database connection not available"}), 500
    # ... sisa kode ...

@app.route('/<short_id>')
def redirect_to_url(short_id):
    if not mongo:
        return jsonify({"error": "Database connection not available"}), 500
    try:
        url_data = mongo.db.urls.find_one_or_404({'short_id': short_id})
        return redirect(url_data['long_url'])
    except Exception as e:
        return jsonify({"error": f"Database query failed: {e}"}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Cek apakah mongo ada, jika tidak, tetap bisa melayani file statis
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/urls')
def get_all_urls():
    if not mongo:
        return jsonify({"error": "Database connection not available"}), 500
    
    urls = []
    try:
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
        return jsonify({"error": f"Database query failed: {e}"}), 500

@app.route('/api/urls/<short_id>', methods=['DELETE'])
def delete_url(short_id):
    if not mongo:
        return jsonify({"error": "Database connection not available"}), 500
        
    try:
        result = mongo.db.urls.delete_one({'short_id': short_id})
        if result.deleted_count > 0:
            return jsonify({"message": "URL berhasil dihapus"}), 200
        else:
            return jsonify({"error": "URL tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": f"Database query failed: {e}"}), 500

if __name__ == '__main__':
    # Ini hanya untuk dijalankan secara lokal. Gunicorn digunakan di Koyeb.
    pass