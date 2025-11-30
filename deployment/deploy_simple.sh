#!/bin/bash

# KUHP Analyzer - Simple Deployment Script (Without Secrets)
# Menggunakan Google Agent Development Kit (ADK) dengan Gemini 2.5 Flash
# Alternative deployment jika ada masalah dengan Secret Manager
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
    echo "Cara penggunaan: ./deploy_simple.sh PROJECT_ID [REGION] [GEMINI_API_KEY]"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: Harap berikan GEMINI_API_KEY sebagai argumen ketiga atau set sebagai environment variable"
    exit 1
fi

echo "Memulai deployment KUHP Analyzer ke Google Cloud Run (Simple Mode)..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "WARNING: API Key akan di-set sebagai environment variable (kurang secure)"

# Aktifkan API yang diperlukan untuk ADK
echo "Mengaktifkan Google Cloud APIs yang diperlukan untuk ADK..."
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudfunctions.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID

# Set project dan region default
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Build dan push backend image
echo "Membangun dan push backend image..."
cd backend
gcloud builds submit --tag $BACKEND_IMAGE --project=$PROJECT_ID
cd ..

# Deploy backend service (tanpa secrets, menggunakan env var langsung)
echo "Deploy backend service ke Cloud Run (Simple Mode)..."
gcloud run deploy kuhp-analyzer-backend \
    --image=$BACKEND_IMAGE \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=900 \
    --port=8080 \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT_ID,ENVIRONMENT=production,GEMINI_API_KEY=$GEMINI_API_KEY \
    --project=$PROJECT_ID

# Dapatkan backend URL
BACKEND_URL=$(gcloud run services describe kuhp-analyzer-backend --platform=managed --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
echo "Backend berhasil di-deploy di: $BACKEND_URL"

# Build dan push frontend image dengan build argument
echo "Membangun dan push frontend image dengan API URL: $BACKEND_URL"
cd frontend
gcloud builds submit --config=cloudbuild.yaml --substitutions=_NEXT_PUBLIC_API_URL=$BACKEND_URL,_IMAGE_NAME=$FRONTEND_IMAGE --project=$PROJECT_ID
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
    --port=3000 \
    --set-env-vars=NEXT_PUBLIC_API_URL=$BACKEND_URL \
    --project=$PROJECT_ID

# Dapatkan frontend URL
FRONTEND_URL=$(gcloud run services describe kuhp-analyzer-frontend --platform=managed --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

echo ""
echo "=========================================="
echo "Simple Deployment berhasil diselesaikan!"
echo "=========================================="
echo "URL Frontend: $FRONTEND_URL"
echo "URL Backend: $BACKEND_URL"
echo ""
echo "Anda sekarang dapat mengakses aplikasi KUHP Analyzer di:"
echo "$FRONTEND_URL"
echo ""
echo "CATATAN: API Key disimpan sebagai environment variable."
echo "Untuk production, gunakan Secret Manager dengan proper IAM permissions."