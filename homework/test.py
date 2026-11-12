from scapy.all import *

target_ip = '8.8.8.8'
packet = IP(dst=target_ip)/ICMP()
response = sr1(packet)
response.show()