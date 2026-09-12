# `matrix`

Configuration for a private [Matrix](https://matrix.org) chat server, deployed as a pod with the [Synapse](https://element-hq.github.io/synapse/latest/) homeserver, its PostgreSQL database and the [Element](https://element.io) web client.

The target is a replacement for a Discord server among a closed group of people: text rooms organized in spaces, direct messages, file and image sharing, end-to-end encryption, and the Element apps on every platform.
Synapse and Element are the reference implementations of the protocol, maintained by the same company that runs the largest public deployment, which is what makes them the safe long-term choice.

The server is **not federated**: it exchanges nothing with other Matrix servers, and its rooms and accounts are only reachable through it.
The template achieves this by not serving the server-server API at all (only the client-server API is enabled on the listener) and by refusing federation with every domain in the Synapse configuration, which is the setup Synapse documents for a private server.
Not federating also keeps the resource usage small: a federated homeserver spends most of its memory and CPU on remote rooms.

Accounts are created by invitation: registration is open but requires a **registration token**, which an administrator issues, so nobody can create an account without one.
The first administrator account is created at first boot by `matrix-init-admin.service` from `admin_username` and `admin_password`.

Two host names are involved, each with its own [Caddy](caddy.md) site:

* `hostname`, where Synapse's client API is published on `http_port` (the "homeserver URL" of the Matrix clients);
* `element_hostname`, where the Element web client is published on `element_port`: this is the address members open in a browser. Element must not be served from the same host name as the API, as its own documentation warns, since a page served by the homeserver could otherwise read the client's session.

User IDs have the form `@name:<domain>`, with `domain` defaulting to `hostname`. Since a user ID can never change once accounts exist, decide on `domain` before the first start (see the parameter below).

## Inviting members

A registration token is created through the Synapse admin API, authenticated as the administrator. From any machine, replacing the host name, user and password:

```bash
TOKEN=$(curl -s -X POST https://matrix.mydomain.com/_matrix/client/v3/login \
  -d '{"type":"m.login.password","user":"admin","password":"L0NgP@SsW0rD"}' | sed 's/.*"access_token":"\([^"]*\)".*/\1/')
curl -s -X POST https://matrix.mydomain.com/_synapse/admin/v1/registration_tokens/new \
  -H "Authorization: Bearer $TOKEN" -d '{"uses_allowed": 10}'
```

The answer contains the token to hand to the new members, who open `https://chat.mydomain.com`, choose *Create account* and enter it when asked.
`uses_allowed` caps the number of accounts the token can create (omit it for unlimited); `expiry_time` (a timestamp in milliseconds) makes it expire.
The [registration tokens API](https://element-hq.github.io/synapse/latest/usage/administration/admin_api/registration_tokens.html) also lists and deletes tokens, and the rest of the [admin API](https://element-hq.github.io/synapse/latest/usage/administration/admin_api/) manages users and rooms (deactivate an account, reset a password, make another user an administrator...).

An administrator can also create an account directly, with a password of their choosing, as the service user (see the [maintenance page](../getting-started/maintenance.md)):

```bash
podman exec -it matrix-synapse register_new_matrix_user -c /config/homeserver.yaml http://localhost:8008
```

## Voice and video

Calls are not part of this template: they need a media server, deployed by the [matrix_rtc](matrix_rtc.md) template. Setting `rtc_hostname` to the host name of that service switches on the corresponding options here (see the parameter below). Without it, Element only offers legacy one-to-one calls, which connect the two browsers directly and only work when they can reach each other, typically on the same LAN or through the VPN.

!!! note
    Element enables end-to-end encryption on the private rooms it creates. Encrypted history is only readable on devices that were in the room, or that received the keys from another device of the same account through *Secure Backup*, which each member should set up from their settings; a member who logs in from a new device without it does not see the past of encrypted rooms. Rooms created as *Public* are not encrypted.

## `matrix.image`

The image of Synapse to deploy. Synapse publishes no floating major tag, so the version is pinned: bump it to follow the releases.

* **Type:** String
* **Example:** `ghcr.io/element-hq/synapse:v1.160.0`

## `matrix.element_image`

The image of the Element web client. Like Synapse, Element publishes no floating major tag.

* **Type:** String
* **Example:** `docker.io/vectorim/element-web:v1.12.27`

## `matrix.postgres_image`

The image of PostgreSQL used by Synapse. The database is created with the `C` collation Synapse requires.

* **Type:** String
* **Example:** `docker.io/postgres:17`

## `matrix.http_port`

Port to listen for HTTP requests to the Synapse client API.

* **Type:** Integer
* **Example:** `3014`

## `matrix.element_port`

Port to listen for HTTP requests to the Element web client.

* **Type:** Integer
* **Example:** `3015`

## `matrix.hostname`

Public host name of Synapse, the homeserver URL of the clients (`https://<hostname>`). It should match its [Caddy](caddy.md) site.

* **Type:** Fully qualified domain name
* **Example:** `matrix.mydomain.com`

## `matrix.element_hostname`

Public host name of the Element web client, which should match its [Caddy](caddy.md) site. It must differ from `hostname`.

* **Type:** Fully qualified domain name
* **Example:** `chat.mydomain.com`

## `matrix.domain`

* **Optional**

The part of the user IDs after the colon (`@name:mydomain.com`), called the server name by Matrix. When it is left out, `hostname` is used and the IDs read `@name:matrix.mydomain.com`.

Clients that are given a server name look up the homeserver URL at `https://<domain>/.well-known/matrix/client`, a document Synapse serves on `http_port`. When `domain` is set, the Caddy site of that domain must therefore forward this path to Synapse, as in the example block of `metaconfig.yaml`. With calls enabled (`rtc_hostname`), the same site must also forward the OpenID endpoint, which the call service reaches at `https://<domain>` after reading `.well-known/matrix/server` there:

    ```
    @matrix path /.well-known/matrix/* /_matrix/federation/v1/openid/*
    handle @matrix {
        reverse_proxy host.containers.internal:3014
    }
    ```

Element itself is configured with the homeserver URL and does not need the lookup.

* **Type:** DNS domain
* **Purpose:** Fixed for the lifetime of the server; Synapse refuses to start with a different value once the database exists.
* **Example:** `mydomain.com`

## `matrix.rtc_hostname`

* **Optional**

Public host name of the [matrix_rtc](matrix_rtc.md) service (its `hostname`). When set:

* Synapse announces the call backend to the clients (`https://<rtc_hostname>/livekit/jwt`, both on the MatrixRTC transports endpoint and in `.well-known/matrix/client`), enables the experimental features Element Call relies on (MSC4143, MSC4222, delayed events), raises the rate limits that call signaling needs, and serves the OpenID endpoint with which the authorization service verifies identities, plus the `.well-known/matrix/server` document that leads to it (pointing at the server name on port 443, where nothing else of the federation API exists; see `domain` for the Caddy side);
* Element routes every call, direct messages included, through Element Call, so nothing depends on the legacy peer-to-peer calls.

* **Type:** Fully qualified domain name
* **Example:** `rtc.mydomain.com`

## `matrix.admin_username`

Local part of the ID of the first administrator account, created at first boot.

* **Type:** String
* **Example:** `admin`

## `matrix.admin_password`

Password of the first administrator account.

* **Type:** String
* **Example:** `L0NgP@SsW0rD`
