"""Local entrypoint: python backend/main.py"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        app_dir=str(Path(__file__).resolve().parent),
    )
