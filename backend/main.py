import os
import google.generativeai as genai
import PyPDF2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="KUHP Difference Analyzer", version="1.0.0")

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

def extract_text_from_pdf(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

kuhp_old_text = ""
kuhp_new_text = ""

@app.on_event("startup")
async def startup_event():
    global kuhp_old_text, kuhp_new_text
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    genai.configure(api_key=gemini_api_key)
    
    documents_path = "../documents"
    
    try:
        kuhp_old_text = extract_text_from_pdf(f"{documents_path}/kuhp_old.pdf")
        kuhp_new_text = extract_text_from_pdf(f"{documents_path}/kuhp_new.pdf")
        print("PDF documents loaded successfully")
    except Exception as e:
        print(f"Error loading PDFs: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "KUHP Difference Analyzer API is running"}

@app.post("/analyze", response_model=QueryResponse)
async def analyze_kuhp_difference(request: QueryRequest):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-exp')
        
        prompt = f"""
        Anda adalah AI assistant yang bertugas menganalisis perbedaan antara KUHP lama dan KUHP baru.
        
        Teks KUHP Lama:
        {kuhp_old_text[:10000]}...
        
        Teks KUHP Baru:
        {kuhp_new_text[:10000]}...
        
        Pertanyaan pengguna: "{request.query}"
        
        Tugas Anda:
        1. Tentukan apakah pertanyaan relevan dengan KUHP (ya/tidak)
        2. Jika relevan, berikan analisis perbedaan yang komprehensif mengenai pasal atau topik yang ditanyakan
        3. Jika tidak relevan, tolak dengan sopan dan jelaskan bahwa scope terbatas pada KUHP
        
        Format jawaban:
        RELEVANCE: [YA/TIDAK]
        ANALYSIS: [Analisis lengkap perbedaan antara KUHP lama dan baru untuk topik yang ditanyakan, atau pesan penolakan jika tidak relevan]
        
        Berikan analisis yang detail tentang:
        - Perubahan yang terjadi
        - Pasal-pasal yang ditambah, dihapus, atau dimodifikasi
        - Implikasi dari perubahan tersebut
        
        Jika pertanyaan di luar scope KUHP, berikan pesan: "Maaf, saya hanya dapat membantu menganalisis perbedaan dalam dokumen KUHP. Silakan ajukan pertanyaan yang berkaitan dengan pasal atau topik dalam KUHP."
        """
        
        response = model.generate_content(prompt)
        
        response_text = response.text
        
        is_relevant = "YA" in response_text.split("RELEVANCE:")[1].split("ANALYSIS:")[0].strip().upper()
        
        analysis = response_text.split("ANALYSIS:")[1].strip() if "ANALYSIS:" in response_text else response_text
        
        return QueryResponse(
            response=analysis,
            is_relevant=is_relevant
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kuhp-analyzer-backend"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)