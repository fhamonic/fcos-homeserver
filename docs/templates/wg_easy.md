# `wg_easy`

Configuration for [wg-easy](https://github.com/wg-easy/wg-easy), a WireGuard VPN server with a web interface to manage clients. It gives remote access to the local network (and thus to the services that are not published through Caddy) from phones and laptops.

This template is **rootful**: the container needs the `NET_ADMIN`, `SYS_MODULE` and `NET_RAW` capabilities, IP forwarding sysctls and the `wireguard` and `nft_masq` kernel modules, which the template loads at boot. Its units are installed under `/etc/containers/systemd/` and the WireGuard configuration lives in `/var/wg_easy`.

The web interface is served over plain HTTP (`INSECURE=true`) on `http_port`, on the assumption that it is only reached from the local network or through the VPN itself. If you publish it through Caddy, restrict the site to the local network with [`directives`](caddy.md#caddysitesdirectives) as in the example `metaconfig.yaml`. The WireGuard port has to be forwarded from the internet router to the server.

The initial administrator account and the connection parameters are set from the variables below at first start; later changes must be made from the web interface.

## `wg_easy.image`

The image of wg-easy to deploy.

* **Type:** String
* **Example:** `ghcr.io/wg-easy/wg-easy:15`

## `wg_easy.http_port`

Port to listen for HTTP requests (web interface).

* **Type:** Integer
* **Example:** `3008`

## `wg_easy.wireguard_port`

UDP port of the WireGuard tunnel, published on the host and advertised to the clients.

* **Type:** Integer
* **Example:** `51821`

## `wg_easy.admin_username`

Username of the initial administrator of the web interface.

* **Type:** String
* **Example:** `admin`

## `wg_easy.admin_password`

Password of the initial administrator of the web interface.

* **Type:** String
* **Example:** `L0NgP@SsW0rD`

## `wg_easy.host`

Public hostname or IP address of the server, written into the client configurations as the tunnel endpoint.

* **Type:** Domain name or IP address
* **Example:** `vpn.mydomain.com`
