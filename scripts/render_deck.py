"""사이트(index.html)의 카드 그리기 기능(window.__deck)으로 13장 PNG를 뽑는다.
사용: python3 render_deck.py <site_dir> YYYY-MM-DD customer <out_dir>"""
import sys, os, base64, threading, http.server, functools, socketserver
from playwright.sync_api import sync_playwright
site, date, aud, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
H.log_message = lambda *a: None
srv = socketserver.TCPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page()
    pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(f"http://127.0.0.1:{port}") else r.continue_())
    pg.goto(f"http://127.0.0.1:{port}/index.html")
    pg.wait_for_function("window.__deck !== undefined", timeout=20000)
    urls = pg.evaluate("""async ([d,a]) => { const D = await window.__deck(d,a); return D.cs.map(c => c.toDataURL('image/png')); }""", [date, aud])
    for i, u in enumerate(urls):
        open(os.path.join(out, f"피터팬_고객보험노트_{date.replace('-','')}_{i+1:02d}.png"), "wb").write(base64.b64decode(u.split(",")[1]))
    print(len(urls), "cards ->", out)
    b.close()
srv.shutdown()
