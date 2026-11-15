"""Pruebas de integración: levanta los routers como procesos, envía paquetes y muestra las salidas.

Uso (desde la raíz del repositorio):
    python3 pruebas/escenarios.py <escenario>
Escenarios: v1, v2, v2_mal, ttl1, v3, v4, default, orden, todos
"""
import os
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from red import Red, enviar, caminos, mostrar_log, RAIZ  # noqa: E402

NOMBRES = {8880 + i: f"R{i}" for i in range(7)}
NOMBRES[7000] = "Rdef"
SIN_TTL = 255  # la versión final del código siempre tiene TTL; 255 emula "sin TTL"


def red_v(version, ids, rutas=None):
    rutas = rutas or {}
    return [(f"R{i}", 8880 + i, rutas.get(i, f"rutas_R{i}_{version}.txt")) for i in ids]


def esc_v1():
    print("##### Ejemplo 1: 2 routers #####")
    with Red("v1", red_v("v1", [1, 2])) as red:
        enviar("127.0.0.1", 8882, "hola R2", SIN_TTL, 8881)
        time.sleep(0.2)
        enviar("127.0.0.1", 8881, "hola R1", SIN_TTL, 8881)
    for r in ["R1", "R2"]:
        mostrar_log(red, r)


def esc_v2():
    print("##### Ejemplo 2: 3 routers en línea #####")
    with Red("v2", red_v("v2", [1, 2, 3])) as red:
        for puerto, msg in [(8883, "hola R3"), (8882, "hola R2"), (8884, "hola"), (8881, "hola R1")]:
            enviar("127.0.0.1", puerto, msg, SIN_TTL, 8881)
            time.sleep(0.2)
    for r in ["R1", "R2", "R3"]:
        mostrar_log(red, r)


def esc_v2_mal(ttl=SIN_TTL):
    print(f"##### Ejemplo 2 con R2 mal configurado, TTL inicial = {ttl} #####")
    with Red(f"v2_mal_ttl{ttl}", red_v("v2", [1, 2, 3], {2: "rutas_R2_v2_mal.txt"})) as red:
        enviar("127.0.0.1", 8883, "hola R3", ttl, 8881)
        time.sleep(1.5)
    for r in ["R1", "R2", "R3"]:
        mostrar_log(red, r, max_lineas=8)
        print(f"  (total de líneas en {r}: {len(red.log(r))})")


def esc_ttl1():
    print("##### TTL = 1 desde R1 hacia R3 (ejemplo 2) #####")
    with Red("ttl1", red_v("v2", [1, 2, 3])) as red:
        enviar("127.0.0.1", 8883, "hola", 1, 8881)
        time.sleep(0.2)
        enviar("127.0.0.1", 8883, "hola con TTL 2", 2, 8881)
        time.sleep(0.2)
        enviar("127.0.0.1", 8883, "hola con TTL 3", 3, 8881)
    for r in ["R1", "R2", "R3"]:
        mostrar_log(red, r)


def resumen_caminos(cams, n_min, titulo):
    print(f"--- {titulo} ---")
    for msg, cam in cams.items():
        print(f"{msg:>10}: {' -> '.join(cam)}   ({len(cam) - 1} saltos)")
    saltos = Counter(len(c) - 1 for c in cams.values())
    print(f"Distribución de saltos: {dict(sorted(saltos.items()))}  | mínimo posible: {n_min}")
    prom = sum(k * v for k, v in saltos.items()) / max(1, sum(saltos.values()))
    print(f"Promedio de saltos: {prom:.2f}")


def esc_v3(n=12):
    print(f"##### 5 routers: {n} paquetes de R1 a R5 #####")
    with Red("v3", red_v("v3", [1, 2, 3, 4, 5])) as red:
        for i in range(n):
            enviar("127.0.0.1", 8885, f"paq{i:02d}", SIN_TTL, 8881)
            time.sleep(0.15)
    mostrar_log(red, "R2", max_lineas=8)
    mostrar_log(red, "R5")
    resumen_caminos(dict(sorted(caminos(red, NOMBRES).items())), 3, "Caminos R1 -> R5")


