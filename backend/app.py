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
print(f"Attempting to connect with MONGO_URI: {mongo_uri}")
if not mongo_uri:
    print("FATAL ERROR: MONGO_URI is not set.")
    # Jika menjalankan secara lokal, gunakan fallback
    if os.environ.get('FLASK_ENV') == 'development':
        mongo_uri = "mongodb://mongo:27017/url_shortener"
        print(f"Using local fallback MONGO_URI: {mongo_uri}")
    else:
        import sys
        sys.exit(1) # Hentikan jika di produksi dan tidak ada URI

app.config["MONGO_URI"] = mongo_uri

# Inisialisasi PyMongo
try:
    mongo = PyMongo(app)
    # Panggil metode sederhana untuk memicu koneksi, contohnya:
    mongo.db.command('ping') # Ini butuh akses ke MongoDB 4.4+
    print("MongoDB connection successful.")
except Exception as e:
    print(f"FATAL ERROR: Could not connect to MongoDB: {e}")
    mongo = None # Pastikan mongo adalah None jika koneksi gagal

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