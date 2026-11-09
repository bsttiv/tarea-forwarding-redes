import sys
import socket
import header

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("prueba_router.py recibe 3 argumentos: headers IP_router_inicial puerto_router_inicial")
        print('Ejemplo: python3 prueba_router.py "127.0.0.1;8885;10" 127.0.0.1 8881 < archivo.txt')
        sys.exit(1)

    # headers tiene el formato ip_destino;puerto_destino;ttl
    headers = args[1].split(";")
    if len(headers) != 3:
        print("Los headers deben tener el formato ip_destino;puerto_destino;ttl")
        sys.exit(1)
    ip_destino, puerto_destino, ttl = headers
    ip_router_inicial = args[2]
    puerto_router_inicial = int(args[3])

    # Se lee el archivo desde la entrada estandar, una linea por paquete
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for linea in sys.stdin:
        linea = linea.rstrip("\n")
        paquete = header.Header(ip_destino.encode(), puerto_destino.encode(), linea.encode(), ttl.encode())
        s.sendto(paquete.to_packet(), (ip_router_inicial, puerto_router_inicial))
    s.close()
