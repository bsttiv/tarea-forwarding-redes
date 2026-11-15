"""Tests unitarios: parse_packet/create_packet y check_routes (incluye round-robin).

Uso (desde la raíz del repositorio):  python3 pruebas/test_unitarios.py
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
from router import parse_packet, create_packet, Router  # noqa: E402


def R(archivo):
    return os.path.join("rutas", archivo)


print("== Test parse_packet / create_packet (con TTL) ==")
# IP 127.0.0.1, puerto 8883 (0x22B3), TTL 10, mensaje "hola"
IP_packet_v1 = bytes([127, 0, 0, 1]) + (8883).to_bytes(2, "big") + bytes([10]) + b"hola"
parsed_IP_packet = parse_packet(IP_packet_v1)
IP_packet_v2 = create_packet(parsed_IP_packet)
print("IP_packet_v1 =", IP_packet_v1)
print("parse_packet ->", parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
for ip, puerto, ttl, msg in [("10.20.30.40", 65535, 255, "x" * 20), ("0.0.0.0", 0, 1, ""), ("192.168.1.254", 7000, 64, "ñandú")]:
    v1 = bytes(int(x) for x in ip.split(".")) + puerto.to_bytes(2, "big") + bytes([ttl]) + msg.encode()
    print(f"  {ip};{puerto};{ttl}: v1 == v2 ? {create_packet(parse_packet(v1)) == v1}")
print("Paquete de 5 bytes (header incompleto) ->", parse_packet(b"\x7f\x00\x00\x01\x22"))

print("\n== Test check_routes (ejemplo 2, router R1) ==")
r1 = Router("127.0.0.1", 8881, R("rutas_R1_v2.txt"))
for dest in [("127.0.0.1", 8882), ("127.0.0.1", 8883), ("127.0.0.1", 8884), ("10.0.0.1", 8882)]:
    print(f"  R1 check_routes(destino={dest}) -> {r1.check_routes(R('rutas_R1_v2.txt'), dest)}")

print("\n== Test check_routes (ejemplo 2, router R2) ==")
r2 = Router("127.0.0.1", 8882, R("rutas_R2_v2.txt"))
for dest in [("127.0.0.1", 8881), ("127.0.0.1", 8883), ("127.0.0.1", 8884)]:
    print(f"  R2 check_routes(destino={dest}) -> {r2.check_routes(R('rutas_R2_v2.txt'), dest)}")

print("\n== Test round-robin (5 routers, R2, destino R5) ==")
r2 = Router("127.0.0.1", 8882, R("rutas_R2_v3.txt"))
print("  ", [r2.check_routes(R("rutas_R2_v3.txt"), ("127.0.0.1", 8885))[1] for _ in range(6)])

print("\n== Test round-robin por área (R3 de 5 routers) ==")
r3 = Router("127.0.0.1", 8883, R("rutas_R3_v3.txt"))
seq = []
for dest in [8881, 8885, 8881, 8885, 8882, 8884, 8881, 8885]:
    seq.append(f"{dest}->{r3.check_routes(R('rutas_R3_v3.txt'), ('127.0.0.1', dest))[1]}")
print("  ", seq)

print("\n== Test round-robin por área (R2 de 7 routers, 3 rutas hacia 8883-8886) ==")
r2 = Router("127.0.0.1", 8882, R("rutas_R2_v4.txt"))
seq = []
for dest in [8885, 8881, 8885, 8881, 8885, 8880, 8885, 8881]:
    seq.append(f"{dest}->{r2.check_routes(R('rutas_R2_v4.txt'), ('127.0.0.1', dest))[1]}")
print("  ", seq)

print("\n== Test ruta default (R2 con router default) ==")
r2 = Router("127.0.0.1", 8882, R("rutas_R2_v5.txt"))
for dest in [("127.0.0.1", 8881), ("127.0.0.1", 9000), ("8.8.8.8", 53)]:
    print(f"  R2 check_routes(destino={dest}) -> {r2.check_routes(R('rutas_R2_v5.txt'), dest)}")
