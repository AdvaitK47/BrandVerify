"""
BrandVerify Bulletproof HTTP & Preview Server
Zero-dependency Python server that serves the BrandVerify frontend and mock endpoints.
"""

import http.server
import socketserver
import os
import sys

PORT = 8000
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

class BrandVerifyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        raw_path = self.path.split('?')[0].rstrip('/')
        
        # Route mapping dictionary
        routes = {
            "": "index.html",
            "/": "index.html",
            "/index": "index.html",
            "/index.html": "index.html",
            
            "/dashboard": "dashboard.html",
            "/dashboard.html": "dashboard.html",
            
            "/brand": "brand.html",
            "/brand.html": "brand.html",
            
            "/submission": "submission.html",
            "/submission.html": "submission.html",
            
            "/review": "review.html",
            "/review.html": "review.html",
            
            "/login": "login.html",
            "/login.html": "login.html",
        }

        if raw_path in routes:
            target_rel = routes[raw_path]
            if os.path.exists(os.path.join(FRONTEND_DIR, target_rel)):
                self.path = "/" + target_rel
        elif raw_path.endswith(".html"):
            basename = os.path.basename(raw_path)
            if os.path.exists(os.path.join(FRONTEND_DIR, basename)):
                self.path = "/" + basename

        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/v1/auth/login"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <div style="padding:10px; border-radius:8px; background:rgba(255,255,255,0.08); border:1px solid #ffffff; color:#ffffff; font-size:0.85rem; margin-top:8px;">
              ✓ Logged in successfully! Opening your brands dashboard...
            </div>
            <script>
              localStorage.setItem('bv_signed_in', 'true');
              setTimeout(() => { window.location.href = 'dashboard.html'; }, 500);
            </script>
            """
            self.wfile.write(html.encode("utf-8"))
            return

        return super().do_POST()

def run():
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), BrandVerifyHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 65)
        print(" BrandVerify Local Server Active")
        print(f" URL:   {url}")
        print(" Serving directory: ./frontend")
        print("=" * 65)
        print("Routes:")
        print(f"  • Overview:            {url}/")
        print(f"  • Dashboard:           {url}/dashboard.html")
        print(f"  • Compliance Checker:  {url}/brand.html")
        print(f"  • Content Submission:  {url}/submission.html")
        print(f"  • Review & Diff Hub:   {url}/review.html")
        print(f"  • Log In / Sign Up:    {url}/login.html")
        print("=" * 65)
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    run()
