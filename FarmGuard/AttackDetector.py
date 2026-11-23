"""
AttackDetector — 네트워크 UDP 트래픽을 감시해 Flooding 공격 여부를 판단하는 핵심 탐지 로직

[역할]
들어오는 UDP 패킷을 발신 IP별로 집계하고, 일정 시간 안에 임계치(threshold)를
넘으면 "공격"으로 판단한다. 공격으로 판단되면 Blocker에게 차단을 요청하고,
GatewayState에 결과를 기록한다. 공격이 멎으면 자동 복구도 트리거한다.

[품질 요구사항]
공격을 1초 이내에 탐지해야 함 — 집계 주기/판단 로직을 짤 때 이 기준을 염두에 둘 것.

[주의]
state.is_protected()가 False(무방비 모드)면 애초에 탐지 로직 자체를 돌리지 않는다
(무방비 상태를 "탐지는 못하지만 증상은 있는" 상태로 연출하기 위함).

[호출 관계]
- monitor_traffic() → (내부적으로 패킷 수신, requestCounts 집계)
- check_flooding(ip)가 True면 →
    blocker.block(ip)
    state.markAttack(ip)
    storage.insert_event("DETECT", ...)
- 공격이 멎으면 →
    blocker.unblock(ip)
    state.markRecovery(ip)
    storage.insert_event("RECOVER", ...)

[필요한 메소드]
- monitor_traffic()   : 패킷 수신해서 IP별 카운트 집계
- check_flooding(ip)  : 해당 IP가 임계치 넘었는지 판단
- run()               : 전체 탐지 루프 (별도 스레드)
"""
import socket
import time

class AttackDetector:
    def __init__(self,state,blocker,storage,threshold=1000):
        self.state = state # 현재 상태
        self.blocker = blocker # 차단을 요청할 대상
        self.storage = storage # 기록
        self.packet_count = {} # IP별로 지금까지 몇개 패킷이 왔는지 세는 카운터
        self.threshold = threshold # 탐지 임계점 기준값
    
    def check_flooding(self,ip):
        return self.packet_count.get(ip,0) >= self.threshold # 패킷 세는 카운터에 ip를 넣고 임계값을 넘는지 확인 
        
    def monitor_traffic(self): # 1초 내에 한 ip로부터 얼마나 많은 패킷이 들어오는지 트래픽 감시
        now = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0',9999))
        s.settimeout(1.0)
        while time.time() - now <= 1:
            try:
                data, addr = s.recvfrom(1024) # addr 
                ip = addr[0] # 입력온 패킷 ip주소 저장
                self.packet_count[ip] = self.packet_count.get(ip,0) + 1 # 패킷 카운터에 key값이 ip인 value값을 +1 (패킷 1개가 왔다는 것을 의미)
            except socket.timeout: # 패킷 1초간 안오면 while문 빠져나감
                print("1초간 패킷이 오지않음\n")
                break
        s.close()
        
    def run(self):  # 무한 관찰, 판단, 차단까지 하는 메서드
        while True:
            self.monitor_traffic()
            flood_list = []
            for ip in self.packet_count:
                if self.check_flooding(ip):
                    self.blocker.block(ip)
                    self.state.markAttack(ip)
                    self.storage.insert_event("DETECT", f"ip={ip}, count={self.packet_count[ip]}")
                    flood_list.append(ip)
            for ip in flood_list:
                self.packet_count.pop(ip)