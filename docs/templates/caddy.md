# `caddy`

Configuration for the [Caddy](https://caddyserver.com/) reverse proxy, the single entry point of the server: every other service is published through one of its sites, with a certificate obtained automatically.

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

## `caddy.lan_subnets`

The address ranges of the local network, in CIDR notation, from which [private sites](#caddyprivate_sites) answer and [protected sites](#caddyprotected_sites) answer without a login. Caddy matches them against the address of the client connection itself, which a client cannot fake with a header: the sockets are opened by systemd on the host, so Caddy sees the real client address. Caddy's `private_ranges` shortcut is accepted as an item and stands for every private IPv4 and IPv6 range plus the loopback.

!!! note
    A client that reaches the server over IPv6 comes from its global address, which a list of IPv4 subnets does not match: it gets a 403 even at home. Either keep the host names of private sites IPv4-only on your DNS, or add the IPv6 prefix of the LAN when your provider gives a stable one.

* **Optional**, required as soon as there are private or protected sites
* **Type:** List of CIDR ranges
* **Example:** `[192.168.0.0/24]`

## `caddy.authelia`

The [Authelia](authelia.md) service that checks the logins of [protected sites](#caddyprotected_sites).

* **Optional**, required as soon as there are protected sites

### `caddy.authelia.port`

The `http_port` of the Authelia service. Caddy reaches it on the host through `host.containers.internal`.

* **Type:** Integer
* **Example:** `3023`

## `caddy.public_sites`

List of sites served over HTTPS to any client, one per host name. A site is either a reverse proxy to a service of the server, a redirect to another address, or a block of Caddy directives written by hand.
Caddy automatically requests a certificate from Let's Encrypt for each host name, for private sites too.

!!! note
    If you reprovision your system multiple times, consider commenting out the sites. Excessive certificate requests may cause Let's Encrypt to temporarily block your IP.

Exactly one of `port`, `redirect_to` or `directives` must be set per site.

* **Optional**
* **Type:** List

### `caddy.public_sites[].hostname`

Host name of the site, which must resolve to the server.

* **Type:** Fully qualified domain name
* **Example:** `jellyfin.mydomain.com`

### `caddy.public_sites[].port`

The `http_port` of the service to proxy the site to. Caddy reaches it on the host through `host.containers.internal`. For a service on another machine, give `directives` with `reverse_proxy <address>:<port>` instead.

* **Type:** Integer
* **Example:** `3002`

### `caddy.public_sites[].redirect_to`

Target of a permanent HTTP redirect for the site, instead of a reverse proxy. Caddy placeholders such as `{uri}` are allowed.

* **Type:** String
* **Example:** `https://home.mydomain.com{uri}`

### `caddy.public_sites[].directives`

Caddy directives inserted verbatim into the site block, for anything `port` and `redirect_to` cannot express. Remember that Caddy [orders directives itself](https://caddyserver.com/docs/caddyfile/directives#directive-order) (`redir` and `handle` run before `respond`, which runs before `reverse_proxy`), so a `respond` meant to stop some requests must be scoped with a matcher and must not sit next to `handle` blocks. To keep a whole site on the LAN, make it a private site instead.

* **Type:** Multi-line string
* **Example:** keep one path on the LAN

    ```yaml
    - hostname: vault.mydomain.com
      directives: |
        @admin_outside {
            path /admin*
            not remote_ip 192.168.0.0/24
        }
        respond @admin_outside 403
        reverse_proxy host.containers.internal:3019
    ```

## `caddy.private_sites`

List of sites served over HTTPS to the clients of [`lan_subnets`](#caddylan_subnets) only; every other client gets a `403 Forbidden`. Use it for web interfaces without authentication, or not meant to be exposed to the internet. The entries take the same keys as those of [`public_sites`](#caddypublic_sites).

The restriction applies to whatever the site does, `directives` included: the template nests the body of the site in a `handle` block reserved to the LAN, so directives that are only valid at the top of a site block (`tls`, `log`, `bind`) cannot be used in a private site.

!!! note
    Private sites still get a Let's Encrypt certificate, so their host names must resolve publicly to the server, and they appear in the public [certificate transparency](https://certificate.transparency.dev/) logs. The restriction decides who gets an answer, not who knows the site exists.

* **Optional**
* **Type:** List
* **Example:**

    ```yaml
    private_sites:
      - hostname: prometheus.mydomain.com
        port: 3013
    ```

## `caddy.protected_sites`

List of sites served over HTTPS to the clients of [`lan_subnets`](#caddylan_subnets) as they are, and to every other client after a login on the [Authelia](authelia.md) portal. Use it for web interfaces without authentication of their own that must be reachable from outside. The entries take the same keys as those of [`public_sites`](#caddypublic_sites).

Caddy checks each request from outside with Authelia before running the body of the site: a browser without a session is redirected to the portal and brought back once logged in, and the application then receives the `Remote-User`, `Remote-Email`, `Remote-Name` and `Remote-Groups` headers of the user. Those headers are first removed from every request, so that no client can set them itself; LAN clients reach the application without them. As for private sites, the body is nested in a `handle` block, so `tls`, `log` and `bind` cannot be used in `directives`.

!!! warning
    Only browsers can log in. Mobile and desktop apps, sync clients and scripts get a `401 Unauthorized` from outside the LAN, so a service with accounts and apps of its own belongs in `public_sites`.

!!! note "Trusting the LAN"
    A client counts as local by the address of its connection, which Caddy receives from the systemd socket: headers such as `X-Forwarded-For` cannot change it, and a forged address cannot complete a TCP connection. The login is skipped, though, for anything able to send requests from the LAN:

    - **The router.** Some routers rewrite the source address of forwarded connections to their own LAN address, and every client from the internet then counts as local. Check once, from a phone on mobile data, that a protected site asks for the login. For the same reason, never list the address range of a tunnel or relay in `lan_subnets`.
    - **Browsers on the LAN.** A malicious page opened on a LAN machine can send requests to a protected site (host names are public in the certificate logs) and open WebSocket connections to it, without a login. From a machine outside the LAN the same page gets nowhere: the browser leaves the session cookie (`SameSite=Lax`) out of the requests that other sites send in the background.
    - **Services and devices of the LAN** that fetch addresses for someone else, such as link previews or webhooks.

    The same holds for private sites, and for the ports of the services themselves, which every template publishes on all interfaces: the LAN reaches them without Caddy.

* **Optional**
* **Type:** List
* **Example:**

    ```yaml
    protected_sites:
      - hostname: zigbee.mydomain.com
        port: 3021
    ```
