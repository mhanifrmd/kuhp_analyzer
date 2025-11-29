import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# ADK imports
from kuhp_agent import get_agent_instance, KUHPAgentHandler

load_dotenv()

app = FastAPI(
    title="KUHP Analyzer - Agent Development Kit", 
    version="2.0.0",
    description="AI Agent untuk analisis KUHP menggunakan Google Agent Development Kit"
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
    agent_info: Optional[dict] = None

class AgentStatusResponse(BaseModel):
    status: str
    agent_info: dict
    health: str

# Global agent instance
kuhp_agent: Optional[KUHPAgentHandler] = None

@app.on_event("startup")
async def startup_event():
    """Initialize KUHP Analyzer Agent dengan ADK"""
    global kuhp_agent
    
    try:
        # Get project ID dari environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if not project_id:
            # Fallback untuk development
            project_id = "your-project-id"
            print("[WARNING] No GCP project ID found, using default")
            
        print(f"[ADK] Initializing KUHP Analyzer Agent for project: {project_id}")
        
        # Initialize agent dengan ADK
        kuhp_agent = get_agent_instance(project_id=project_id)
        
        # Load documents
        if kuhp_agent.load_documents():
            print("[ADK] KUHP Analyzer Agent initialized successfully")
        else:
            print("[ADK WARNING] Failed to load documents, agent may have limited functionality")
            
    except Exception as e:
        print(f"[ADK ERROR] Failed to initialize agent: {e}")
        # Don't raise - let the app start but handle errors in endpoints
        kuhp_agent = None

@app.get("/")
async def root():
    """Root endpoint dengan informasi agent"""
    return {
        "message": "KUHP Analyzer dengan Google Agent Development Kit",
        "version": "2.0.0",
        "agent_status": "initialized" if kuhp_agent else "not_initialized",
        "description": "AI Agent untuk menganalisis perbedaan KUHP lama dan baru"
    }

@app.post("/analyze", response_model=QueryResponse)
async def analyze_kuhp_difference(request: QueryRequest):
    """
    Analyze perbedaan KUHP menggunakan ADK Agent
    """
    try:
        if not kuhp_agent:
            raise HTTPException(
                status_code=503, 
                detail="KUHP Analyzer Agent belum diinisialisasi. Silakan coba lagi nanti."
            )
            
        # Validate input
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query tidak boleh kosong"
            )
            
        query = request.query.strip()
        
        # Analyze menggunakan ADK agent
        print(f"[ADK] Processing query: {query}")
        analysis_result = kuhp_agent.analyze_differences(query)
        
        return QueryResponse(
            response=analysis_result["response"],
            is_relevant=analysis_result["is_relevant"],
            agent_info={
                "chunks_used": analysis_result.get("context_chunks_used", 0),
                "agent_name": kuhp_agent.agent_config.agent_name,
                "model": kuhp_agent.agent_config.model_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ADK ERROR] Analysis failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Terjadi kesalahan saat memproses analisis: {str(e)}"
        )

@app.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get detailed agent status untuk monitoring"""
    try:
        if not kuhp_agent:
            return AgentStatusResponse(
                status="not_initialized",
                agent_info={},
                health="unhealthy"
            )
            
        agent_status = kuhp_agent.get_agent_status()
        
        return AgentStatusResponse(
            status="active",
            agent_info=agent_status,
            health="healthy" if agent_status["documents_loaded"] else "degraded"
        )
        
    except Exception as e:
        print(f"[ADK ERROR] Status check failed: {e}")
        return AgentStatusResponse(
            status="error",
            agent_info={"error": str(e)},
            health="unhealthy"
        )

@app.post("/agent/reset")
async def reset_agent_session():
    """Reset agent session untuk conversation baru"""
    try:
        if not kuhp_agent:
            raise HTTPException(
                status_code=503,
                detail="Agent tidak tersedia"
            )
            
        kuhp_agent.reset_session()
        
        return {
            "message": "Agent session berhasil direset",
            "status": "success"
        }
        
    except Exception as e:
        print(f"[ADK ERROR] Session reset failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mereset session: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Comprehensive health check untuk Cloud Run"""
    health_status = {
        "status": "healthy",
        "service": "kuhp-analyzer-adk",
        "version": "2.0.0",
        "components": {
            "fastapi": "healthy",
            "agent": "unknown",
            "documents": "unknown"
        }
    }
    
    try:
        if kuhp_agent:
            agent_status = kuhp_agent.get_agent_status()
            health_status["components"]["agent"] = "healthy"
            health_status["components"]["documents"] = "healthy" if agent_status["documents_loaded"] else "degraded"
            health_status["agent_info"] = {
                "name": agent_status["agent_name"],
                "model": agent_status["model_name"],
                "chunks_loaded": agent_status["chunks_loaded"]
            }
        else:
            health_status["components"]["agent"] = "unhealthy"
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["agent"] = "unhealthy"
        health_status["status"] = "degraded"
        health_status["error"] = str(e)
        
    return health_status

@app.get("/docs/agent")
async def get_agent_documentation():
    """Get dokumentasi agent untuk debugging"""
    if not kuhp_agent:
        return {"error": "Agent tidak tersedia"}
        
    return {
        "agent_config": {
            "name": kuhp_agent.agent_config.agent_name,
            "model": kuhp_agent.agent_config.model_name,
            "temperature": kuhp_agent.agent_config.temperature,
            "max_tokens": kuhp_agent.agent_config.max_output_tokens
        },
        "document_config": {
            "chunk_size": kuhp_agent.doc_config.chunk_size,
            "overlap": kuhp_agent.doc_config.overlap
        },
        "tools": kuhp_agent.agent.agent_tools,
        "system_prompt": kuhp_agent.agent.get_system_prompt()[:200] + "..."
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)