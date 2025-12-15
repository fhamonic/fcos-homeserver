import shutil
import os
import subprocess
import sys
from dataclasses import dataclass

endpoint = "fhamonic.fr"
host_port = "51820"
network_interface = "enp2s0f1"

# ####################### Do not edit below this line #########################

if len(sys.argv) < 2:
    raise Exception("Usage: new_wgconfig <output_dir> [<num_clients>]")

output_dir = sys.argv[1]
num_clients = int(sys.argv[2]) if len(sys.argv) > 2 else 1

shutil.rmtree(output_dir, ignore_errors=True)
os.mkdir(output_dir)


@dataclass
class WGKeys:
    priv: str
    pub: str
    psk: str


def generate_wireguard_keys():
    privkey = subprocess.check_output(["wg", "genkey"]).decode().strip()
    pubkey = (
        subprocess.check_output(["wg", "pubkey"], input=privkey.encode())
        .decode()
        .strip()
    )
    psk = subprocess.check_output(["wg", "genpsk"]).decode().strip()
    return WGKeys(privkey, pubkey, psk)


server_keys = generate_wireguard_keys()
clients_keys = [generate_wireguard_keys() for _ in range(num_clients)]

# ################################## Server ###################################
server_config = (
    "[Interface]\n"
    f"Address = 10.0.0.1/24\n"
    f"ListenPort = {host_port}\n"
    f"PrivateKey = {server_keys.priv}\n"
    f"PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {network_interface} -j MASQUERADE\n"
    f"PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {network_interface} -j MASQUERADE\n"
)
for i, client_keys in enumerate(clients_keys):
    server_config += (
        "\n[Peer]\n"
        f"PublicKey = {client_keys.pub}\n"
        f"PresharedKey = {client_keys.psk}\n"
        f"AllowedIPs = 10.0.0.{i+2}/32\n"
    )

with open(f"{output_dir}/server.conf", "wt") as f:
    f.write(server_config)

# ################################## Clients ##################################
for i, client_keys in enumerate(clients_keys):
    client_config = (
        "[Interface]\n"
        f"Address = 10.0.0.{i+2}/32\n"
        f"PrivateKey = {client_keys.priv}\n"
        "\n[Peer]\n"
        f"PublicKey = {server_keys.pub}\n"
        f"PresharedKey = {client_keys.psk}\n"
        "AllowedIPs = 0.0.0.0/0\n"
        f"Endpoint = {endpoint}:{host_port}\n"
        "PersistentKeepalive = 25"
    )

    with open(f"{output_dir}/client_{i}.conf", "wt") as f:
        f.write(client_config)
