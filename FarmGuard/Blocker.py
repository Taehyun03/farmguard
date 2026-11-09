"""
Blocker — 공격자로 판단된 IP를 실제로 네트워크 차단/해제하는 담당

[역할]
AttackDetector가 "이 IP 공격자야"라고 판단해서 요청하면, 실제로 리눅스
iptables 규칙을 걸어서 해당 IP의 트래픽을 막는다(block). 복구 조건이
충족되면 그 규칙을 풀어준다(unblock).

[품질 요구사항]
장애 발생 지점을 3초 이내에 복구해야 함 — unblock 판단 주기를 짤 때 염두에 둘 것.

[호출 관계]
- AttackDetector → block(ip)      (공격 탐지 시)
- AttackDetector → unblock(ip)    (복구 조건 충족 시)
- AttackDetector → is_blocked(ip) (지금 이 IP가 차단 중인지 확인할 때)

[필요한 메소드]
- block(ip)      : iptables로 해당 IP 차단 + 차단 목록에 기록
- unblock(ip)    : iptables 규칙 해제 + 차단 목록에서 제거
- is_blocked(ip) : 해당 IP가 지금 차단 중인지 True/False 반환
"""