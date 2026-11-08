# GatewayState 설계 문서

> 작성자: 김태현 · 작성일: 2026-11-08
> 대상 파일: `state.py`

## 1. 이 클래스는 뭔가

`GatewayState`는 팜가드 전체 시스템이 "지금 무슨 상황인지" 공유해서 보는 **공유 상태 저장소**다. 센서를 직접 읽지도, 공격을 탐지하지도, 차단하지도 않는다. 그냥 **다른 클래스들이 알아낸 결과를 적어두고, 누가 물어보면 지금 상태를 알려주는 역할**만 한다.

### 왜 이게 필요한가

우리 시스템은 여러 부분이 동시에 돌아간다.

- `SensorCollector`는 계속 센서값을 읽음
- `AttackDetector`는 계속 트래픽을 감시함
- `Blocker`는 탐지 결과에 따라 IP를 차단/해제함
- `WebServer`는 1초마다 대시보드에 "지금 상태" 응답을 줘야 함

이 4개가 서로 직접 정보를 주고받으면 복잡해지므로, 중간에 **공유 칠판 하나**를 두고 다들 거기에만 쓰고 거기서만 읽게 한다.

| 쓰는 쪽 (상태 변경) | 읽는 쪽 (상태 조회) |
|---|---|
| `SensorCollector`, `AttackDetector`, `Blocker` | `WebServer` |

> 대시보드가 없어도 이 클래스는 필요하다 — `AttackDetector`가 탐지 로직을 돌릴지 말지 판단하려면 "지금 보호 모드 켜져 있나?"를 먼저 확인해야 하기 때문.

## 2. 멀티스레드 안전성 (Lock)

이 클래스의 변수들은 센서 수집 스레드 / 공격 탐지 스레드 / 웹 요청 스레드가 **동시에** 읽고 쓴다. 보호 없이 접근하면 두 가지 문제가 생긴다.

1. **경쟁 상태(race condition)**: `self._events = [new] + self._events` 같은 코드는 내부적으로 "읽기→계산→쓰기" 세 단계로 쪼개져 실행된다. 두 스레드가 동시에 읽어가면, 먼저 쓴 결과가 나중에 쓴 쪽에 덮어써져 사라질 수 있다.
2. **어중간한 상태 노출**: 관련된 변수 여러 개(`protected`, `mode`, `attacker`, `msg`)가 한 세트로 바뀌어야 하는데 하나씩 따로 바꾸면, 그 사이에 다른 스레드가 "일부만 바뀐 모순된 상태"를 읽어갈 수 있다.

**규칙**: 모든 쓰기/읽기 메소드는 `with self._lock:` 블록 안에서만 변수에 접근한다. 변수를 외부에서 직접 접근(`state.protected = True` 등)하지 않는다 — 그래서 속성 이름 앞에 `_`를 붙여 "메소드를 통해서만 접근"하도록 표시했다.

## 3. 속성 (Attributes)

| 속성 | 타입 | 기본값 | 의미 |
|---|---|---|---|
| `_protected` | bool | `False` | 팜가드 보호 기능 on/off |
| `_mode` | str | `"정상"` | `"정상"` / `"공격탐지"` — 대시보드 신호등 색 결정 |
| `_attacker` | str \| None | `None` | 현재 공격자 IP |
| `_msg` | str | `"정상 동작 중입니다."` | 화면에 보여줄 한 줄 설명 |
| `_latest` | dict \| None | `None` | 가장 최근 센서값 (매번 덮어씀, 이력 아님) |
| `_events` | list[dict] | `[]` | 최근 이벤트 로그 (최신이 맨 앞) — 각 항목 `{"ts", "kind", "detail"}` |
| `_overloaded` | bool | `False` | 무방비 상태에서 실제로 센서 수집이 끊겼는지 |
| `_lock` | threading.Lock | - | 동시 접근 방지용 |

### `_overloaded`가 `_mode`와 별도로 있는 이유

`_mode`는 `AttackDetector`가 "탐지해서" 바꾸는 값인데, 보호 모드가 꺼져 있으면 탐지 로직 자체가 안 돈다. 그래서 무방비 상태에서 실제 공격이 들어와도 `_mode`는 계속 `"정상"`으로 남는다. `_overloaded`는 진단(탐지) 없이, `SensorCollector`가 "센서값이 실제로 안 들어오고 있다"는 증상만으로 판단하는 별도 신호다. 대시보드 빨간불(위험) 조건 = `not protected and overloaded`.

