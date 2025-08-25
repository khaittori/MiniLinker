from flask import Flask, request, jsonify, redirect, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
import shortuuid
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# --- Konfigurasi Database MongoDB ---
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://mongo:27017/url_shortener")
mongo = PyMongo(app)

# --- Konfigurasi Folder Upload ---
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return jsonify({"message": "MiniLinker API is running!"})

@app.route('/shorten', methods=['POST'])
def shorten_url():
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

    mongo.db.urls.insert_one({
        'short_id': short_id,
        'long_url': long_url,
        'description': description,
        'thumbnail': thumbnail_filename
    })

    short_url = request.host_url + short_id
    return jsonify({
        "short_url": short_url,
        "description": description,
        "thumbnail": thumbnail_filename
    })

@app.route('/<short_id>')
def redirect_to_url(short_id):
    try:
        url_data = mongo.db.urls.find_one_or_404({'short_id': short_id})
        return redirect(url_data['long_url'])
    except Exception as e:
        print(f"Error fetching URL for {short_id}: {e}")
        return jsonify({"error": "URL not found"}), 404


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/urls')
def get_all_urls():
    urls = []
    for url in mongo.db.urls.find():
        urls.append({
            'short_id': url['short_id'],
            'short_url': request.host_url + url['short_id'],
            'long_url': url['long_url'],
            'description': url.get('description', ''),
            'thumbnail_url': request.host_url + 'uploads/' + url['thumbnail'] if url.get('thumbnail') else ''
        })
    return jsonify(urls)

@app.route('/api/urls/<short_id>', methods=['DELETE'])
def delete_url(short_id):
    result = mongo.db.urls.delete_one({'short_id': short_id})
    if result.deleted_count > 0:
        return jsonify({"message": "URL berhasil dihapus"}), 200
    else:
        return jsonify({"error": "URL tidak ditemukan"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
