import os
import sys
import webbrowser
import datetime
import json
import time
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

DEFAULT_PORT = 8080

import urllib.parse

# In-memory telemetry cache to ensure ultra-fast responses without rate limits
_TELEMETRY_CACHE = {
    'last_time': 0,
    'data': None
}

def get_live_telemetry_data():
    now_ts = time.time()
    if _TELEMETRY_CACHE['data'] and (now_ts - _TELEMETRY_CACHE['last_time'] < 10):
        return _TELEMETRY_CACHE['data']

    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute

    # 1. IMGW Weather
    temp = 1.0
    try:
        req = urllib.request.Request('https://danepubliczne.imgw.pl/api/data/synop/station/krakow', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2.0) as r:
            d = json.loads(r.read())
            temp = float(d.get('temperatura', 1.0))
    except Exception:
        temp = 1.0

    # 2. ZTP GTFS-RT Fleet
    active_vehicles = 565
    try:
        import google.transit.gtfs_realtime_pb2 as gtfs
        req = urllib.request.Request('https://gtfs.ztp.krakow.pl/VehiclePositions.pb', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2.0) as r:
            feed = gtfs.FeedMessage()
            feed.ParseFromString(r.read())
            active_vehicles = len(feed.entity)
    except Exception:
        active_vehicles = 565

    # 3. Energy Tariff Zone B23 & EMS Decision
    is_peak = (7 <= hour < 13) or (17 <= hour < 22)
    is_night_valley = (hour >= 22 or hour < 6)

    # Temperature impact on HVAC load (e-SORT standard)
    hvac_factor = 1.0
    if temp < 5.0:
        hvac_factor = round(1.0 + (5.0 - temp) * 0.05, 2)
    elif temp > 25.0:
        hvac_factor = round(1.0 + (temp - 25.0) * 0.04, 2)

    if 20 <= hour <= 22:
        base_load = 0.70
        charging_demand = round(min(4.34, (hour - 19) * 1.5 + (minute / 60.0) * 1.2) * hvac_factor, 2)
        total_unmanaged = round(base_load + charging_demand, 2)
        bess_target_mw = -1.37
        grid_draw = round(max(0.0, total_unmanaged + bess_target_mw), 2)
        status_text = f"Wieczorny szczyt zjazdów MPK ({active_vehicles} pojazdów w sieci) | Ochrona mocy: {total_unmanaged} MW -> {grid_draw} MW"
        mode = "PEAK_SHAVING"
    elif is_night_valley:
        base_load = 0.70
        charging_demand = 1.80
        total_unmanaged = 2.50
        bess_target_mw = 0.90
        grid_draw = round(total_unmanaged + bess_target_mw, 2)
        status_text = f"Tania dolina nocna B23 (380 zł/MWh) | Ładowanie BESS z sieci: +0.90 MW"
        mode = "VALLEY_CHARGING"
    else:
        grid_draw = 1.90
        bess_target_mw = 0.0
        status_text = f"Gotowość EMS B23 | Stabilizacja napięcia i rezerwa wirująca ({active_vehicles} pojazdów ZTP)"
        mode = "STANDBY"

    res = {
        'status': 'OK',
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
        'clock': now.strftime('%H:%M'),
        'hour': hour,
        'minute': minute,
        'second': now.second,
        'temperature': temp,
        'hvac_factor': hvac_factor,
        'active_vehicles': active_vehicles,
        'b23_peak': is_peak,
        'bess_mw': bess_target_mw,
        'grid_draw_mw': grid_draw,
        'mode': mode,
        'status_text': status_text,
        'savings_annual_pln': 795721,
        'municipal_savings_pln': 3580000
    }
    _TELEMETRY_CACHE['last_time'] = now_ts
    _TELEMETRY_CACHE['data'] = res
    return res

class ThreadingSimpleServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

class KrakowMapHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow cross-origin and disable restrictive caching during dev
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, must-revalidate')
        super().end_headers()

    def resolve_alias(self, raw_path):
        clean_path = raw_path.split('?')[0].split('#')[0]
        unquoted = urllib.parse.unquote(clean_path).lstrip('/')

        if unquoted in ('', 'index.html'):
            return '/krakow_smartgrid_scada.html'

        filename = os.path.basename(unquoted)
        lower_name = filename.lower()

        # Direct check in 0_DLA_CIEBIE_I_JURY/
        jury_path = os.path.join('0_DLA_CIEBIE_I_JURY', filename)
        if os.path.exists(jury_path):
            return '/' + jury_path.replace('\\', '/')

        # Case-insensitive / normalized lookup in 0_DLA_CIEBIE_I_JURY
        if os.path.isdir('0_DLA_CIEBIE_I_JURY'):
            for jf in os.listdir('0_DLA_CIEBIE_I_JURY'):
                if jf.lower() == lower_name:
                    return '/0_DLA_CIEBIE_I_JURY/' + jf

        # Tutorial / Presentation fallback
        if any(k in lower_name for k in ['tutorial', 'prezentacja_teoria', 'samouczek']):
            for candidate in [
                'krakow_smartgrid_scada.html',
                os.path.join('0_DLA_CIEBIE_I_JURY', '00_PREZENTACJA_PRZEWODNIK_PROJEKTU.pdf'),
                os.path.join('_archiwum_robocze', 'stare_prezentacje_i_wideo', 'prezentacja_teoria_i_tutorial.html')
            ]:
                if os.path.exists(candidate):
                    return '/' + candidate.replace('\\', '/')

        # 1. 2-page Project Description PDF (§ 5 ust. 2 pkt 2)
        if lower_name.endswith('.pdf') and any(k in lower_name for k in ['opis', 'celu', '2_stron', 'summary']):
            for candidate in [
                os.path.join('0_DLA_CIEBIE_I_JURY', '02_OPIS_PROJEKTU_2_STRONY_UMK.pdf'),
                os.path.join('0_DLA_CIEBIE_I_JURY', '01_OPIS_PROJEKTU_2_STRONY_UMK.pdf'),
                'Krakow_SmartGrid_Opis_Projektu_i_Celu.pdf'
            ]:
                if os.path.exists(candidate):
                    return '/' + candidate.replace('\\', '/')
        # 2. Financial Model Excel
        elif lower_name.endswith('.xlsx') and any(k in lower_name for k in ['model', 'finans', 'wola_duchacka', 'excel']):
            for candidate in [
                os.path.join('0_DLA_CIEBIE_I_JURY', '04_MODEL_FINANSOWY_EXCEL.xlsx'),
                os.path.join('0_DLA_CIEBIE_I_JURY', '02_MODEL_FINANSOWY_EXCEL.xlsx'),
                '02_MODEL_FINANSOWY_EXCEL.xlsx'
            ]:
                if os.path.exists(candidate):
                    return '/' + candidate.replace('\\', '/')
        # 3. Technical Dossier & Guide PDF
        elif lower_name.endswith('.pdf') and any(k in lower_name for k in ['prezentacja', 'przewodnik', 'dokumentacja', 'techniczn', 'dossier']):
            for candidate in [
                os.path.join('0_DLA_CIEBIE_I_JURY', '03_PREZENTACJA_I_DOKUMENTACJA_TECHNICZNA.pdf'),
                os.path.join('0_DLA_CIEBIE_I_JURY', '00_PREZENTACJA_PRZEWODNIK_PROJEKTU.pdf'),
                os.path.join('0_DLA_CIEBIE_I_JURY', '03_DOKUMENTACJA_TECHNICZNA.pdf')
            ]:
                if os.path.exists(candidate):
                    return '/' + candidate.replace('\\', '/')
        # 4. Official Contest Submission ZIP
        elif lower_name.endswith('.zip') and any(k in lower_name for k in ['zgloszen', 'paczka', 'konkurs']):
            for candidate in [
                os.path.join('0_DLA_CIEBIE_I_JURY', 'Krakow_SmartGrid_Zgloszenie_Konkursowe.zip'),
                os.path.join('0_DLA_CIEBIE_I_JURY', '08_PACZKA_ZGLOSZENIOWA_DO_WYSLANIA.zip'),
                os.path.join('_formalnosci_etap1_archive', '08_PACZKA_ZGLOSZENIOWA_DO_WYSLANIA.zip')
            ]:
                if os.path.exists(candidate):
                    return '/' + candidate.replace('\\', '/')

        return raw_path

    def do_HEAD(self):
        self.path = self.resolve_alias(self.path)
        try:
            super().do_HEAD()
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        if self.path.startswith('/api/live-telemetry') or self.path.startswith('/api/live'):
            telemetry = get_live_telemetry_data()
            payload = json.dumps(telemetry, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(payload)
            return

        self.path = self.resolve_alias(self.path)
        try:
            super().do_GET()
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass

    def guess_type(self, path):
        if path.endswith('.glb'):
            return 'model/gltf-binary'
        if path.endswith('.json') or path.endswith('.geojson') or path.endswith('.city.json'):
            return 'application/json'
        if path.endswith('.js'):
            return 'application/javascript'
        if path.endswith('.css'):
            return 'text/css'
        if path.endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        if path.endswith('.pdf'):
            return 'application/pdf'
        if path.endswith('.zip'):
            return 'application/zip'
        return super().guess_type(path)

def create_server(start_port=DEFAULT_PORT, max_attempts=20):
    """Binds to the first available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            server_address = ('127.0.0.1', port)
            httpd = ThreadingSimpleServer(server_address, KrakowMapHandler)
            return httpd, port
        except OSError:
            continue
    raise RuntimeError(f"Nie udalo sie znalezc wolnego portu w zakresie {start_port} - {start_port + max_attempts}")

def start_server(open_browser=True, target_page=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    httpd, port = create_server(DEFAULT_PORT)
    if not target_page:
        target_page = "krakow_smartgrid_scada.html"
    url = f"http://localhost:{port}/{target_page.lstrip('/')}"
    print(f"\n=======================================================")
    print(f"  KRAKÓW SMARTGRID ENTERPRISE SCADA CONTROL CENTER")
    print(f"  Adres lokalny: {url}")
    print(f"  Serwowane pliki z: {base_dir}")
    print(f"=======================================================\n")
    if open_browser:
        print(f"Otwieram przegladarke: {url}...")
        webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
        httpd.server_close()

if __name__ == '__main__':
    target = None
    open_b = True
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--no-browser", "-n"):
            open_b = False
        elif arg in ("--page", "-p") and i + 1 < len(args):
            i += 1
            target = args[i]
        elif not arg.startswith("-") and target is None:
            target = arg
        i += 1
    start_server(open_browser=open_b, target_page=target)