## 4. 메소드 (API)

### 쓰기 (상태를 변경, 리턴값 없음)

| 메소드 | 호출 주체 | 설명 |
|---|---|---|
| `toggle_protection()` | `WebServer` (토글 버튼) | `_protected`를 반대로 뒤집고, `mode`/`attacker`/`overloaded`를 초기화. 켜짐/꺼짐에 따라 `msg` 분기 |
| `markAttack(ip)` | `AttackDetector` | 공격 탐지 시 호출. `mode="공격탐지"`, `attacker=ip` 설정, `events`에 `"DETECT"` 기록 추가 |
| `markRecovery(ip)` | `Blocker` (차단 해제 시) | 복구 시 호출. `mode="정상"`, `attacker=None` 리셋, `events`에 `"RECOVER"` 기록 추가 |
| `setLatest(sample)` | `SensorCollector` | 센서값 읽을 때마다 호출. `sample`은 `{"temp", "humi", "soil", "light"}` 형태 딕셔너리 |
| `setOverloaded(value)` | `SensorCollector` | 무방비 상태에서 수집 중단/재개를 감지했을 때 `True`/`False` 전달 |

### 읽기 (상태를 조회, 변경 없음)

| 메소드 | 호출 주체 | 설명 |
|---|---|---|
| `is_protected()` | `AttackDetector` | 탐지 로직을 돌릴지 말지 판단용 |
| `snapshot()` | `WebServer` | 7개 속성 전부를 딕셔너리로 반환 — `/api/status` 응답에 그대로 사용 |

## 5. 전체 코드

```python
import threading
from datetime import datetime


class GatewayState:
    def __init__(self):
        self._lock = threading.Lock()
        self._protected = False
        self._mode = "정상"
        self._attacker = None
        self._msg = "정상 동작 중입니다."
        self._latest = None
        self._events = []
        self._overloaded = False

    def toggle_protection(self):
        with self._lock:
            self._protected = not self._protected
            self._attacker = None
            self._overloaded = False
            self._mode = "정상"
            if self._protected:
                self._msg = "정상 동작 중입니다."
            else:
                self._msg = "팜가드가 꺼져있습니다."

    def markAttack(self, ip):
        with self._lock:
            self._attacker = ip
            self._mode = "공격탐지"
            self._msg = f"{ip}에서 공격이 탐지되었습니다."
            now = datetime.now().strftime("%H:%M:%S")
            self._events = [{"ts": now, "kind": "DETECT", "detail": self._msg}] + self._events

    def markRecovery(self, ip):
        with self._lock:
            self._attacker = None
            self._mode = "정상"
            self._msg = f"{ip}로부터 받은 공격을 복구했습니다."
            now = datetime.now().strftime("%H:%M:%S")
            self._events = [{"ts": now, "kind": "RECOVER", "detail": self._msg}] + self._events

    def setLatest(self, sample):
        with self._lock:
            self._latest = sample

    def setOverloaded(self, value):
        with self._lock:
            self._overloaded = value

    def is_protected(self):
        with self._lock:
            return self._protected

    def snapshot(self):
        with self._lock:
            return {
                "protected": self._protected,
                "mode": self._mode,
                "attacker": self._attacker,
                "msg": self._msg,
                "latest": self._latest,
                "events": self._events,
                "overloaded": self._overloaded,
            }
```

## 6. 다른 클래스에서 쓰는 방법 (예시)

```python
# gateway.py (혹은 각 클래스 __init__)에서 하나만 만들어서 공유
state = GatewayState()

# SensorCollector
state.setLatest({"temp": 26.4, "humi": 62, "soil": 540, "light": 820})

# AttackDetector
if state.is_protected():
    state.markAttack("192.0.2.84")

# Blocker (차단 해제 시)
state.markRecovery("192.0.2.84")

# WebServer
status = state.snapshot()  # 그대로 JSON으로 응답
```

> 주의: `GatewayState` 객체는 **하나만 만들어서** 모든 클래스가 참조(공유)해야 한다. 클래스마다 따로 `GatewayState()`를 만들면 서로 다른 칠판을 보게 되어 상태가 공유되지 않는다.

## 7. 다음 작업

- [ ] `Storage` (DB 저장) 구현
- [ ] `SensorCollector` 구현
- [ ] `AttackDetector` 구현
- [ ] `Blocker` 구현
- [ ] `WebServer` 구현 — 완성되면 `state.py`를 import해서 위 예시처럼 연결
