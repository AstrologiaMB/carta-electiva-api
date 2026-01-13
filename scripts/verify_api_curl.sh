
#!/bin/bash
# Start API in background on port 8111 to avoid conflicts
echo "🚀 Starting API Server on port 8111..."
# Use python directly to run uvicorn module
./venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8111 --log-level error &
PID=$!

echo "⏳ Waiting 5 seconds for server boot..."
sleep 5

echo "📡 Sending Request to /buscar-fechas-v2..."
curl -X POST "http://localhost:8111/buscar-fechas-v2" \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "test_curl",
           "tema": "trabajo",
           "fecha_inicio": "2025-08-15",
           "dias": 5,
           "ubicacion": {"ciudad": "Buenos Aires", "pais": "Argentina"},
           "carta_natal": {
             "fecha_nacimiento": "1990-01-01", 
             "hora_nacimiento": "12:00", 
             "ciudad": "Buenos Aires", 
             "pais": "Argentina", 
             "timezone": "America/Argentina/Buenos_Aires"
           }
         }'

echo ""
echo "🛑 Killing Server (PID $PID)..."
kill $PID
wait $PID 2>/dev/null
echo "✅ Done."
