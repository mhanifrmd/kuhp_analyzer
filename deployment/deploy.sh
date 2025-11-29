#!/bin/bash

# KUHP Analyzer - Script Deployment untuk Google Cloud Run
# Menggunakan Gemini 2.5 Flash untuk analisis AI
# Jalankan script ini di Google Cloud Shell

set -e

# Konfigurasi
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"asia-southeast2"}
BACKEND_IMAGE="gcr.io/${PROJECT_ID}/kuhp-analyzer-backend"
FRONTEND_IMAGE="gcr.io/${PROJECT_ID}/kuhp-analyzer-frontend"
GEMINI_API_KEY=${3:-""}

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "Error: Harap berikan PROJECT_ID sebagai argumen pertama"
    echo "Cara penggunaan: ./deploy.sh PROJECT_ID [REGION] [GEMINI_API_KEY]"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: Harap berikan GEMINI_API_KEY sebagai argumen ketiga atau set sebagai environment variable"
    exit 1
fi

echo "Memulai deployment KUHP Analyzer ke Google Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Aktifkan API yang diperlukan
echo "Mengaktifkan Google Cloud APIs yang diperlukan..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID

# Set project dan region default
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Buat secret untuk Gemini API key
echo "Membuat secret untuk Gemini API key..."
echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-secret --data-file=- --project=$PROJECT_ID || true

# Clone repository jika belum ada
if [ ! -d "kuhp-analyzer" ]; then
    echo "Clone repository dari GitHub..."
    git clone https://github.com/YOUR_USERNAME/kuhp-analyzer.git
    cd kuhp-analyzer
else
    echo "Repository sudah ada, masuk ke direktori..."
    cd kuhp-analyzer
    git pull origin main
fi

# Build dan push backend image
echo "Membangun dan push backend image..."
cd backend
gcloud builds submit --tag $BACKEND_IMAGE --project=$PROJECT_ID
cd ..

# Deploy backend service
echo "Deploy backend service ke Cloud Run..."
gcloud run deploy kuhp-analyzer-backend \
    --image=$BACKEND_IMAGE \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --timeout=300 \
    --set-env-vars=PORT=8080 \
    --set-secrets=GEMINI_API_KEY=gemini-secret:latest \
    --project=$PROJECT_ID

# Dapatkan backend URL
BACKEND_URL=$(gcloud run services describe kuhp-analyzer-backend --platform=managed --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
echo "Backend berhasil di-deploy di: $BACKEND_URL"

# Build dan push frontend image
echo "Membangun dan push frontend image..."
cd frontend
gcloud builds submit --tag $FRONTEND_IMAGE --project=$PROJECT_ID
cd ..

# Deploy frontend service
echo "Deploy frontend service ke Cloud Run..."
gcloud run deploy kuhp-analyzer-frontend \
    --image=$FRONTEND_IMAGE \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=0.5 \
    --timeout=300 \
    --set-env-vars=PORT=3000,NEXT_PUBLIC_API_URL=$BACKEND_URL \
    --project=$PROJECT_ID

# Dapatkan frontend URL
FRONTEND_URL=$(gcloud run services describe kuhp-analyzer-frontend --platform=managed --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

echo ""
echo "=========================================="
echo "Deployment berhasil diselesaikan!"
echo "=========================================="
echo "URL Frontend: $FRONTEND_URL"
echo "URL Backend: $BACKEND_URL"
echo ""
echo "Anda sekarang dapat mengakses aplikasi KUHP Analyzer di:"
echo "$FRONTEND_URL"
echo ""
echo "Catatan: Pastikan untuk mengganti YOUR_USERNAME dengan username GitHub Anda yang sebenarnya"