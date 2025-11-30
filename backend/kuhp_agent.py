"""
KUHP Analyzer Implementation
Menggunakan Gemini File API untuk analisis PDF langsung
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Google AI SDK for File API
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    print("[ERROR] Google AI SDK not available")
    GENAI_AVAILABLE = False


@dataclass
class KUHPConfig:
    """Konfigurasi untuk KUHP analyzer"""
    model_name: str = "gemini-2.0-flash"  # Stable model for file API
    temperature: float = 0.1
    old_kuhp_path: str = "documents/kuhp_old.pdf"
    new_kuhp_path: str = "documents/kuhp_new.pdf"


class KUHPAnalyzer:
    """KUHP Analyzer menggunakan Gemini File API langsung"""
    
    def __init__(self):
        self.config = KUHPConfig()
        self.model = None
        self.old_kuhp_file = None
        self.new_kuhp_file = None
        self.is_initialized = False
        
        # Initialize Gemini
        self._initialize_gemini()
        
    def _initialize_gemini(self):
        """Initialize Gemini AI dengan API key"""
        try:
            if not GENAI_AVAILABLE:
                raise Exception("Google AI SDK not available")
                
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY not found in environment variables")
                
            genai.configure(api_key=api_key)
            
            self.model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config={
                    "temperature": self.config.temperature
                    # No max_output_tokens limit - use model default
                }
            )
            
            print(f"[KUHP] Gemini initialized successfully using {self.config.model_name}")
            
        except Exception as e:
            print(f"[KUHP ERROR] Failed to initialize Gemini: {e}")
            raise
            
    def load_documents(self) -> bool:
        """Load PDF files ke Gemini menggunakan File API"""
        try:
            print("[KUHP] Uploading PDF documents to Gemini...")
            
            # Upload KUHP lama
            old_path = Path(self.config.old_kuhp_path)
            if old_path.exists():
                print(f"[KUHP] Uploading {old_path.name}...")
                self.old_kuhp_file = genai.upload_file(
                    path=str(old_path),
                    display_name="KUHP Lama"
                )
                print(f"[KUHP] KUHP Lama uploaded: {self.old_kuhp_file.display_name}")
            else:
                print(f"[KUHP WARNING] File not found: {old_path}")
                return False
            
            # Upload KUHP baru
            new_path = Path(self.config.new_kuhp_path)
            if new_path.exists():
                print(f"[KUHP] Uploading {new_path.name}...")
                self.new_kuhp_file = genai.upload_file(
                    path=str(new_path),
                    display_name="KUHP Baru"
                )
                print(f"[KUHP] KUHP Baru uploaded: {self.new_kuhp_file.display_name}")
            else:
                print(f"[KUHP WARNING] File not found: {new_path}")
                return False
                
            # Wait for files to be processed
            self._wait_for_files_active()
            
            self.is_initialized = True
            print("[KUHP] Documents loaded and ready for analysis")
            
            return True
            
        except Exception as e:
            print(f"[KUHP ERROR] Failed to load documents: {e}")
            return False
            
    def _wait_for_files_active(self):
        """Wait for uploaded files to become active"""
        print("[KUHP] Waiting for files to be processed...")
        
        max_wait_time = 60  # seconds
        wait_interval = 2
        elapsed = 0
        
        while elapsed < max_wait_time:
            old_file_info = genai.get_file(self.old_kuhp_file.name) if self.old_kuhp_file else None
            new_file_info = genai.get_file(self.new_kuhp_file.name) if self.new_kuhp_file else None
            
            if (old_file_info and old_file_info.state.name == "ACTIVE" and
                new_file_info and new_file_info.state.name == "ACTIVE"):
                print("[KUHP] Both files are now active and ready for use")
                return
                
            print(f"[KUHP] Files still processing... ({elapsed}s elapsed)")
            time.sleep(wait_interval)
            elapsed += wait_interval
            
        print("[KUHP WARNING] Files may not be fully processed, but continuing anyway")

    def analyze_differences(self, query: str) -> Dict[str, Any]:
        """Analyze perbedaan KUHP berdasarkan query langsung dari PDF files"""
        try:
            if not self.is_initialized:
                raise Exception("Gemini belum diinisialisasi")
                
            if not self.old_kuhp_file or not self.new_kuhp_file:
                raise Exception("PDF files belum di-upload")
            
            print(f"[KUHP] Starting analysis for query: {query[:100]}...")
            
            # Check relevance first
            is_relevant = self._check_query_relevance(query)
            
            if not is_relevant:
                return {
                    "response": self._get_irrelevant_response(query),
                    "is_relevant": False,
                    "files_used": 0
                }
            
            # Generate analysis dengan PDF files
            analysis_prompt = self._build_analysis_prompt(query)
            
            # Generate response dengan file attachments
            response = self._generate_response_with_files(analysis_prompt)
            
            result = {
                "response": response,
                "is_relevant": True,
                "files_used": 2  # both PDF files
            }
            
            print("[KUHP] Analysis completed using both KUHP PDF files")
            return result
            
        except Exception as e:
            print(f"[KUHP ERROR] Analysis failed: {e}")
            raise

    def _check_query_relevance(self, query: str) -> bool:
        """Check apakah query relevan dengan KUHP"""
        kuhp_keywords = [
            'kuhp', 'hukum pidana', 'pasal', 'pidana', 'kejahatan', 'pelanggaran',
            'pencurian', 'pembunuhan', 'penganiayaan', 'penipuan', 'korupsi',
            'perkosaan', 'narkoba', 'terorisme', 'cyber', 'cyber crime',
            'sanksi', 'hukuman', 'denda', 'penjara', 'kurungan', 'tahanan',
            'tindak pidana', 'delik', 'unsur', 'ancaman', 'maksimal', 'minimal'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in kuhp_keywords)
    
    def _get_irrelevant_response(self, query: str) -> str:
        """Response untuk query yang tidak relevan"""
        return """Maaf, pertanyaan Anda sepertinya tidak terkait dengan KUHP (Kitab Undang-Undang Hukum Pidana) Indonesia.

