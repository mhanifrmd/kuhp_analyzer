"""
KUHP Analyzer Agent Implementation
Menggunakan Google Agent Development Kit dengan Vertex AI dan LangChain
"""

import os
import json
from typing import Dict, Any, Optional, List
import PyPDF2
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from google.cloud import aiplatform
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        print("[ADK WARNING] LangChain imports failed, using basic text processing")
        LANGCHAIN_AVAILABLE = False
        
        # Fallback Document class
        class Document:
            def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
                self.page_content = page_content
                self.metadata = metadata or {}
                
        # Fallback text splitter
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
                
            def split_text(self, text: str) -> List[str]:
                chunks = []
                start = 0
                while start < len(text):
                    end = start + self.chunk_size
                    chunk = text[start:end]
                    chunks.append(chunk)
                    start = end - self.chunk_overlap
                return chunks
from agent_config import KUHPAnalyzerAgent, AgentConfig, DocumentConfig


class KUHPAgentHandler:
    """
    Handler untuk KUHP Analyzer Agent menggunakan Google ADK
    """
    
    def __init__(self, project_id: str, location: str = "asia-southeast1"):
        self.project_id = project_id
        self.location = location
        self.agent_config, self.doc_config = self._get_config()
        self.agent = KUHPAnalyzerAgent(self.agent_config, self.doc_config)
        self.model = None
        self.chat_session = None
        self.documents_loaded = False
        self.kuhp_old_chunks = []
        self.kuhp_new_chunks = []
        
        # Initialize Vertex AI
        self._initialize_vertex_ai()
        
    def _get_config(self) -> tuple[AgentConfig, DocumentConfig]:
        """Get configuration based on environment"""
        env = os.getenv("ENVIRONMENT", "production")
        if env == "development":
            from agent_config import get_development_config
            return get_development_config()
        else:
            from agent_config import get_production_config
            return get_production_config()
            
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI dan Gemini model"""
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(
                model_name=self.agent_config.model_name,
                system_instruction=self.agent.get_system_prompt()
            )
            self.chat_session = self.model.start_chat()
            print(f"[ADK] Vertex AI initialized with {self.agent_config.model_name}")
        except Exception as e:
            print(f"[ADK ERROR] Failed to initialize Vertex AI: {e}")
            raise
            
    def load_documents(self) -> bool:
        """Load dan process dokumen KUHP"""
        try:
            if self.documents_loaded:
                return True
                
            print("[ADK] Loading KUHP documents...")
            
            # Load KUHP lama
            old_text = self._extract_text_from_pdf(self.doc_config.old_kuhp_path)
            # Load KUHP baru  
            new_text = self._extract_text_from_pdf(self.doc_config.new_kuhp_path)
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.doc_config.chunk_size,
                chunk_overlap=self.doc_config.overlap
            )
            
            old_docs = text_splitter.split_text(old_text)
            new_docs = text_splitter.split_text(new_text)
            
            self.kuhp_old_chunks = [
                Document(page_content=chunk, metadata={"type": "kuhp_old", "chunk_id": i})
                for i, chunk in enumerate(old_docs)
            ]
            
            self.kuhp_new_chunks = [
                Document(page_content=chunk, metadata={"type": "kuhp_new", "chunk_id": i})
                for i, chunk in enumerate(new_docs)
            ]
            
            self.documents_loaded = True
            print(f"[ADK] Documents loaded: {len(self.kuhp_old_chunks)} old chunks, {len(self.kuhp_new_chunks)} new chunks")
            return True
            
        except Exception as e:
            print(f"[ADK ERROR] Failed to load documents: {e}")
            return False
            
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text dari PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF {file_path}: {str(e)}")
            
    def check_relevance(self, query: str) -> bool:
        """Check apakah query relevan dengan KUHP menggunakan agent"""
        try:
            relevance_prompt = f"""
            Sebagai AHLI HUKUM, tentukan apakah Kata Kunci berikut berikut relevan dengan KUHP:
            
            Kata Kunci: "{query}"
            
            Kriteria relevan:
            - Berkaitan dengan pasal-pasal KUHP
            - Menyangkut hukum pidana Indonesia
            - Membahas kejahatan, pelanggaran, atau sanksi
            - Berkaitan dengan perubahan/perbedaan KUHP
            
            Jawab hanya: YA atau TIDAK
            """
            
            response = self.chat_session.send_message(relevance_prompt)
            return "YA" in response.text.upper()
            
        except Exception as e:
            print(f"[ADK ERROR] Relevance check failed: {e}")
            return False
            
    def find_relevant_chunks(self, query: str, doc_type: str = "both") -> List[Document]:
        """Find relevant document chunks berdasarkan query"""
        relevant_chunks = []
        
        # Simple keyword-based search (bisa ditingkatkan dengan vector search)
        query_lower = query.lower()
        
        chunks_to_search = []
        if doc_type in ["old", "both"]:
            chunks_to_search.extend(self.kuhp_old_chunks)
        if doc_type in ["new", "both"]:
            chunks_to_search.extend(self.kuhp_new_chunks)
            
        for chunk in chunks_to_search:
            if any(keyword in chunk.page_content.lower() for keyword in query_lower.split()):
                relevant_chunks.append(chunk)
                
        # Limit to top 5 most relevant chunks
        return relevant_chunks[:5]
        
    def analyze_differences(self, query: str) -> Dict[str, Any]:
        """Analyze perbedaan KUHP menggunakan agent dengan tools"""
        try:
            if not self.documents_loaded:
                if not self.load_documents():
                    return {
                        "response": "Maaf, terjadi kesalahan saat memuat dokumen KUHP.",
                        "is_relevant": False
                    }
                    
            # Step 1: Check relevance
            is_relevant = self.check_relevance(query)
            
            if not is_relevant:
                return {
                    "response": "Maaf, saya hanya dapat membantu menganalisis perbedaan dalam dokumen KUHP. Silakan ajukan pertanyaan yang berkaitan dengan pasal atau topik dalam KUHP.",
                    "is_relevant": False
                }
                
            # Step 2: Find relevant chunks
            relevant_chunks = self.find_relevant_chunks(query)
            
            if not relevant_chunks:
                return {
                    "response": "Maaf, tidak ditemukan informasi yang relevan dalam dokumen KUHP untuk pertanyaan Anda. Coba gunakan kata kunci yang lebih spesifik.",
                    "is_relevant": True
                }
                
            # Step 3: Generate analysis using agent
            context_text = "\n\n".join([
                f"[{chunk.metadata['type'].upper()}] {chunk.page_content[:500]}..."
                for chunk in relevant_chunks
            ])
            
            analysis_prompt = f"""
            Sebagai AHLI HUKUM, buatlah sebuah perbandingan antara KUHP lama dan baru berdasarkan KONTEKS DOKUMEN dan KATA KUNCI berikut:
            
            KONTEKS DOKUMEN:
            {context_text}
            
            KATA KUNCI: "{query}"
            
            TUGAS ANDA:
            1. Identifikasi perbedaan utama antara KUHP lama dan KUHP baru terkait dengan KATA KUNCI tersebut
            2. Jelaskan perubahan pasal-pasal yang relevan
            3. Berikan analisis dampak dari perubahan tersebut
            4. Gunakan format yang jelas dan mudah dipahami
            
            Berikan analisis yang komprehensif dan faktual berdasarkan dokumen yang tersedia.

            dan tolong PASTIKAN respon yang anda berikan terbagi dalam 2 segmen yaitu KUHP LAMA dan KUHP BARU serta pastikan penulisan nya rapih tanpa tabahan character "*"
            """
            
            response = self.chat_session.send_message(analysis_prompt)
            
            return {
                "response": response.text,
                "is_relevant": True,
                "context_chunks_used": len(relevant_chunks)
            }
            
        except Exception as e:
            print(f"[ADK ERROR] Analysis failed: {e}")
            return {
                "response": "Maaf, terjadi kesalahan saat menganalisis pertanyaan Anda. Silakan coba lagi.",
                "is_relevant": False
            }
            
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status agent untuk monitoring"""
        return {
            "agent_name": self.agent_config.agent_name,
            "model_name": self.agent_config.model_name,
            "documents_loaded": self.documents_loaded,
            "chunks_loaded": {
                "old": len(self.kuhp_old_chunks),
                "new": len(self.kuhp_new_chunks)
            },
            "project_id": self.project_id,
            "location": self.location
        }
        
    def reset_session(self):
        """Reset chat session untuk conversation baru"""
        try:
            self.chat_session = self.model.start_chat()
            print("[ADK] Chat session reset")
        except Exception as e:
            print(f"[ADK ERROR] Failed to reset session: {e}")


# Global agent instance untuk reuse
_agent_instance: Optional[KUHPAgentHandler] = None


def get_agent_instance(project_id: str = None) -> KUHPAgentHandler:
    """Get or create global agent instance"""
    global _agent_instance
    
    if _agent_instance is None:
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
        _agent_instance = KUHPAgentHandler(project_id=project_id)
        
    return _agent_instance