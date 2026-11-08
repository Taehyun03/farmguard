import threading
import time

class GatewayState:
    def __init__(self):
        self._lock = threading.Lock()
        self._protected = False # 팜가드 보호 기능이 켜져있나?
        self._mode = "정상" # 현재 공격이 탐지 되었나?
        self._attacker = None # 공격자 IP주소 저장
        self._msg = "정상 동작 중입니다." # 웹에 표시해 사람이 읽게되는 설명
        self._latest = None # 방금 들어온 센서값 한 묶음 
        self._events = [] # 최근 있었던 이벤트 / 공격탐지됨 등등 정보 
        self._overloaded = False # 무방비 상태에서 센서수집이 멈췄는가
    def setProtection(self):
        with self._lock:
            self._protected = not self._protected # 팜가드 온/오프 값을 뒤집기만 함.
            # 값들을 모두 초기화함
            self._mode = "정상"
            self._attacker = None
            self._overloaded = False
            
            if self._protected: # 팜가드가 켜져있을 시
                self._msg = "정상 동작 중입니다."
            else: # 팜가드가 꺼져있을 시
                self._msg = "팜가드가 동작 중이지 않습니다."
    
    def markAttack(self, ip): # 공격 탐지 시
        with self._lock:
            self._attacker = ip # 입력받은 ip 변수에 저장
            self._mode = "공격탐지"
            self._msg = f"{ip}에서 공격이 탐지되었습니다."
            now = datetime.now().strftime("%H:%M:%S")
            self._events = [{"ts":now,"kind":"DETECT","detail":self._msg}] + self._events
                
    def setLatest(self,sample): # 아두이노 센서값 저장
        with self._lock:
            self._latest = sample
    
    def setOverloaded(self,value): # 무방비상태에서 센서 수집이 끊겼는지 여부, 받는 값은 불리언
        with self._lock:
            self._overloaded = value
    
    def markRecovery(self,ip): # 공격 복구 시
        with self._lock:
            self._attacker = None
            self._mode = "정상"
            self._msg = f"{ip}로부터 받은 공격을 복구했습니다."
            now = datetime.now().strftime("%H:%M:%S")
            self._events = [{"ts":now,"kind":"RECOVER","detail":self._msg}] + self._events
    
    def is_protected(self): # 다른클래스가 지금 보호모드 on off 물어볼때 리턴하는 메소드
        with self._lock:
            return self._protected
        
    def snapshot(self): # webserver가 대시보드에 응답할때 init 변수 7개를 딕셔너리로 만들어 리턴해주는 함수
        with self._lock:
            return {
                "protected":self._protected,
                "mode":self._mode,
                "attacker":self._attacker,
                "msg":self._msg,
                "latest":self._latest,
                "events":self._events,
                "overloaded":self._overloaded
            }