def esc_v4(n=6):
    print(f"##### 7 routers (R0..R6): intercalando {n} paquetes R1->R5 y {n} paquetes R5->R1 #####")
    with Red("v4", red_v("v4", range(7))) as red:
        for i in range(n):
            enviar("127.0.0.1", 8885, f"ida{i:02d}", SIN_TTL, 8881)
            time.sleep(0.15)
            enviar("127.0.0.1", 8881, f"vuelta{i:02d}", SIN_TTL, 8885)
            time.sleep(0.15)
    mostrar_log(red, "R2", max_lineas=14)
    cams = dict(sorted(caminos(red, NOMBRES).items()))
    resumen_caminos({k: v for k, v in cams.items() if k.startswith("ida")}, 3, "Caminos R1 -> R5")
    resumen_caminos({k: v for k, v in cams.items() if k.startswith("vuelta")}, 3, "Caminos R5 -> R1")


def esc_default():
    print("##### 5 routers + router default (127.0.0.1, 7000) #####")
    routers = red_v("v5", [1, 2, 3, 4, 5]) + [("Rdef", 7000, "rutas_default.txt")]
    with Red("default", routers) as red:
        enviar("127.0.0.1", 9000, "hacia afuera 1", 10, 8881)
        time.sleep(0.3)
        enviar("8.8.8.8", 53, "hacia afuera 2", 10, 8883)
        time.sleep(0.3)
        enviar("127.0.0.1", 8885, "dentro de la red", 10, 8881)
    for r in ["R1", "R3", "R5", "Rdef"]:
        mostrar_log(red, r)


def esc_orden(n=200):
    print(f"##### Orden de llegada: archivo de {n} líneas de R1 a R5 con prueba_router.py #####")
    archivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archivo_grande.txt")
    with open(archivo, "w") as f:
        for i in range(1, n + 1):
            f.write(f"linea {i:03d}\n")
    with Red("orden", red_v("v3", [1, 2, 3, 4, 5])) as red:
        with open(archivo) as f:
            subprocess.run([sys.executable, "prueba_router.py", "127.0.0.1;8885;10", "127.0.0.1", "8881"],
                           stdin=f, cwd=RAIZ, check=True)
        time.sleep(2)
    recibidas = [l for l in red.log("R5") if l.startswith("linea ")]
    nums = [int(l.split()[1]) for l in recibidas]
    fuera = sum(1 for a, b in zip(nums, nums[1:]) if b < a)
    descartes = sum(sum(1 for l in red.log(r) if "TTL 0" in l) for r in ["R1", "R2", "R3", "R4", "R5"])
    print(f"Líneas enviadas: {n} | recibidas en R5: {len(nums)} | descartadas por TTL: {descartes}")
    print(f"Inversiones de orden (línea menor después de una mayor): {fuera}")
    print("Primeras 30 líneas recibidas en R5:", " ".join(str(x) for x in nums[:30]))
    cams = caminos(red, NOMBRES)
    saltos = Counter(len(c) - 1 for c in cams.values())
    print(f"Distribución de saltos: {dict(sorted(saltos.items()))}")


ESC = {"v1": esc_v1, "v2": esc_v2, "v2_mal": lambda: (esc_v2_mal(SIN_TTL), print(), esc_v2_mal(10)),
       "ttl1": esc_ttl1, "v3": esc_v3, "v4": esc_v4, "default": esc_default, "orden": esc_orden}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in list(ESC) + ["todos"]:
        print(__doc__)
        sys.exit(1)
    for nombre in (ESC if sys.argv[1] == "todos" else [sys.argv[1]]):
        ESC[nombre]()
        print()
