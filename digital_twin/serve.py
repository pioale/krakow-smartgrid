"""
Kraków EcoGrid - Web-GIS & 3D Digital Twin HTTP Server
Uruchamia lokalny serwer HTTP dla interaktywnej mapy Web-GIS i bliźniaka cyfrowego.
Eliminuje ograniczenia protokołu file:/// oraz błędy CORS.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 8088
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS for local development & Web-GIS asset loading
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress noisy HTTP GET logging in console
        pass


def run_server():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    
    # Allow specifying target page: 'map.html' or 'index.html'
    target_page = "map.html"
    for arg in sys.argv[1:]:
        if not arg.startswith("-") and (".html" in arg):
            target_page = arg
            break
            
    url_map = f"http://localhost:{PORT}/map.html"
    url_3d = f"http://localhost:{PORT}/index.html"
    target_url = f"http://localhost:{PORT}/{target_page}"
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"===========================================================")
            print(f"⚡ Krakow EcoGrid: Smart Transit & Energy GIS is running!")
            print(f"🗺️  Mapa Web-GIS (MapLibre GL): {url_map}")
            print(f"🏙️  Makieta 3D (Three.js):     {url_3d}")
            print(f"🌐 Otwieranie: {target_url}")
            print(f"🛑 Naciśnij Ctrl+C, aby zatrzymać serwer.")
            print(f"===========================================================")
            sys.stdout.flush()
            
            if "--no-browser" not in sys.argv:
                webbrowser.open(target_url)
                
            httpd.serve_forever()
    except OSError as e:
        if "already in use" in str(e) or getattr(e, 'errno', None) in (98, 10048):
            print(f"ℹ️  Serwer Krakow EcoGrid juz dziala na porcie {PORT}.")
            print(f"🗺️  Mapa Web-GIS: {url_map}")
            sys.stdout.flush()
            if "--no-browser" not in sys.argv:
                webbrowser.open(target_url)
        else:
            raise e
    except KeyboardInterrupt:
        print("\nZatrzymano serwer Krakow EcoGrid.")


if __name__ == "__main__":
    run_server()
