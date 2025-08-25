import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
    // State untuk form
    const [longUrl, setLongUrl] = useState('');
    const [description, setDescription] = useState('');
    const [thumbnail, setThumbnail] = useState(null);
    
    // State untuk daftar URL
    const [shortenedUrls, setShortenedUrls] = useState([]);
    
    // --- STATE BARU: Untuk menyimpan ID item yang baru saja di-copy ---
    const [copiedId, setCopiedId] = useState(null);

    const fetchUrls = async () => {
        try {
            const response = await axios.get('http://localhost:5000/api/urls');
            setShortenedUrls(response.data);
        } catch (error) {
            console.error('Error fetching URLs:', error);
        }
    };

    useEffect(() => {
        fetchUrls();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('long_url', longUrl);
        formData.append('description', description);
        if (thumbnail) {
            formData.append('thumbnail', thumbnail);
        }

        try {
            await axios.post('http://localhost:5000/shorten', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setLongUrl('');
            setDescription('');
            setThumbnail(null);
            e.target.reset();
            fetchUrls();
        } catch (error) {
            console.error('Error creating short URL:', error);
            alert('Gagal membuat URL pendek!');
        }
    };

    const handleDelete = async (shortId) => {
        if (window.confirm("Apakah Anda yakin ingin menghapus URL ini?")) {
            try {
                await axios.delete(`http://localhost:5000/api/urls/${shortId}`);
                fetchUrls();
            } catch (error) {
                console.error('Error deleting URL:', error);
                alert('Gagal menghapus URL.');
            }
        }
    };

    // --- FUNGSI BARU: Untuk menyalin teks ke clipboard ---
    const handleCopy = async (textToCopy, shortId) => {
        try {
            await navigator.clipboard.writeText(textToCopy);
            // Set ID item yang di-copy untuk menampilkan feedback "Copied!"
            setCopiedId(shortId);
            // Hapus feedback setelah 2 detik
            setTimeout(() => {
                setCopiedId(null);
            }, 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
            alert('Gagal menyalin link.');
        }
    };

    return (
        <div className="container">
            <h1>URL Shortener</h1>
            <form onSubmit={handleSubmit} className="form-container">
                {/* ... bagian form tidak berubah ... */}
                <input
                    type="url"
                    placeholder="Masukkan URL panjang"
                    value={longUrl}
                    onChange={(e) => setLongUrl(e.target.value)}
                    required
                />
                <textarea
                    placeholder="Deskripsi singkat"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
                <label>Upload Thumbnail (Opsional)</label>
                <input
                    type="file"
                    onChange={(e) => setThumbnail(e.target.files[0])}
                />
                <button type="submit">Perpendek URL</button>
            </form>

            <div className="urls-list">
                <h2>Hasil URL Pendek</h2>
                {shortenedUrls.map((url) => (
                    <div key={url.short_id} className="url-card">
                        {url.thumbnail_url && <img src={url.thumbnail_url} alt="thumbnail" className="thumbnail"/>}
                        <div className="url-info">
                            <p><strong>Deskripsi:</strong> {url.description || 'Tidak ada deskripsi'}</p>
                            <p><strong>URL Asli:</strong> <a href={url.long_url} target="_blank" rel="noopener noreferrer">{url.long_url}</a></p>
                            
                            {/* --- PERUBAHAN TAMPILAN URL PENDEK --- */}
                            <div className="short-url-container">
                                <p><strong>URL Pendek:</strong> <a href={url.short_url} target="_blank" rel="noopener noreferrer">{url.short_url}</a></p>
                                {copiedId === url.short_id ? (
                                    <span className="copy-feedback">Copied!</span>
                                ) : (
                                    <button onClick={() => handleCopy(url.short_url, url.short_id)} className="copy-button">
                                        Copy
                                    </button>
                                )}
                            </div>
                        </div>
                        <button 
                            onClick={() => handleDelete(url.short_id)} 
                            className="delete-button"
                        >
                            Hapus
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default App;