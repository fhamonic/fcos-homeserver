# `caddy`

Configuration for the [Caddy](https://caddyserver.com/) reverse proxy, the single entry point of the server: every other service is published through one of its routes, with a certificate obtained automatically.

Caddy runs rootless but listens on the privileged ports 80 and 443 thanks to two mechanisms: the host lowers `net.ipv4.ip_unprivileged_port_start` to 80, and the sockets are opened by systemd (`caddy.socket`) and passed to the container, which also lets the unit start on the first connection.

## `caddy.image`

The image of the Caddy server to deploy.

* **Type:** String
* **Example:** `docker.io/library/caddy:2.10`

## `caddy.http_port`

Port to listen for HTTP requests.
TCP connections are forwarded to Caddy via a UNIX socket for improved performance. Every HTTP request is permanently redirected to HTTPS.

* **Type:** Integer
* **Example:** `80`

## `caddy.https_port`

Port to listen for HTTPS requests.
TCP (and UDP for QUIC/HTTP-3) connections are forwarded to Caddy via UNIX sockets.

* **Type:** Integer
* **Example:** `443`

## `caddy.https_redirections`

List of HTTPS virtual hosts and their corresponding internal services.
By default, Caddy will automatically request an SSL certificate from Let's Encrypt for each configured route.

!!! note
    If you reprovision your system multiple times, consider commenting out the HTTPS redirections. Excessive certificate requests may cause Let's Encrypt to temporarily block your IP.

Exactly one of `internal_port`, `redirect_to` or `custom` must be set per route.

### `caddy.https_redirections[].route`

Public domain name handled by Caddy.

* **Type:** Fully qualified domain name
* **Example:** `jellyfin.mydomain.com`

### `caddy.https_redirections[].internal_port`

Internal HTTP port where the backend service is exposed. Caddy reaches it on the host through `host.containers.internal`.

* **Type:** Integer
* **Example:** `3002`

### `caddy.https_redirections[].redirect_to`

Target of a permanent HTTP redirect for the route, instead of a reverse proxy. Caddy placeholders such as `{uri}` are allowed.

* **Type:** String
* **Example:** `https://home.mydomain.com{uri}`

### `caddy.https_redirections[].custom`

Caddy directives inserted verbatim into the route's site block, for anything `internal_port` and `redirect_to` cannot express. Remember that Caddy orders directives itself (`respond` runs before `reverse_proxy`), so scope `respond` with a matcher.

* **Type:** Multi-line string
* **Example:** restrict a route to the local network

    ```yaml
    - route: prometheus.mydomain.com
      custom: |
        @public not remote_ip 192.168.0.0/24
        respond @public 403
        reverse_proxy host.containers.internal:3013
    ```
