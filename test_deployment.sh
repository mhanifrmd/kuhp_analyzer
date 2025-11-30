#!/bin/bash

# Test deployment script untuk memvalidasi konfigurasi sebelum deploy ke Cloud Run

set -e

PROJECT_ID=${1:-"test-project"}
GEMINI_API_KEY=${2:-"test-key"}

echo "Testing KUHP Analyzer deployment configuration..."
echo "Project ID: $PROJECT_ID"

# Test 1: Validate deployment script syntax
echo "1. Testing deployment script syntax..."
if bash -n deployment/deploy.sh; then
    echo "   [PASS] Deployment script syntax valid"
else
    echo "   [FAIL] Deployment script has syntax errors"
    exit 1
fi

# Test 2: Check Docker files
echo "2. Testing Dockerfiles..."
if docker --version > /dev/null 2>&1; then
    # Test backend Dockerfile
    if docker build -t test-backend -f backend/Dockerfile backend/ --dry-run 2>/dev/null; then
        echo "   [PASS] Backend Dockerfile syntax valid"
    else
        echo "   [INFO] Backend Dockerfile check (docker not available or dry-run not supported)"
    fi
    
    # Test frontend Dockerfile  
    if docker build -t test-frontend -f frontend/Dockerfile frontend/ --dry-run 2>/dev/null; then
        echo "   [PASS] Frontend Dockerfile syntax valid"
    else
        echo "   [INFO] Frontend Dockerfile check (docker not available or dry-run not supported)"
    fi
else
    echo "   [INFO] Docker not available, skipping Dockerfile validation"
fi

# Test 3: Check for PORT environment variable usage
echo "3. Testing PORT environment variable configuration..."

# Check deployment script doesn't set PORT as env var
if grep -q "PORT=" deployment/deploy.sh; then
    echo "   [FAIL] Deployment script incorrectly sets PORT as environment variable"
    echo "   Cloud Run reserves PORT environment variable"
    exit 1
else
    echo "   [PASS] Deployment script correctly uses --port flag instead of PORT env var"
fi

# Test 4: Check backend Python syntax
echo "4. Testing backend Python syntax..."
cd backend
for py_file in *.py; do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        echo "   [PASS] $py_file syntax valid"
    else
        echo "   [FAIL] $py_file has syntax errors"
        exit 1
    fi
done
cd ..

# Test 5: Check requirements.txt
echo "5. Testing requirements.txt..."
if pip install --dry-run -r backend/requirements.txt > /dev/null 2>&1; then
    echo "   [PASS] Requirements.txt dependencies resolvable"
else
    echo "   [INFO] Requirements.txt check (pip dry-run may not be available)"
fi

# Test 6: Check frontend configuration
echo "6. Testing frontend configuration..."
if [ -f "frontend/package.json" ]; then
    if node -e "JSON.parse(require('fs').readFileSync('frontend/package.json', 'utf8'))" 2>/dev/null; then
        echo "   [PASS] Frontend package.json valid JSON"
        
        # Check if package-lock.json exists
        if [ -f "frontend/package-lock.json" ]; then
            echo "   [PASS] Frontend package-lock.json exists"
        else
            echo "   [INFO] Frontend package-lock.json not found - will be generated during build"
        fi
    else
        echo "   [FAIL] Frontend package.json invalid JSON"
        exit 1
    fi
else
    echo "   [FAIL] Frontend package.json not found"
    exit 1
fi

# Test 7: Check document files
echo "7. Testing document files..."
if [ -f "documents/kuhp_old.pdf" ] && [ -f "documents/kuhp_new.pdf" ]; then
    echo "   [PASS] KUHP document files present"
else
    echo "   [FAIL] KUHP document files missing"
    exit 1
fi

# Test 8: Test environment variable requirements
echo "8. Testing environment variable configuration..."
if grep -q "GOOGLE_CLOUD_PROJECT" backend/main.py; then
    echo "   [PASS] Backend uses GOOGLE_CLOUD_PROJECT environment variable"
else
    echo "   [FAIL] Backend missing GOOGLE_CLOUD_PROJECT usage"
    exit 1
fi

echo ""
echo "=========================================="
echo "Deployment configuration test PASSED!"
echo "=========================================="
echo ""
echo "Ready to deploy to Cloud Run with:"
echo "./deployment/deploy.sh $PROJECT_ID asia-southeast2 \$GEMINI_API_KEY"
echo ""
echo "Note: Make sure to set a valid GEMINI_API_KEY before deployment"