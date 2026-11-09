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

class AttackDetector:
    def __init__(self,state,blocker,storage,threshold=1000):
        self.state = state # 탐지 결과 저장
        self.blocker = blocker # 차단을 요청할 대상 
        self.storage = storage # 기록을 남길 대상
        self.threshold = threshold # 탐지 임계점 기준값
        
    
        
    