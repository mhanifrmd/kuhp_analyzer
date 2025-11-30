import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# KUHP Analyzer imports
from kuhp_agent import get_analyzer_instance, KUHPAnalyzer

load_dotenv()

app = FastAPI(
    title="KUHP Analyzer - Gemini File API", 
    version="3.0.0",
    description="AI Analyzer untuk analisis KUHP menggunakan Gemini File API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    is_relevant: bool
    analyzer_info: Optional[dict] = None

class AnalyzerStatusResponse(BaseModel):
    status: str
    analyzer_info: dict
    health: str

# Global analyzer instance
kuhp_analyzer: Optional[KUHPAnalyzer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize KUHP Analyzer dengan Gemini File API"""
    global kuhp_analyzer
    
    try:
        print("[KUHP] Initializing KUHP Analyzer with Gemini File API")
        
        # Initialize analyzer
        kuhp_analyzer = get_analyzer_instance()
        
        # Load documents
        if kuhp_analyzer.load_documents():
            print("[KUHP] KUHP Analyzer initialized successfully")
        else:
            print("[KUHP WARNING] Failed to load documents, analyzer may have limited functionality")
            
    except Exception as e:
        print(f"[KUHP ERROR] Failed to initialize analyzer: {e}")
        # Don't raise - let the app start but handle errors in endpoints
        kuhp_analyzer = None

@app.get("/")
async def root():
    """Root endpoint dengan informasi analyzer"""
    return {
        "message": "KUHP Analyzer dengan Gemini File API",
        "version": "3.0.0",
        "analyzer_status": "initialized" if kuhp_analyzer else "not_initialized",
        "description": "AI Analyzer untuk menganalisis perbedaan KUHP lama dan baru"
    }

@app.post("/analyze", response_model=QueryResponse)
async def analyze_kuhp_difference(request: QueryRequest):
    """
    Analyze perbedaan KUHP menggunakan Gemini File API
    """
    try:
        if not kuhp_analyzer:
            raise HTTPException(
                status_code=503, 
                detail="KUHP Analyzer belum diinisialisasi. Silakan coba lagi nanti."
            )
            
        # Validate input
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query tidak boleh kosong"
            )
            
        query = request.query.strip()
        
        # Analyze menggunakan Gemini File API
        print(f"[KUHP] Processing query: {query}")
        analysis_result = kuhp_analyzer.analyze_differences(query)
        
        return QueryResponse(
            response=analysis_result["response"],
            is_relevant=analysis_result["is_relevant"],
            analyzer_info={
                "files_used": analysis_result.get("files_used", 0),
                "model": kuhp_analyzer.config.model_name,
                "method": "gemini_file_api"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[KUHP ERROR] Analysis failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Terjadi kesalahan saat memproses analisis: {str(e)}"
        )

@app.get("/analyzer/status", response_model=AnalyzerStatusResponse)
async def get_analyzer_status():
    """Get detailed analyzer status untuk monitoring"""
    try:
        if not kuhp_analyzer:
            return AnalyzerStatusResponse(
                status="not_initialized",
                analyzer_info={},
                health="unhealthy"
            )
            
        analyzer_status = kuhp_analyzer.get_status()
        
        return AnalyzerStatusResponse(
            status="active",
            analyzer_info=analyzer_status,
            health="healthy" if analyzer_status["files_uploaded"] else "degraded"
        )
        
    except Exception as e:
        print(f"[KUHP ERROR] Status check failed: {e}")
        return AnalyzerStatusResponse(
            status="error",
            analyzer_info={"error": str(e)},
            health="unhealthy"
        )

@app.post("/analyzer/reload")
async def reload_analyzer_files():
    """Reload PDF files untuk analyzer"""
    try:
        if not kuhp_analyzer:
            raise HTTPException(
                status_code=503,
                detail="Analyzer tidak tersedia"
            )
            
        if kuhp_analyzer.load_documents():
            return {
                "message": "PDF files berhasil direload",
                "status": "success"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Gagal memuat ulang PDF files"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[KUHP ERROR] File reload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal reload files: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Comprehensive health check untuk Cloud Run"""
    health_status = {
        "status": "healthy",
        "service": "kuhp-analyzer-gemini",
        "version": "3.0.0",
        "components": {
            "fastapi": "healthy",
            "analyzer": "unknown",
            "files": "unknown"
        }
    }
    
    try:
        if kuhp_analyzer:
            analyzer_status = kuhp_analyzer.get_status()
            health_status["components"]["analyzer"] = "healthy"
            health_status["components"]["files"] = "healthy" if analyzer_status["files_uploaded"] else "degraded"
            health_status["analyzer_info"] = {
                "model": analyzer_status["model_name"],
                "old_kuhp": analyzer_status["old_kuhp_file"],
                "new_kuhp": analyzer_status["new_kuhp_file"]
            }
        else:
            health_status["components"]["analyzer"] = "unhealthy"
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["analyzer"] = "unhealthy"
        health_status["status"] = "degraded"
        health_status["error"] = str(e)
        
    return health_status

@app.get("/docs/analyzer")
async def get_analyzer_documentation():
    """Get dokumentasi analyzer untuk debugging"""
    if not kuhp_analyzer:
        return {"error": "Analyzer tidak tersedia"}
        
    return {
        "analyzer_config": {
            "model": kuhp_analyzer.config.model_name,
            "temperature": kuhp_analyzer.config.temperature,
            "max_tokens": kuhp_analyzer.config.max_output_tokens,
            "old_kuhp_path": kuhp_analyzer.config.old_kuhp_path,
            "new_kuhp_path": kuhp_analyzer.config.new_kuhp_path
        },
        "file_status": {
            "old_kuhp_uploaded": bool(kuhp_analyzer.old_kuhp_file),
            "new_kuhp_uploaded": bool(kuhp_analyzer.new_kuhp_file),
            "is_initialized": kuhp_analyzer.is_initialized
        },
        "method": "gemini_file_api",
        "description": "Menggunakan Gemini File API untuk upload dan analisis PDF langsung"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)