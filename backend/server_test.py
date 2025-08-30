#!/usr/bin/env python3
"""
Simple server test script to verify API functionality
"""
import asyncio
import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Baseball Trade AI test server...")
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8080, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"Server startup error: {e}")
        import traceback
        traceback.print_exc()