Saya adalah AI assistant yang khusus dirancang untuk menganalisis perbedaan antara KUHP lama dan KUHP baru yang berlaku di Indonesia.

Silakan tanyakan hal-hal yang berkaitan dengan:
• Pasal-pasal dalam KUHP
• Jenis-jenis tindak pidana (kejahatan dan pelanggaran)
• Sanksi dan hukuman dalam KUHP
• Perbedaan ketentuan antara KUHP lama dan baru
• Perubahan sistem pemidanaan

Contoh pertanyaan yang dapat saya bantu:
- "Apa perbedaan Pasal 351 tentang penganiayaan di KUHP lama dan baru?"
- "Bagaimana perubahan ketentuan tentang pencurian?"
- "Apa sanksi untuk tindak pidana korupsi di KUHP baru?"
"""

    def _build_analysis_prompt(self, query: str) -> str:
        """Build analysis prompt untuk Gemini dengan PDF files"""
        
        prompt = f"""Anda adalah AI assistant yang ahli dalam menganalisis KUHP (Kitab Undang-Undang Hukum Pidana) Indonesia.

Tugas Anda: Analisis perbedaan antara KUHP lama dan KUHP baru berdasarkan query pengguna dengan menggunakan kedua file PDF yang telah diberikan.

Query pengguna: {query}

=== INSTRUKSI ANALISIS ===
1. Baca dan analisis kedua file PDF KUHP (lama dan baru) yang telah diberikan
2. Bandingkan ketentuan yang relevan dengan query pengguna
3. Jelaskan perbedaan utama yang ditemukan
4. Berikan analisis dampak dari perubahan tersebut
5. Gunakan bahasa Indonesia yang jelas dan mudah dipahami
6. Fokus pada aspek praktis dan implementasi
7. Jika ada pasal yang dihapus, dipindahkan, atau ditambah, jelaskan dengan detail
8. Kutip nomor pasal yang spesifik dari kedua versi KUHP

=== FORMAT RESPONS ===
Berikan analisis dalam format berikut:

**Ringkasan Perbedaan:**
[Jelaskan perbedaan utama dalam 2-3 kalimat]

**Analisis Detail:**
[Analisis mendalam tentang perubahan dengan kutipan pasal spesifik]

**Dampak Praktis:**
[Jelaskan dampak implementasi perubahan]

**Kesimpulan:**
[Ringkasan dan rekomendasi]

Jawab dalam bahasa Indonesia yang profesional dan informatif."""
        
        return prompt

    def _generate_response_with_files(self, prompt: str) -> str:
        """Generate response menggunakan Gemini dengan PDF files"""
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Verify files are still active before generating
                self._verify_files_ready()

                # PENTING: Files harus dikirim SEBELUM prompt untuk Gemini File API
                # Ini memastikan model dapat mengakses konten file terlebih dahulu
                content = [
                    self.old_kuhp_file,  # KUHP Lama dulu
                    self.new_kuhp_file,  # KUHP Baru
                    prompt               # Prompt terakhir
                ]

                print(f"[KUHP] Generating response (attempt {attempt + 1}/{max_retries})...")
                response = self.model.generate_content(content)

                if response.text:
                    return response.text
                else:
                    raise Exception("Empty response received from Gemini")

            except Exception as e:
                print(f"[KUHP ERROR] Response generation failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"[KUHP] Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise

    def _verify_files_ready(self):
        """Verify both files are still active and ready"""
        try:
            old_file_info = genai.get_file(self.old_kuhp_file.name)
            new_file_info = genai.get_file(self.new_kuhp_file.name)

            if old_file_info.state.name != "ACTIVE":
                print(f"[KUHP WARNING] Old KUHP file state: {old_file_info.state.name}")
                raise Exception(f"KUHP Lama file is not active: {old_file_info.state.name}")

            if new_file_info.state.name != "ACTIVE":
                print(f"[KUHP WARNING] New KUHP file state: {new_file_info.state.name}")
                raise Exception(f"KUHP Baru file is not active: {new_file_info.state.name}")

        except Exception as e:
            print(f"[KUHP ERROR] File verification failed: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            "model_name": self.config.model_name,
            "is_initialized": self.is_initialized,
            "files_uploaded": bool(self.old_kuhp_file and self.new_kuhp_file),
            "old_kuhp_file": self.old_kuhp_file.display_name if self.old_kuhp_file else None,
            "new_kuhp_file": self.new_kuhp_file.display_name if self.new_kuhp_file else None
        }


def get_analyzer_instance() -> KUHPAnalyzer:
    """Get KUHP Analyzer instance untuk aplikasi"""
    return KUHPAnalyzer()