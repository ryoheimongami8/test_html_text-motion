"""Static server for the BEANS! CM page. Serves the parent folder (so ../__old assets resolve)
and accepts three POST routes under <page dir>/:
  save         ?name=...   write an exported MP4 into ビーンズCM/out/
  save-config             overwrite ビーンズCM/config.json (validated as JSON first)
  save-asset   ?name=...   overwrite a file in ビーンズCM/assets/ (image/video replace from the editor panel)
"""
import http.server, json, os, sys, urllib.parse, webbrowser, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'out')
ASSETS = os.path.join(HERE, 'assets')
CONFIG_PATH = os.path.join(HERE, 'config.json')
PORT = next((int(a) for a in sys.argv[1:] if a.isdigit()), 8790)


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))

        if u.path.endswith('/save'):
            name = os.path.basename(urllib.parse.parse_qs(u.query).get('name', ['export.mp4'])[0]) or 'export.mp4'
            os.makedirs(OUT, exist_ok=True)
            path = os.path.join(OUT, name)
            with open(path, 'wb') as f:
                f.write(data)

        elif u.path.endswith('/save-config'):
            try:
                json.loads(data.decode('utf-8'))  # reject malformed JSON before it overwrites the real config
            except Exception as e:
                self.send_error(400, f'invalid JSON: {e}'); return
            path = CONFIG_PATH
            with open(path, 'wb') as f:
                f.write(data)

        elif u.path.endswith('/save-asset'):
            name = os.path.basename(urllib.parse.parse_qs(u.query).get('name', [''])[0])
            if not name:
                self.send_error(400, 'missing ?name='); return
            os.makedirs(ASSETS, exist_ok=True)
            path = os.path.join(ASSETS, name)
            with open(path, 'wb') as f:
                f.write(data)

        else:
            self.send_error(404); return

        body = str(path).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    url = f'http://localhost:{PORT}/' + urllib.parse.quote(os.path.basename(HERE)) + '/index.html'
    print('BEANS! CM ->', url)
    if '--no-browser' not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    http.server.ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
