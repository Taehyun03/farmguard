"""
SensorCollector — 아두이노(ArduinoSensor)로부터 환경 센서값을 읽어오는 담당

[역할]
USB 시리얼로 연결된 아두이노에서 온도/습도/토양수분/조도를 주기적으로 읽고,
그 결과를 GatewayState(최신값 갱신)와 Storage(기록 저장)에 전달한다.

[주의 — 흔한 오해]
AttackDetector와는 아무 관계가 없다! 센서값(온습도)과 네트워크 트래픽(공격 탐지)은
완전히 다른 데이터이므로, SensorCollector → AttackDetector로 뭔가를 전달하지 않는다.
SensorCollector는 오직 GatewayState, Storage하고만 대화한다.

[호출 관계]
- (내부) run() 루프가 read_sensor()를 반복 호출
- run() → state.setLatest(sample)
- run() → storage.insert_sensor(sample)
- run() → (무방비 상태에서 일정 시간 값이 안 들어오면) state.setOverloaded(True)

[필요한 메소드]
- read_sensor() : 아두이노로부터 한 번 값을 읽어와 dict로 반환
- run()         : 별도 스레드에서 1초 주기로 read_sensor() 반복 호출하는 루프
"""