class Header:
    def __init__(self, ip: bytes, puerto: int, msg: bytes, ttl: int):
        ip_split = ip.split(b".")
        if len(ip_split) != 4:
            print("Formato de IP incorrecto")
            return
        ip_num = 0
        for i in range(4):
            try:
                val = int(ip_split[i].decode())
            except Exception:
                print("Formato de IP incorrecto")
                return
            ip_num |= (val << (8*(3-i)))
        self.ip = ip_num.to_bytes(4)
        # solo nos quedamos con los ultimos 2 bytes
        self.puerto = puerto.to_bytes(2)
        self.msg = msg
        self.ttl = ttl.to_bytes(1)
    def to_packet(self) -> bytes:
        return self.ip + self.puerto + self.ttl + self.msg
    def __str__(self):
        s = ""
        ip_num = int.from_bytes(self.ip)
        for i in range(4):
            s = s + str((ip_num >> (8*(3-i))) & 0xFF) + "."
        s = s[:-1]
        puerto_str = str(int.from_bytes(self.puerto))
        ttl_str = str(int.from_bytes(self.ttl))
        return f"{s};{puerto_str};{ttl_str};{self.msg.decode(errors='replace')}"
