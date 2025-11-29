"""
KUHP Analyzer Agent Configuration
Menggunakan Google Agent Development Kit (ADK)
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Konfigurasi untuk KUHP Analyzer Agent"""
    agent_name: str = "kuhp-analyzer-agent"
    agent_description: str = "AI Agent untuk menganalisis perbedaan KUHP lama dan baru"
    model_name: str = "gemini-2.5-flash-exp"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40


@dataclass 
class DocumentConfig:
    """Konfigurasi untuk dokumen KUHP"""
    old_kuhp_path: str = "../documents/kuhp_old.pdf"
    new_kuhp_path: str = "../documents/kuhp_new.pdf"
    chunk_size: int = 1000
    overlap: int = 200


class KUHPAnalyzerAgent:
    """
    KUHP Analyzer Agent menggunakan Google ADK
    Agent ini memiliki kemampuan khusus untuk:
    1. Memproses dokumen KUHP
    2. Menganalisis perbedaan antar versi
    3. Memberikan response yang relevan dan akurat
    """
    
    def __init__(self, config: AgentConfig, doc_config: DocumentConfig):
        self.config = config
        self.doc_config = doc_config
        self.agent_tools = self._initialize_tools()
        self.agent_memory = self._initialize_memory()
        
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize agent tools untuk analisis KUHP"""
        return [
            {
                "name": "document_analyzer",
                "description": "Menganalisis konten dokumen KUHP",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query yang akan dianalisis"
                        },
                        "document_type": {
                            "type": "string", 
                            "enum": ["old", "new", "comparison"],
                            "description": "Jenis analisis dokumen"
                        }
                    },
                    "required": ["query", "document_type"]
                }
            },
            {
                "name": "relevance_checker", 
                "description": "Memeriksa relevansi query dengan KUHP",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query untuk diperiksa relevansinya"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "difference_analyzer",
                "description": "Menganalisis perbedaan spesifik antara KUHP lama dan baru",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "pasal": {
                            "type": "string",
                            "description": "Nomor pasal yang akan dianalisis"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Topik atau kata kunci untuk analisis"
                        }
                    },
                    "required": ["topic"]
                }
            }
        ]
        
    def _initialize_memory(self) -> Dict[str, Any]:
        """Initialize agent memory untuk menyimpan context"""
        return {
            "conversation_history": [],
            "document_cache": {},
            "analysis_results": {}
        }
        
    def get_system_prompt(self) -> str:
        """Generate system prompt untuk agent"""
        return """
        Anda adalah KUHP Analyzer Agent, sebuah AI agent khusus yang dirancang untuk menganalisis 
        perbedaan antara KUHP (Kitab Undang-Undang Hukum Pidana) lama dan baru.
        
        KEMAMPUAN ANDA:
        1. Menganalisis dokumen KUHP dengan detail dan akurat
        2. Mengidentifikasi perubahan, penambahan, dan penghapusan pasal
        3. Memberikan penjelasan yang komprehensif tentang implikasi perubahan
        4. Menolak pertanyaan di luar scope KUHP dengan sopan
        
        ATURAN:
        1. HANYA menjawab pertanyaan yang berkaitan dengan KUHP
        2. Berikan analisis yang faktual dan berdasarkan dokumen
        3. Jelaskan perubahan dengan detail dan konteks yang relevan
        4. Jika tidak yakin, katakan bahwa informasi tidak tersedia
        
        TOOLS YANG TERSEDIA:
        - document_analyzer: Untuk menganalisis konten dokumen
        - relevance_checker: Untuk memeriksa relevansi pertanyaan
        - difference_analyzer: Untuk analisis perbedaan spesifik
        
        FORMAT RESPONSE:
        RELEVANCE: [YA/TIDAK]
        ANALYSIS: [Analisis detail atau pesan penolakan]
        """
        
    def get_agent_instructions(self) -> Dict[str, Any]:
        """Get detailed instructions untuk agent behavior"""
        return {
            "role": "KUHP Legal Document Analyzer",
            "goal": "Menganalisis dan menjelaskan perbedaan antara KUHP lama dan baru",
            "backstory": "Anda adalah ahli hukum pidana yang memiliki pengetahuan mendalam tentang KUHP",
            "tools": self.agent_tools,
            "memory": True,
            "verbose": True,
            "allow_delegation": False,
            "max_iter": 5,
            "step_callback": self._step_callback
        }
        
    def _step_callback(self, step: Dict[str, Any]) -> None:
        """Callback untuk monitoring agent steps"""
        print(f"Agent Step: {step.get('action', 'Unknown')}")
        
        
# Environment-specific configurations
def get_production_config() -> tuple[AgentConfig, DocumentConfig]:
    """Get configuration untuk production environment"""
    agent_config = AgentConfig(
        agent_name="kuhp-analyzer-prod",
        temperature=0.5,  # Lebih konsisten untuk production
        max_output_tokens=3000
    )
    
    doc_config = DocumentConfig(
        chunk_size=1500,  # Lebih besar untuk production
        overlap=300
    )
    
    return agent_config, doc_config


def get_development_config() -> tuple[AgentConfig, DocumentConfig]:
    """Get configuration untuk development environment"""
    agent_config = AgentConfig(
        agent_name="kuhp-analyzer-dev", 
        temperature=0.7,
        max_output_tokens=2048
    )
    
    doc_config = DocumentConfig()
    
    return agent_config, doc_config