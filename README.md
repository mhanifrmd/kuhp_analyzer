# KUHP Analyzer

Aplikasi web AI Agent untuk menganalisis perbedaan antara KUHP lama dan KUHP baru menggunakan Google Agent Development Kit (ADK) dengan Gemini 2.5 Flash. Aplikasi ini memungkinkan pengguna untuk mencari pasal atau kata kunci tertentu dan mendapatkan analisis komprehensif tentang perubahan yang terjadi antara kedua versi KUHP.

## Fitur

- **AI Agent Architecture**: Menggunakan Google Agent Development Kit (ADK) dengan Gemini 2.5 Flash
- **Advanced Document Processing**: Chunking dan retrieval yang cerdas untuk dokumen KUHP
- **Multi-Tool Agent**: Agent dengan tools khusus untuk analisis hukum
- **Interface Modern**: Frontend Next.js yang responsif dan user-friendly
- **Scalable Backend**: FastAPI dengan ADK integration
- **Cloud Native**: Optimized untuk Google Cloud Run dengan Vertex AI
- **Scope Terbatas**: Hanya menjawab pertanyaan yang berkaitan dengan KUHP

## Arsitektur

```
frontend/          # Aplikasi frontend Next.js
├── app/           # App Router pages
├── Dockerfile     # Konfigurasi container frontend
└── package.json   # Dependencies

backend/           # Aplikasi backend FastAPI
├── main.py        # File aplikasi utama
├── Dockerfile     # Konfigurasi container backend
└── requirements.txt # Python dependencies

documents/         # Dokumen PDF
├── kuhp_old.pdf   # KUHP lama
└── kuhp_new.pdf   # KUHP baru

deployment/        # Konfigurasi deployment
├── deploy.sh      # Script deployment otomatis
├── backend.yaml   # Konfigurasi Cloud Run backend
└── frontend.yaml  # Konfigurasi Cloud Run frontend
```

## Prasyarat

### Untuk Development Lokal:
- Node.js 18 atau lebih tinggi
- Python 3.11 atau lebih tinggi
- Docker dan Docker Compose
- Google Gemini API Key

### Untuk Deployment ke Google Cloud:
- Akses ke Google Cloud Console
- Google Cloud Project dengan billing yang sudah diaktifkan
- Google Gemini API Key
- Repository GitHub (public atau private)

## Setup Development Lokal

### 1. Clone Repository
```bash
git clone <repository-url>
cd kuhp_difference
```

### 2. Setup Environment Variables
```bash
# Copy file environment contoh
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit file .env dan isi dengan API key Anda
nano .env  # Isi GEMINI_API_KEY
```

### 3. Jalankan dengan Docker Compose
```bash
# Build dan jalankan semua services
docker-compose up --build

# Atau jalankan di background
docker-compose up -d --build
```

### 4. Akses Aplikasi
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API Docs: http://localhost:8080/docs

### 5. Development Manual (Tanpa Docker)

#### Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Deployment ke Google Cloud Run

### Metode Menggunakan Google Cloud Shell (Direkomendasikan)

#### 1. Persiapan Repository
Pastikan kode Anda sudah di-push ke GitHub repository. Jika belum:

```bash
# Di terminal lokal
git add .
git commit -m "Siap untuk deployment"
git push origin main
```

