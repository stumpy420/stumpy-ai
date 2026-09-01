import uvicorn
import os
import sys

# Enable UTF-8 for windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend folder is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("  [STARTING] Stumpy AI - The AI That Learns With You")
    print("  [SERVER]   Serving at: http://localhost:8000")
    print("  [STORAGE]  Local Memory & SQLite: data/stumpy.db")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
