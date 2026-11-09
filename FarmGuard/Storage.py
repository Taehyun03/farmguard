"""
Storage — SQLite 저장소: 센서 기록과 이벤트 로그를 "영구" 저장

[역할]
GatewayState가 "지금 이 순간"만 기억한다면, Storage는 "지나간 기록"을
DB에 남겨서 나중에 조회할 수 있게 한다 (대시보드 실시간 그래프의 과거 데이터,
이력 조회용).

[호출 관계]
- SensorCollector  → insert_sensor()  (센서값 읽을 때마다)
- AttackDetector   → insert_event()   (공격 탐지 시, kind="DETECT")
- Blocker          → insert_event()   (복구 시, kind="RECOVER")
- WebServer        → recent_history() (대시보드 그래프 초기값 조회용)

[필요한 메소드]
- insert_sensor(sample: dict)  : 센서값 한 묶음을 sensor 테이블에 저장
- insert_event(kind: str, detail: str) : 이벤트 한 줄을 event 테이블에 저장
- recent_history(limit: int)   : 최근 센서 기록 N개를 시각 역순으로 조회

[주의]
여러 스레드가 동시에 DB에 쓰므로, sqlite3 connection을 스레드마다 따로 만들고
쓰기 작업은 Lock으로 보호해야 한다 (state.py의 Lock 패턴 참고).
"""