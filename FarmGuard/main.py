import threading

from GatewayState import GatewayState
from Storage import Storage
from Blocker import Blocker
from AttackDetector import AttackDetector
from SensorCollector import SensorCollector
from WebServer import WebServer


def main():
    state = GatewayState()
    storage = Storage()
    blocker = Blocker(state, storage)
    detector = AttackDetector(state, blocker, storage)
    collector = SensorCollector(state, storage, test_mode=False)
    webserver = WebServer(state, storage)

    threading.Thread(target=collector.run, daemon=True).start()
    threading.Thread(target=blocker.run, daemon=True).start()
    threading.Thread(target=detector.run, daemon=True).start()

    webserver.serve()  # 메인 스레드는 여기서 멈춰서 계속 웹 요청을 받음


if __name__ == "__main__":
    main()