#### 2. Buka Google Cloud Console
1. Buka [Google Cloud Console](https://console.cloud.google.com)
2. Pilih project Anda atau buat project baru
3. Pastikan billing sudah diaktifkan

#### 3. Buka Cloud Shell
1. Klik ikon Cloud Shell di pojok kanan atas Console
2. Tunggu hingga Cloud Shell terminal terbuka
3. Cloud Shell sudah dilengkapi dengan gcloud CLI dan semua tool yang diperlukan

#### 4. Siapkan Gemini API Key
1. Buka [Google AI Studio](https://aistudio.google.com/)
2. Generate API Key untuk Gemini
3. Copy API Key tersebut

#### 5. Jalankan Deployment
Di Cloud Shell, jalankan perintah berikut:

```bash
# Set variabel environment
export PROJECT_ID="project-id-anda"
export GEMINI_API_KEY="gemini-api-key-anda"

# Clone repository (ganti YOUR_USERNAME dengan username GitHub Anda)
git clone https://github.com/YOUR_USERNAME/kuhp-analyzer.git
cd kuhp-analyzer

# Jalankan script deployment
chmod +x deployment/deploy.sh
./deployment/deploy.sh $PROJECT_ID asia-southeast2 $GEMINI_API_KEY
```

#### 6. Hasil Deployment
Script akan menampilkan URL aplikasi setelah selesai:
```
Frontend URL: https://kuhp-analyzer-frontend-xxx.a.run.app
Backend URL: https://kuhp-analyzer-backend-xxx.a.run.app
```

### Deployment Manual (Jika diperlukan)

Jika Anda ingin melakukan deployment secara manual di Cloud Shell:

#### 1. Aktifkan API yang Diperlukan
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 2. Set Project
```bash
gcloud config set project PROJECT_ID_ANDA
gcloud config set run/region asia-southeast2
```

#### 3. Buat Secret untuk API Key
```bash
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-secret --data-file=-
```

#### 4. Deploy Backend
```bash
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/kuhp-analyzer-backend
gcloud run deploy kuhp-analyzer-backend \
    --image=gcr.io/$PROJECT_ID/kuhp-analyzer-backend \
    --platform=managed \
    --region=asia-southeast2 \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --set-secrets=GEMINI_API_KEY=gemini-secret:latest
cd ..
```

#### 5. Dapatkan Backend URL
```bash
BACKEND_URL=$(gcloud run services describe kuhp-analyzer-backend \
    --platform=managed \
    --region=asia-southeast2 \
    --format='value(status.url)')
echo "Backend URL: $BACKEND_URL"
```

#### 6. Deploy Frontend
```bash
cd frontend
gcloud builds submit --tag gcr.io/$PROJECT_ID/kuhp-analyzer-frontend
gcloud run deploy kuhp-analyzer-frontend \
    --image=gcr.io/$PROJECT_ID/kuhp-analyzer-frontend \
    --platform=managed \
    --region=asia-southeast2 \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=0.5 \
    --set-env-vars=NEXT_PUBLIC_API_URL=$BACKEND_URL
cd ..
```

## Konfigurasi

### Environment Variables

#### Backend (.env):
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8080
```

#### Frontend (.env.local):
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.run.app
```

### API Endpoints

#### Backend API:
- `GET /` - Health check
- `POST /analyze` - Analisis perbedaan KUHP
- `GET /health` - Health check detail
- `GET /docs` - Dokumentasi API interaktif

#### Format Request:
```json
{
  "query": "Pasal 351 tentang penganiayaan"
}
```

#### Format Response:
```json
{
  "response": "Analisis perbedaan...",
  "is_relevant": true
}
```

## Testing

### Test API dengan cURL di Cloud Shell:
```bash
# Health check
curl https://your-backend-url.run.app/health

# Test analisis
curl -X POST https://your-backend-url.run.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "Pasal 351"}'
```

### Test Frontend:
1. Buka aplikasi di browser
2. Masukkan query: "Pasal 351"
3. Klik "Analisis Perbedaan"
4. Verifikasi response yang relevan

## Monitoring

### Cloud Run Metrics di Console:
- CPU utilization
- Memory usage
- Request count
- Response time
- Error rate

### Logs di Cloud Shell:
```bash
# Backend logs
gcloud logs tail kuhp-analyzer-backend --region=asia-southeast2

# Frontend logs  
gcloud logs tail kuhp-analyzer-frontend --region=asia-southeast2
```

## Security

- API keys disimpan sebagai Google Cloud Secrets
- CORS dikonfigurasi untuk production
- Public access (tidak memerlukan authentication)
- Input validation di backend
- Rate limiting dari Cloud Run

## Estimasi Biaya

Estimasi biaya Google Cloud Run (per bulan):
- Backend: ~$10-30 (tergantung penggunaan)
- Frontend: ~$5-15 (tergantung traffic)
- Storage: ~$1-5
- **Total: ~$16-50/bulan**

## Troubleshooting

### Error: "Permission denied"
```bash
# Di Cloud Shell
gcloud auth list
gcloud config list
```

### Error: "Service not found"
```bash
gcloud services enable run.googleapis.com
```

### Error: "Image not found"
```bash
# Rebuild image
gcloud builds submit --tag gcr.io/$PROJECT_ID/service-name
```

### Error: "Secret not found"
```bash
# Buat ulang secret
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-secret --data-file=-
```

### Frontend tidak bisa connect ke Backend:
1. Periksa environment variable NEXT_PUBLIC_API_URL
2. Pastikan backend service sudah berjalan
3. Periksa konfigurasi CORS

## Contoh Penggunaan

### Query yang Valid:
- "Pasal 351 tentang penganiayaan"
- "perbedaan pidana pembunuhan"
- "Bab XVI tentang kejahatan terhadap keamanan negara"
- "sanksi pencurian dalam KUHP baru"

### Query yang Ditolak:
- "Bagaimana cara masak nasi?"
- "Siapa presiden Indonesia?"
- "Cuaca hari ini bagaimana?"

## Panduan Pemeliharaan

### Update Kode:
1. Lakukan perubahan di repository lokal
2. Push ke GitHub
3. Jalankan deployment ulang di Cloud Shell

### Update Dependencies:
1. Update package.json atau requirements.txt
2. Push perubahan ke GitHub
3. Deploy ulang untuk menggunakan dependencies terbaru

### Monitoring Regular:
- Periksa logs secara berkala
- Monitor penggunaan resources
- Periksa error rate dan performance

## Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## License

Project ini menggunakan MIT License.

## Support

Untuk pertanyaan atau dukungan teknis, silakan buat issue di repository ini.

---

**Dibuat menggunakan Next.js, FastAPI, dan Google Gemini 2.5 Flash - Deploy menggunakan Google Cloud Shell**