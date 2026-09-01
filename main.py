import uvicorn
import os
import sys

# Ensure backend folder is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Railway requires 0.0.0.0, not 127.0.0.1
    print(f"Starting Stumpy AI on {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
