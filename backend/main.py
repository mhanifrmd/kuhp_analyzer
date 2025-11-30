import os
from typing import Optional, List, Any
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
    version="3.1.0",
    description="AI Analyzer untuk analisis perbedaan KUHP lama dan baru dengan tampilan side-by-side"
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

# Models untuk structured comparison data
class PasalDetail(BaseModel):
    pasal: Optional[str] = None
    judul: Optional[str] = None
    isi: Optional[str] = None
    sanksi: Optional[str] = None

class PasalComparison(BaseModel):
    topik: str
    kuhp_lama: Optional[PasalDetail] = None
    kuhp_baru: Optional[PasalDetail] = None
    perbedaan: Optional[List[str]] = None

class ComparisonData(BaseModel):
    ringkasan: Optional[str] = None
    pasal_terkait: Optional[List[PasalComparison]] = None
    analisis_perubahan: Optional[str] = None
    kesimpulan: Optional[str] = None

class QueryResponse(BaseModel):
    response: str  # Raw response as fallback
    is_relevant: bool
    comparison_data: Optional[ComparisonData] = None  # Structured data for side-by-side
    analyzer_info: Optional[dict] = None

class AnalyzerStatusResponse(BaseModel):
    status: str
    analyzer_info: dict
    health: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    is_relevant: bool

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
        
        # Parse comparison_data jika ada
        comparison_data = None
        if analysis_result.get("comparison_data"):
            try:
                comparison_data = ComparisonData(**analysis_result["comparison_data"])
            except Exception as e:
                print(f"[KUHP WARNING] Failed to parse comparison_data: {e}")

        return QueryResponse(
            response=analysis_result["response"],
            is_relevant=analysis_result["is_relevant"],
            comparison_data=comparison_data,
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

@app.post("/chat", response_model=ChatResponse)
async def chat_kuhp(request: ChatRequest):
    """
    Chat tentang KUHP - format conversational
    """
    try:
        if not kuhp_analyzer:
            raise HTTPException(
                status_code=503,
                detail="KUHP Analyzer belum diinisialisasi. Silakan coba lagi nanti."
            )

        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Pesan tidak boleh kosong"
            )

        message = request.message.strip()

        # Chat menggunakan Gemini
        print(f"[KUHP CHAT] Processing message: {message}")
        chat_result = kuhp_analyzer.chat(message)

        return ChatResponse(
            response=chat_result["response"],
            is_relevant=chat_result["is_relevant"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[KUHP CHAT ERROR] Chat failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Terjadi kesalahan saat memproses chat: {str(e)}"
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