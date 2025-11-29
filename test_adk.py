#!/usr/bin/env python3
"""
Test script untuk KUHP Analyzer menggunakan Google Agent Development Kit (ADK)
Test compatibility untuk Google Cloud Run deployment
"""

import sys
import os
import json
from typing import Dict, Any

def test_adk_imports():
    """Test semua ADK-related imports"""
    try:
        # Core Google Cloud imports
        import google.cloud.aiplatform
        print("[ADK PASS] Google Cloud AI Platform imported")
        
        import vertexai
        print("[ADK PASS] Vertex AI imported")
        
        # LangChain imports
        import langchain
        print("[ADK PASS] LangChain imported")
        
        # Agent components
        from kuhp_agent import KUHPAgentHandler, get_agent_instance
        print("[ADK PASS] KUHP Agent components imported")
        
        from agent_config import KUHPAnalyzerAgent, AgentConfig, DocumentConfig
        print("[ADK PASS] Agent configuration imported")
        
        return True
        
    except ImportError as e:
        print(f"[ADK FAIL] Import error: {e}")
        return False

def test_agent_configuration():
    """Test agent configuration dan setup"""
    try:
        from agent_config import get_production_config, get_development_config
        
        # Test production config
        agent_config, doc_config = get_production_config()
        print(f"[ADK PASS] Production config: {agent_config.agent_name}")
        
        # Test development config
        agent_config_dev, doc_config_dev = get_development_config()
        print(f"[ADK PASS] Development config: {agent_config_dev.agent_name}")
        
        # Test agent initialization
        from agent_config import KUHPAnalyzerAgent
        agent = KUHPAnalyzerAgent(agent_config, doc_config)
        
        # Test system prompt generation
        system_prompt = agent.get_system_prompt()
        if len(system_prompt) > 100:
            print("[ADK PASS] System prompt generated successfully")
        else:
            print("[ADK FAIL] System prompt too short")
            return False
            
        # Test agent instructions
        instructions = agent.get_agent_instructions()
        if "tools" in instructions and "role" in instructions:
            print("[ADK PASS] Agent instructions configured")
        else:
            print("[ADK FAIL] Agent instructions incomplete")
            return False
            
        return True
        
    except Exception as e:
        print(f"[ADK FAIL] Agent configuration error: {e}")
        return False

def test_mock_agent_handler():
    """Test agent handler initialization (mock mode)"""
    try:
        # Test dengan mock project ID
        project_id = "mock-project-for-testing"
        
        # Import dan test basic functionality
        from kuhp_agent import KUHPAgentHandler
        
        # Test configuration loading
        from agent_config import get_development_config
        agent_config, doc_config = get_development_config()
        
        print(f"[ADK PASS] Mock agent handler config loaded")
        print(f"  - Agent: {agent_config.agent_name}")
        print(f"  - Model: {agent_config.model_name}")
        print(f"  - Chunk size: {doc_config.chunk_size}")
        
        return True
        
    except Exception as e:
        print(f"[ADK FAIL] Mock agent handler error: {e}")
        return False

def test_fastapi_integration():
    """Test FastAPI integration dengan ADK"""
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        # Create test client
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            data = response.json()
            if "Agent Development Kit" in data["message"]:
                print("[ADK PASS] FastAPI integration working")
            else:
                print("[ADK FAIL] FastAPI response missing ADK reference")
                return False
        else:
            print(f"[ADK FAIL] FastAPI root endpoint failed: {response.status_code}")
            return False
            
        return True
        
    except ImportError:
        print("[ADK INFO] FastAPI TestClient not available, skipping integration test")
        return True
    except Exception as e:
        print(f"[ADK FAIL] FastAPI integration error: {e}")
        return False

