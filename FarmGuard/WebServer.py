"""
WebServer — HTTP 서버로 대시보드 화면과 API를 제공하는 담당 (Farmer가 보는 창구)

[역할]
다른 5개 클래스가 만들어낸 상태/기록을 사람(Farmer)이 웹 브라우저로 볼 수 있게
응답해준다. 직접 센서를 읽거나 공격을 판단하지 않고, GatewayState/Storage를
"읽기"만 한다 (예외: 토글 요청은 GatewayState에 "쓰기"를 요청).

[제공해야 하는 API]
- GET  /              → 대시보드 HTML 페이지 그대로 응답
- GET  /api/status    → state.snapshot() 결과를 JSON으로 응답
- GET  /api/history   → storage.recent_history(100) 결과를 JSON으로 응답
- POST /api/toggle    → state.toggle_protection() 호출 후, 바뀐 상태를 JSON으로 응답

[호출 관계]
- handle_status_request()  → state.snapshot()
- handle_toggle_request()  → state.toggle_protection()
- handle_history_request() → storage.recent_history()

[필요한 메소드]
- handle_status_request()
- handle_toggle_request()
- handle_history_request()
- serve() : 실제 HTTP 서버를 띄우고 요청을 위 메소드들로 분기
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class WebServer:
    def __init__(self, state, storage, host="0.0.0.0", port=8080):
        self.state = state
        self.storage = storage
        self.host = host
        self.port = port

    def handle_status_request(self):
        return self.state.snapshot()

    def handle_toggle_request(self):
        self.state.setProtection()   # 토글만 실행하고
        return self.state.snapshot() # 바뀐 전체 상태를 받아서 리턴

    def handle_history_request(self):
        return self.storage.recent_history(100)

    def serve(self):
        outer = self  # Handler 클래스 안에서 이 WebServer 객체를 쓰기 위해 이름을 따로 잡아둠

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/":
                    with open("dashboard.html", "rb") as f:
                        body = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path == "/api/status":
                    self._send_json(outer.handle_status_request())
                elif self.path == "/api/history":
                    self._send_json(outer.handle_history_request())
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                if self.path == "/api/toggle":
                    self._send_json(outer.handle_toggle_request())
                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer((self.host, self.port), Handler)
        server.serve_forever()