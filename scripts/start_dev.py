#!/usr/bin/env python3
"""
Development environment startup script for CLIP.LRU
Starts both backend and frontend servers
"""

import sys
import os
import subprocess
import time
import signal
from pathlib import Path
from threading import Thread

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DevServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True

    def start_backend(self):
        """Start the backend server"""
        print("🚀 Starting backend server...")
        
        try:
            # Check if dependencies are installed
            import fastapi
            import uvicorn
            print("✅ Backend dependencies found")
        except ImportError as e:
            print(f"❌ Missing backend dependency: {e}")
            print("Please install dependencies: pip install -r requirements.txt")
            return False

        # Start backend server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        try:
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor backend output
            def monitor_backend():
                for line in iter(self.backend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[Backend] {line.rstrip()}")
                    else:
                        break
            
            Thread(target=monitor_backend, daemon=True).start()
            
            # Wait a bit for backend to start
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ Backend server started on http://localhost:8000")
                return True
            else:
                print("❌ Backend server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False

    def start_frontend(self, simple_web_server=True):
        """Start the frontend server"""
        print("🎨 Starting frontend server...")

        # Check if we should use React frontend or HTML frontend
        frontend_dir = project_root / "frontend"
        web_dir = project_root / "web"

        if not simple_web_server and frontend_dir.exists() and (frontend_dir / "package.json").exists():
            return self.start_react_frontend()
        elif web_dir.exists() and (web_dir / "index.html").exists():
            return self.start_html_frontend()
        else:
            print("❌ No frontend found")
            return False

    def start_react_frontend(self):
        """Start React frontend"""
        frontend_dir = project_root / "frontend"

        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            install_cmd = ["npm", "install"]

            try:
                subprocess.run(
                    install_cmd,
                    cwd=frontend_dir,
                    check=True,
                    capture_output=True
                )
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install frontend dependencies: {e}")
                return False

        # Start frontend server
        cmd = ["npm", "run", "dev"]
        
        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor frontend output
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[Frontend] {line.rstrip()}")
                    else:
                        break
            
            Thread(target=monitor_frontend, daemon=True).start()
            
            # Wait a bit for frontend to start
            time.sleep(5)
            
            if self.frontend_process.poll() is None:
                print("✅ React frontend server started on http://localhost:3000")
                return True
            else:
                print("❌ React frontend server failed to start")
                return False

        except Exception as e:
            print(f"❌ Failed to start React frontend: {e}")
            return False

    def start_html_frontend(self):
        """Start HTML frontend"""
        web_dir = project_root / "web"

        # Start HTML frontend server
        cmd = [sys.executable, "server.py", "--port", "3000"]

        try:
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=web_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # Monitor frontend output
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if self.running:
                        print(f"[Frontend] {line.rstrip()}")
                    else:
                        break

            Thread(target=monitor_frontend, daemon=True).start()

            # Wait a bit for frontend to start
            time.sleep(3)

            if self.frontend_process.poll() is None:
                print("✅ HTML frontend server started on http://localhost:3000")
                return True
            else:
                print("❌ HTML frontend server failed to start")
                return False

        except Exception as e:
            print(f"❌ Failed to start HTML frontend: {e}")
            return False

    def stop_servers(self):
        """Stop both servers"""
        print("\n🛑 Stopping servers...")
        self.running = False
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                print("✅ Backend server stopped")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("🔪 Backend server killed")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                print("✅ Frontend server stopped")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("🔪 Frontend server killed")

    def run(self):
        """Run the development environment"""
        print("🎯 CLIP.LRU Development Environment")
        print("=" * 50)
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            self.stop_servers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start backend
            if not self.start_backend():
                print("❌ Failed to start backend server")
                return False
            
            # Start frontend
            if not self.start_frontend():
                print("❌ Failed to start frontend server")
                self.stop_servers()
                return False
            
            print("\n🎉 Development environment is ready!")
            print("📡 Backend API: http://localhost:8000")
            print("🎨 Frontend App: http://localhost:3000")
            print("📚 API Docs: http://localhost:8000/docs")
            print("\nPress Ctrl+C to stop all servers")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend server stopped unexpectedly")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend server stopped unexpectedly")
                    break
            
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_servers()
        
        return True


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start CLIP.LRU development environment")
    parser.add_argument("--backend-only", action="store_true", help="Start only backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Start only frontend server")
    
    args = parser.parse_args()
    
    server = DevServer()
    
    if args.backend_only:
        server.start_backend()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop_servers()
    elif args.frontend_only:
        server.start_frontend()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server.stop_servers()
    else:
        server.run()


if __name__ == "__main__":
    main()
