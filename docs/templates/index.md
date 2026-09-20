# Templates

Each top-level key of `metaconfig.yaml` selects the template of the same name and provides its parameters. The pages of this section list, for every template, what it deploys and the meaning, type and an example value of each parameter.

| Template | Type | Rootless | Description |
|----------|:----:|:--------:|-------------|
| [core](core.md) | &ndash; | | mandatory administration login |
| [adguardhome](adguardhome.md) | Service | | DNS filter + DHCP |
| [caddy](caddy.md) | Service | ✓ | reverse proxy + automatic HTTPS |
| [convertx](convertx.md) | Service | ✓ | file converter (documents, images, audio, video, e-books) |
| [ext4_drives](ext4_drives.md) | Storage | | automatic mounting of ext4 drives |
| [forgejo](forgejo.md) | Service | ✓ | Gitea alternative |
| [homeassistant](homeassistant.md) | Service | ✓ | home automation hub, with Zigbee devices through a USB dongle (Zigbee2MQTT) |
| [homepage](homepage.md) | Service | ✓ | customizable dashboard listing the server's services and bookmarks |
| [immich](immich.md) | Service | ✓ | self-hosted photo management (Google Photos-like) |
| [jellyfin](jellyfin.md) | Service | ✓ | media server |
| [joplin](joplin.md) | Service | ✓ | note-taking backend (Google Keep-like) |
| [livesync](livesync.md) | Service | ✓ | Obsidian vault synchronization backend (CouchDB) |
| [matrix](matrix.md) | Service | ✓ | private chat server (Discord-like) with the Element web client, not federated |
| [matrix_rtc](matrix_rtc.md) | Service | ✓ | voice and video calls for the Matrix server (LiveKit SFU + Element Call backend) |
| [openwebui](openwebui.md) | Service | ✓ | web interface for LLM chat (Ollama, OpenAI-compatible APIs) |
| [overleaf](overleaf.md) | Service | ✓ | LaTeX collaborative editor |
| [prometheus](prometheus.md) | Service | ✓ | metrics collection and time series database, backing the Homepage widgets |
| [stalwart](stalwart.md) | Service | ✓ | outgoing mail relay for the other services (SMTP submission + DKIM) |
| [vaultwarden](vaultwarden.md) | Service | ✓ | password manager server compatible with the Bitwarden clients |
| [wg_easy](wg_easy.md) | Service | | WireGuard VPN server with a web interface |
| [yamtrack](yamtrack.md) | Service | ✓ | media tracker (movies, shows, anime, manga, games, books, comics) |

**Rootless** services run as a dedicated unprivileged user (`u_<template>`), with their Quadlet units under that user's home; the others need capabilities or host networking that only root can grant and are installed system-wide under `/etc/containers/systemd/`. See the [design rationale](../design-rationale/index.md) for what each kind puts on the system, and the [maintenance page](../getting-started/maintenance.md) for how to reach them.

## Conventions

- Every service that serves HTTP takes an `http_port` on which it is published on the host. Nothing is exposed to the internet by itself: publish it through a [Caddy](caddy.md) site pointing at that port.
- Images are given in full (`registry/namespace/name:tag`) and follow their tag through Podman's [automatic updates](../getting-started/automatic-updates.md), so prefer a major or major.minor tag to `latest`. Every rootless template takes an optional `auto_update` schedule, documented on that page rather than repeated below.
- Services that need to know their public address take a `hostname`, which should match their Caddy site.
- Internal credentials between the containers of one service are hard-coded in the template and never reachable from outside the pod; only the credentials you must know are parameters.

The [terminology page](../design-rationale/terminology.md) lists every shared parameter name and what it means.
