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

    def _send_json(self, data, status=200):
        import json
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/api/v1/auth/login"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
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

        if self.path.startswith("/api/images/scan"):
            return self._send_json({
                "extracted_text": "Acme CloudScale Engine - Guaranteed 10X Performance With Zero Latency",
                "ocr_status": "success",
                "dominant_colors": [
                    {"hex": "#121214", "percentage": 52.4},
                    {"hex": "#ffffff", "percentage": 28.1},
                    {"hex": "#3b82f6", "percentage": 19.5}
                ],
                "palette_check": {
                    "status": "pass",
                    "threshold": 15.0,
                    "approved_colors": ["#121214", "#ffffff", "#a1a1aa"],
                    "matches": [
                        {"image_color": "#121214", "nearest_approved_color": "#121214", "delta_e": 0.0, "percentage": 52.4},
                        {"image_color": "#ffffff", "nearest_approved_color": "#ffffff", "delta_e": 0.0, "percentage": 28.1}
                    ],
                    "unmatched_colors": [],
                    "message": "All detected dominant colors match approved brand swatches."
                },
                "flags": [
                    {
                        "type": "ocr_text_claims",
                        "severity": "warning",
                        "message": "Absolute claim 'Guaranteed 10X Performance' detected in image copy without qualification."
                    }
                ]
            })

        if self.path.startswith("/api/media/audio/scan"):
            return self._send_json({
                "transcription": {
                    "transcript": "BrandVerify CloudScale engine is guaranteed to be 10X faster than any competitor on the market with zero downtime.",
                    "segments": [
                        {"start": 0.0, "end": 4.5, "text": "BrandVerify CloudScale engine is guaranteed to be 10X faster than any competitor on the market with zero downtime."}
                    ]
                },
                "spoken_claim_flags": [
                    {
                        "category": "absolute_claim",
                        "match": "guaranteed",
                        "snippet": "guaranteed to be 10X faster",
                        "message": "Absolute guarantee statement requires substantiating test disclosures."
                    }
                ],
                "loudness_check": {
                    "status": "pass",
                    "integrated_lufs": -23.8,
                    "target_lufs": -24.0,
                    "tolerance_lu": 1.0,
                    "acceptable_range": [-25.0, -23.0],
                    "message": "Integrated loudness (-23.8 LUFS) is within broadcast target tolerance."
                },
                "flags": [
                    {
                        "type": "spoken_risk",
                        "severity": "warning",
                        "message": "Absolute performance claim detected in spoken voiceover."
                    }
                ],
                "overall_status": "review_required"
            })

        if self.path.startswith("/api/media/video/scan"):
            return self._send_json({
                "scene_count": 4,
                "scenes": [
                    {"start_seconds": 0.0, "end_seconds": 2.4, "duration_seconds": 2.4},
                    {"start_seconds": 2.4, "end_seconds": 5.1, "duration_seconds": 2.7},
                    {"start_seconds": 5.1, "end_seconds": 7.8, "duration_seconds": 2.7},
                    {"start_seconds": 7.8, "end_seconds": 10.0, "duration_seconds": 2.2}
                ],
                "scene_transition_count": 3,
                "disclaimer_check": {
                    "required_disclaimer": "Terms apply. Results may vary.",
                    "minimum_seconds": 3.0,
                    "sample_interval_seconds": 0.25,
                    "estimated_longest_visible_seconds": 3.25,
                    "observed_start_seconds": 6.0,
                    "observed_end_seconds": 9.25,
                    "status": "pass",
                    "verification_method": "sampled_frame_ocr",
                    "message": "Disclaimer was detected in sampled video frames for 3.25s (exceeds 3.0s minimum requirement)."
                },
                "flags": [],
                "overall_status": "pass"
            })

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
