import sys
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

if __name__ == "__main__":
    import uvicorn

    from src.main import app

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
