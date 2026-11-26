"""인스타그램 자동 게시용 10장(표지 1장 + 뉴스 9장, 번호 1/9~9/9)을 그린다.
사이트 index.html 파일은 바꾸지 않고, 브라우저에 불러올 때만 뉴스 번호 "/10"을 "/9"로 바꿔 그린다.
사용: python3 render_instagram.py <site_dir> YYYY-MM-DD <out_dir>
결과: 피터팬_고객보험노트_YYYYMMDD_insta_01.png(표지) ~ _10.png(뉴스 9번)"""
import sys, os, base64, threading, http.server, functools, socketserver
from playwright.sync_api import sync_playwright
site, date, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
OLD = "x.fillText(`${i+1}/10`,936,137)"
NEW = "x.textAlign='center';x.fillText(`${i+1}/9`,975.5,137);x.textAlign='left'"
html = open(os.path.join(site, "index.html"), encoding="utf-8").read()
assert html.count(OLD) == 1, "사이트 카드 코드의 뉴스 번호 부분을 찾지 못했어요"
html = html.replace(OLD, NEW)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=site)
H.log_message = lambda *a: None
srv = socketserver.TCPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"
def route(r):
    u = r.request.url
    if u.startswith(base + "/index.html"):
        return r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
    return r.continue_() if u.startswith(base) else r.abort()
with sync_playwright() as p:
    exe = "/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None
    b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"])
    pg = b.new_page(); pg.route("**/*", route)
    pg.goto(base + "/index.html")
    pg.wait_for_function("window.__deck !== undefined", timeout=20000)
    urls = pg.evaluate("""async (d) => { const D = await window.__deck(d,'customer'); return D.cs.map(c => c.toDataURL('image/png')); }""", date)
    pick = [0] + list(range(2, 11))   # 표지 + 뉴스 1~9
    ymd = date.replace("-", "")
    for k, i in enumerate(pick):
        open(os.path.join(out, f"피터팬_고객보험노트_{ymd}_insta_{k+1:02d}.png"), "wb").write(base64.b64decode(urls[i].split(",")[1]))
    print(len(pick), "instagram cards ->", out)
    b.close()
srv.shutdown()
