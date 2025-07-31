#!/usr/bin/env python3
"""
Development server startup script for CLIP.LRU
"""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import passlib
        import jose
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False


def check_database():
    """Check database connection"""
    try:
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration in .env file")
        print("Or run: python scripts/init_db.py")
        return False


def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the development server"""
    print(f"Starting CLIP.LRU server on {host}:{port}")
    
    cmd = [
        "python", "-m", "uvicorn",
        "app.main:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"
    ]
    
    if reload:
        cmd.append("--reload")
    
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("🚀 Starting CLIP.LRU Development Server")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database():
        print("\n💡 Tip: Run 'python scripts/init_db.py' to initialize the database")
        sys.exit(1)
    
    # Parse command line arguments
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    if "--host" in sys.argv:
        host_index = sys.argv.index("--host")
        if host_index + 1 < len(sys.argv):
            host = sys.argv[host_index + 1]
    
    if "--port" in sys.argv:
        port_index = sys.argv.index("--port")
        if port_index + 1 < len(sys.argv):
            port = int(sys.argv[port_index + 1])
    
    if "--no-reload" in sys.argv:
        reload = False
    
    print(f"📡 Server will be available at:")
    print(f"   • API: http://{host}:{port}")
    print(f"   • Docs: http://{host}:{port}/docs")
    print(f"   • ReDoc: http://{host}:{port}/redoc")
    print()
    
    # Start server
    start_server(host, port, reload)


if __name__ == "__main__":
    main()
