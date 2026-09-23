import uvicorn
import webbrowser
import time
from threading import Thread

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 65)
    print("  LLM-Powered Resume Screening & Talent Matching Platform")
    print("  Starting server at http://127.0.0.1:8000")
    print("=" * 65)
    
    # Launch browser automatically
    Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
