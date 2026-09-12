# `jellyfin`

Initial configuration for the [Jellyfin](https://jellyfin.org/) media server.

## `jellyfin.image`

The image of Jellyfin to deploy.

* **Type:** String
* **Example:** `docker.io/jellyfin/jellyfin:10`

## `jellyfin.http_port`

Port to listen for HTTP requests.
TCP connections are forwarded to the UNIX socket created by Jellyfin **inside the container** (and bind mounted to the host) using a systemd service running `socat`.
This typically doubles the throughput compared to standard container port binding.

* **Type:** Integer
* **Example:** `3002`

## `jellyfin.media_volumes`

List of bind mounts for media libraries.

* **Type:** List of volume mappings
* **Purpose:** Provides read-only access to host media directories.
* **Format:** `host_path:container_path:options`
* **Example:** `/var/hdd/Movies:/media/Movies:ro,Z`

## `jellyfin.self_url`

Public URL advertised by Jellyfin to clients.

* **Type:** Domain name
* **Example:** `jellyfin.mydomain.com`
