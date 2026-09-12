# `matrix_rtc`

Configuration for the voice and video backend of the [matrix](matrix.md) server: a pod with the [LiveKit](https://livekit.io) media server and the [MatrixRTC authorization service](https://github.com/element-hq/lk-jwt-service), which together are the self-hosted backend of [Element Call](https://github.com/element-hq/element-call/blob/main/docs/self_hosting.md).

Group calls do not go from browser to browser: each participant sends its audio and video once to a media server (an SFU, *selective forwarding unit*), which forwards them to the others. LiveKit is that server. Before joining, a client asks the authorization service for a LiveKit token; the service checks the client's identity with the home server (an OpenID token, verified against Synapse) and, for members of the server, creates the LiveKit room. Element then talks to LiveKit directly for the media.

The template runs both in one pod as `u_matrix_rtc`, generates the API secret they share at first boot (`matrix_rtc-init-keys.service`), and is meant to be exposed through a single [Caddy](caddy.md) site at `hostname`: the authorization service under `/livekit/jwt`, LiveKit's signaling WebSocket everywhere else, as in the example block of `metaconfig.yaml`:

```
handle_path /livekit/jwt/* {
    reverse_proxy host.containers.internal:3017
}
handle {
    reverse_proxy host.containers.internal:3016
}
```

The [matrix](matrix.md) template then needs its `rtc_hostname` set to this service's `hostname`, which announces the backend to the clients and enables the Synapse features it relies on.

## Home network

Media does not go through Caddy: WebRTC needs UDP, so LiveKit is reached on its own ports, which are the reason this is a separate template. The template is written for a server behind a home router:

* **Port forwarding.** Forward these ports on the router to the server, in addition to the 443 of Caddy. The numbers must be the same on both sides, because LiveKit tells the clients which ports to use.

    | Parameter | Protocol | Purpose |
    |-----------|:--------:|---------|
    | `webrtc_udp_port` | UDP | media |
    | `webrtc_tcp_port` | TCP | media fallback, for clients whose network blocks UDP |
    | `turn_port` | UDP | relay (TURN) for clients that cannot reach the media ports directly |

* **Public address.** LiveKit discovers the public address of the router with STUN at every start and hands it to the clients, so a residential address that changes from time to time only needs a restart of the service (or waits for the next one). It does not check that the address loops back to itself, since most home routers do not allow that.
* **No hairpin NAT.** The authorization service has to call Synapse (to verify identities and to tidy call memberships) and the LiveKit API (to create rooms). All three go through public host names, that is out to the router and back, which many home routers refuse. The pod therefore resolves the public names of Synapse and of this service to the host itself, where Caddy answers with the real certificates, and reaches the client API of Synapse directly on its `http_port`.
* **Carrier-grade NAT.** If the ISP does not give the router a public IPv4 address, no forwarded port is reachable and calls cannot work from outside the LAN. This service, alone, can then be moved to a small VPS: nothing else in the template assumes it runs on the same machine as Synapse.
* **Bandwidth.** Every stream leaves the server once per receiving participant, over the home connection's upload link. Voice is cheap (a few tens of kbit/s per stream); video is not, and Element Call lets participants turn the camera off.

!!! note
    A TURN over TLS relay on port 443 helps in the most restrictive networks (corporate firewalls that only let HTTPS through) but is not possible here: 443 belongs to Caddy. The TCP fallback on `webrtc_tcp_port` covers the common cases.

!!! note
    The Element Call application itself is loaded from Element's servers (`call.element.io`), as in Element's default configuration: only the media and authorization backend is self-hosted. Element Call as a hosted page never sees the media, which goes from the browser to LiveKit.

## `matrix_rtc.image`

The image of LiveKit to deploy.

* **Type:** String
* **Example:** `docker.io/livekit/livekit-server:v1.13`

## `matrix_rtc.auth_image`

The image of the MatrixRTC authorization service. It publishes no floating major tag, so the version is pinned.

* **Type:** String
* **Example:** `ghcr.io/element-hq/lk-jwt-service:0.7.0`

## `matrix_rtc.http_port`

Port to listen for HTTP requests to LiveKit (signaling WebSocket and API).

* **Type:** Integer
* **Example:** `3016`

## `matrix_rtc.auth_port`

Port to listen for HTTP requests to the authorization service.

* **Type:** Integer
* **Example:** `3017`

## `matrix_rtc.webrtc_udp_port`

UDP port of the media, published on the host under the same number and to be forwarded on the router.

* **Type:** Integer
* **Example:** `7882`

## `matrix_rtc.webrtc_tcp_port`

TCP port of the media fallback, published on the host under the same number and to be forwarded on the router.

* **Type:** Integer
* **Example:** `7881`

## `matrix_rtc.turn_port`

UDP port of the TURN relay, published on the host under the same number and to be forwarded on the router.

* **Type:** Integer
* **Example:** `3478`

## `matrix_rtc.hostname`

Public host name of the service, which should match its [Caddy](caddy.md) site. It is the value of `rtc_hostname` in the [matrix](matrix.md) template, the address the clients open the WebSocket to, and the name of the TURN relay.

* **Type:** Fully qualified domain name
* **Example:** `rtc.mydomain.com`

## `matrix_rtc.homeserver`

The Matrix server whose members may open calls.

### `matrix_rtc.homeserver.domain`

The server name of the home server, that is the part of its user IDs after the colon: `matrix.domain` when it is set, `matrix.hostname` otherwise.

* **Type:** DNS domain
* **Purpose:** Only OpenID tokens issued by this server name are accepted. The authorization service reads `https://<domain>/.well-known/matrix/server`, which the [matrix](matrix.md) template serves when its `rtc_hostname` is set, and verifies the tokens on `https://<domain>/_matrix/federation/v1/openid/userinfo`; when the domain differs from the Synapse host name, its Caddy site must forward both paths to Synapse, as the example block of `metaconfig.yaml` does.
* **Example:** `mydomain.com`

### `matrix_rtc.homeserver.hostname`

The `hostname` of the [matrix](matrix.md) template. Like `domain`, it is resolved to this host inside the pod, so that the authorization service never leaves the LAN to reach Synapse.

* **Type:** Fully qualified domain name
* **Example:** `matrix.mydomain.com`

### `matrix_rtc.homeserver.port`

The `http_port` of the [matrix](matrix.md) template, on which the client API of Synapse is reached from this pod as `host.containers.internal:<port>`.

* **Type:** Integer
* **Example:** `3014`
