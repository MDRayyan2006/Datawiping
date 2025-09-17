#!/usr/bin/env python3
"""
Simple HTTP server for the DataWipe web frontend
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent
os.chdir(script_dir)

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    """Start the web server"""
    print("🌐 Starting DataWipe Web Frontend Server...")
    print(f"📁 Serving files from: {script_dir}")
    print(f"🌍 Server will be available at: http://localhost:{PORT}")
    print("📱 Open your browser and navigate to the URL above")
    print("🔄 Make sure the FastAPI backend is running on http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Please stop the other server or use a different port.")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