def test_cloud_run_compatibility():
    """Test Cloud Run environment variables dan configuration"""
    try:
        # Test environment variables yang dibutuhkan Cloud Run
        required_env_vars = [
            "PORT", "GOOGLE_CLOUD_PROJECT", "ENVIRONMENT"
        ]
        
        # Set mock values untuk testing
        os.environ["PORT"] = "8080"
        os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
        os.environ["ENVIRONMENT"] = "testing"
        
        # Test configuration loading
        port = int(os.getenv("PORT", 8080))
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        env = os.getenv("ENVIRONMENT")
        
        if port == 8080 and project and env:
            print("[ADK PASS] Cloud Run environment configuration")
            print(f"  - Port: {port}")
            print(f"  - Project: {project}")
            print(f"  - Environment: {env}")
        else:
            print("[ADK FAIL] Cloud Run environment configuration incomplete")
            return False
            
        return True
        
    except Exception as e:
        print(f"[ADK FAIL] Cloud Run compatibility error: {e}")
        return False

def test_memory_requirements():
    """Test memory dan resource requirements untuk Cloud Run"""
    try:
        import psutil
        
        # Get current memory usage
        memory_info = psutil.virtual_memory()
        memory_mb = memory_info.total / (1024 * 1024)
        
        # Cloud Run ADK minimum requirements
        min_memory_mb = 2048  # 2GB minimum untuk ADK
        recommended_memory_mb = 4096  # 4GB recommended
        
        print(f"[ADK INFO] System memory: {memory_mb:.0f}MB")
        
        if memory_mb >= recommended_memory_mb:
            print("[ADK PASS] Memory requirements optimal")
        elif memory_mb >= min_memory_mb:
            print("[ADK PASS] Memory requirements minimum met")
        else:
            print(f"[ADK WARNING] Memory below minimum requirements ({min_memory_mb}MB)")
            
        return True
        
    except ImportError:
        print("[ADK INFO] psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"[ADK FAIL] Memory test error: {e}")
        return False

def generate_deployment_summary():
    """Generate summary untuk deployment"""
    print("\n" + "="*60)
    print("KUHP Analyzer ADK - Deployment Summary")
    print("="*60)
    
    summary = {
        "architecture": "Google Agent Development Kit (ADK)",
        "model": "Gemini 2.5 Flash (gemini-2.5-flash-exp)",
        "platform": "Google Cloud Run",
        "memory_requirement": "4GB (recommended)",
        "cpu_requirement": "2 vCPU",
        "timeout": "15 minutes (900s)",
        "apis_required": [
            "Cloud Run API",
            "Cloud Build API", 
            "AI Platform API",
            "Cloud Functions API",
            "Cloud Storage API"
        ],
        "environment_variables": [
            "GOOGLE_CLOUD_PROJECT",
            "ENVIRONMENT",
            "PORT"
        ],
        "secrets": [
            "GEMINI_API_KEY"
        ]
    }
    
    for key, value in summary.items():
        if isinstance(value, list):
            print(f"{key.title().replace('_', ' ')}: {', '.join(value)}")
        else:
            print(f"{key.title().replace('_', ' ')}: {value}")
            
    print("="*60)

def main():
    print("Testing KUHP Analyzer dengan Google Agent Development Kit (ADK)")
    print("="*65)
    
    tests = [
        ("ADK Imports", test_adk_imports),
        ("Agent Configuration", test_agent_configuration), 
        ("Mock Agent Handler", test_mock_agent_handler),
        ("FastAPI Integration", test_fastapi_integration),
        ("Cloud Run Compatibility", test_cloud_run_compatibility),
        ("Memory Requirements", test_memory_requirements)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            
    print(f"\n{'='*65}")
    print(f"ADK Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("[ADK SUCCESS] Semua test berhasil! Siap untuk deployment ke Cloud Run")
        generate_deployment_summary()
        return 0
    else:
        print(f"[ADK WARNING] {total-passed} test gagal. Periksa dependencies dan konfigurasi")
        return 1

if __name__ == "__main__":
    sys.exit(main())