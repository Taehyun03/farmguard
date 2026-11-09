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