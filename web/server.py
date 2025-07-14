#!/usr/bin/env python3
"""
Simple static file server for the HTML frontend
"""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support and API proxy"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Session-Id')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests with API proxy"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            # Serve static files
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def do_PUT(self):
        """Handle PUT requests"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404)
    
    def proxy_to_backend(self):
        """Proxy API requests to backend server"""
        import urllib.request
        import urllib.error
        
        # Backend URL
        backend_url = f"http://localhost:8000{self.path}"
        
        try:
            # Get request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(
                backend_url,
                data=body,
                method=self.command
            )
            
            # Copy headers
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)
            
            # Make request to backend
            with urllib.request.urlopen(req) as response:
                # Send response status
                self.send_response(response.status)
                
                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['server', 'date']:
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Copy response body
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            self.send_response(e.code)
            
            # Copy error response headers
            for header, value in e.headers.items():
                if header.lower() not in ['server', 'date']:
                    self.send_header(header, value)
            
            self.end_headers()
            
            # Copy error response body
            self.wfile.write(e.read())
            
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(502, "Backend server unavailable")
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[Frontend] {self.address_string()} - {format % args}")


def main():
    """Start the frontend server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start CLIP.LRU frontend server")
    parser.add_argument("--port", type=int, default=3000, help="Port to run on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    
    args = parser.parse_args()
    
    # Change to web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    print(f"🎨 Starting CLIP.LRU Frontend Server")
    print(f"📁 Serving files from: {web_dir}")
    print(f"🌐 Frontend: http://{args.host}:{args.port}")
    print(f"🔗 API Proxy: http://{args.host}:{args.port}/api -> http://localhost:8000/api")
    print(f"📚 Make sure backend is running on http://localhost:8000")
    print()
    
    try:
        server = HTTPServer((args.host, args.port), CORSRequestHandler)
        print(f"✅ Server started successfully!")
        print(f"Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
