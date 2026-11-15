"""Utilidades para levantar una red de routers y analizar sus salidas.

Cada router se ejecuta como un proceso independiente (python3 -u router.py ...)
y su salida estándar se guarda en logs/<nombre>.log.
"""
import os
import re
import socket
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
import header  # noqa: E402

LOGS = os.path.join(AQUI, "logs")
RE_FWD = re.compile(
    r"Redirigiendo paquete (\S+?);(\d+);(\d+);(.*) con destino final \S+ desde (\S+):(\d+) hacia \('(\S+)', (\d+)\)"
)


class Red:
    def __init__(self, nombre, routers):
        """routers: lista de (nombre_router, puerto, archivo_rutas)."""
        self.nombre = nombre
        self.routers = routers
        self.procs = []
        self.archivos = {}
        os.makedirs(LOGS, exist_ok=True)

    def __enter__(self):
        for nom, puerto, rutas in self.routers:
            ruta_log = os.path.join(LOGS, f"{self.nombre}_{nom}.log")
            f = open(ruta_log, "w")
            p = subprocess.Popen(
                [sys.executable, "-u", "router.py", "127.0.0.1", str(puerto), os.path.join("rutas", rutas)],
                cwd=RAIZ, stdout=f, stderr=subprocess.STDOUT,
            )
            self.procs.append(p)
            self.archivos[nom] = ruta_log
        time.sleep(0.5)
        return self

    def __exit__(self, *a):
        time.sleep(0.5)
        for p in self.procs:
            p.terminate()
        for p in self.procs:
            p.wait()

    def log(self, nom):
        with open(self.archivos[nom]) as f:
            return f.read().splitlines()


def enviar(ip_dest, puerto_dest, msg, ttl, puerto_envio, ip_envio="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pkt = header.Header(ip_dest.encode(), puerto_dest, msg.encode(), ttl).to_packet()
    s.sendto(pkt, (ip_envio, puerto_envio))
    s.close()


def caminos(red, nombres_por_puerto):
    """Reconstruye el camino de cada mensaje a partir de los 'Redirigiendo...'.

    Como el TTL baja en 1 por salto, ordenar por TTL descendente da el orden de los saltos.
    Retorna {mensaje: [R_origen, R_siguiente, ...]}.
    """
    saltos = {}
    for nom in red.archivos:
        for linea in red.log(nom):
            m = RE_FWD.search(linea)
            if not m:
                continue
            ttl, msg = int(m.group(3)), m.group(4)
            desde, hacia = int(m.group(6)), int(m.group(8))
            saltos.setdefault(msg, []).append((-ttl, desde, hacia))
    res = {}
    for msg, lst in saltos.items():
        lst.sort()
        camino = [nombres_por_puerto.get(lst[0][1], str(lst[0][1]))]
        for _, _, hacia in lst:
            camino.append(nombres_por_puerto.get(hacia, str(hacia)))
        res[msg] = camino
    return res


def mostrar_log(red, nom, max_lineas=None):
    lineas = red.log(nom)
    if max_lineas is not None and len(lineas) > max_lineas:
        lineas = lineas[:max_lineas] + [f"... ({len(red.log(nom)) - max_lineas} líneas más)"]
    print(f"--- salida de {nom} ---")
    for l in lineas:
        print(l)
