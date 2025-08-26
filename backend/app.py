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

# Debugging: Cetak MONGO_URI untuk verifikasi
print(f"Attempting to connect with MONGO_URI: {mongo_uri}")

# Periksa apakah MONGO_URI ada. Jika tidak, aplikasi tidak bisa berjalan.
if not mongo_uri:
    raise RuntimeError("FATAL ERROR: MONGO_URI environment variable is not set.")

app.config["MONGO_URI"] = mongo_uri

# --- Inisialisasi PyMongo ---
# Inisialisasi mongo dengan None terlebih dahulu
mongo = None
try:
    print("Initializing PyMongo...")
    mongo = PyMongo(app) # Coba inisialisasi PyMongo
    
    # Coba lakukan operasi sederhana untuk mengetes koneksi.
    # Jika PyMongo berhasil diinisialisasi, lakukan ping.
    # Pastikan mongo.db tidak None sebelum mencoba akses.
    if mongo and mongo.db: # Periksa apakah mongo objectnya valid
        mongo.db.command('ping') # Gunakan command 'ping' untuk tes koneksi
        print("MongoDB connection successful.")
    else:
        # Jika mongo.db adalah None, berarti inisialisasi PyMongo mungkin gagal tanpa error eksplisit
        raise Exception("PyMongo initialization resulted in None object.")

except Exception as e:
    print(f"FATAL ERROR: Failed to connect to MongoDB: {e}")
    mongo = None # Pastikan mongo tetap None jika terjadi error

# --- API Endpoints ---

# Pastikan semua endpoint yang menggunakan 'mongo' memiliki pemeriksaan tambahan
@app.route('/shorten', methods=['POST'])
def shorten_url():
    if not mongo: # Periksa jika koneksi gagal saat startup
        return jsonify({"error": "Database connection not available"}), 500
        
    if 'long_url' not in request.form:
        return jsonify({"error": "URL panjang diperlukan"}), 400

    long_url = request.form['long_url']
    description = request.form.get('description', '')
    short_id = shortuuid.uuid()[:8]

    thumbnail_filename = ''
    if 'thumbnail' in request.files:
        file = request.files['thumbnail']
        if file.filename != '':
            thumbnail_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
            file.save(file_path)

    try:
        mongo.db.urls.insert_one({
            'short_id': short_id,
            'long_url': long_url,
            'description': description,
            'thumbnail': thumbnail_filename
        })
        short_url = request.host_url + short_id
        return jsonify({"short_url": short_url, "description": description, "thumbnail": thumbnail_filename}), 201
    except Exception as e:
        return jsonify({"error": f"Database insertion failed: {e}"}), 500

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
    # Handle case where uploads folder might not be persisted or accessible if needed
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
    # Ini hanya untuk dijalankan secara lokal, Koyeb menggunakan gunicorn
    # Pastikan Anda tidak menjalankan app.run() jika sudah menggunakan Gunicorn
    # Jika Anda menjalankan dengan Gunicorn, bagian ini tidak akan dieksekusi
    pass # Biarkan kosong jika Anda sudah menggunakan Gunicorn