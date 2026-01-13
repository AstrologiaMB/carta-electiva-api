
import sys
import os
import json
from fastapi.testclient import TestClient

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

client = TestClient(app)

def test_api_v2():
    print("🚀 Probando Endpoint V2 (POST /buscar-fechas-v2)")
    
    payload = {
        "user_id": "test_user_123",
        "tema": "trabajo", # H10
        "fecha_inicio": "2025-08-15", # Safe date
        "dias": 5,
        "ubicacion": {
            "ciudad": "Buenos Aires",
            "pais": "Argentina"
        },
        "carta_natal": {
            "fecha_nacimiento": "1990-01-01",
            "hora_nacimiento": "12:00",
            "ciudad": "Buenos Aires",
            "pais": "Argentina",
            "timezone": "America/Argentina/Buenos_Aires"
        }
    }
    
    try:
        response = client.post("/buscar-fechas-v2", json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ Success!")
                stats = data['data']['estadisticas']
                print(f"   Momentos: {stats['total_momentos']}")
                print(f"   Tiempo: {stats['tiempo_calculo']}")
                print(f"   Factor: {stats['factor_optimizacion']}")
                
                # Check results
                candidates = data['data']['momentos']
                if len(candidates) > 0:
                    print(f"   First Candidate: {candidates[0]['fecha_hora']}")
                else:
                    print("   ⚠️ No candidates found (strict filters?)")
            else:
                print(f"❌ Failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_api_v2()
