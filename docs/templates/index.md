# Templates

Each top-level key of `metaconfig.yaml` selects the template of the same name and provides its parameters. The pages of this section list, for every template, what it deploys and the meaning, type and an example value of each parameter.

| Template | Type | Rootless | Description |
|----------|:----:|:--------:|-------------|
| [core](core.md) | &ndash; | | mandatory administration login |
| [adguardhome](adguardhome.md) | Service | | DNS filter + DHCP |
| [ext4_drives](ext4_drives.md) | Storage | | automatic mounting of ext4 drives |
| [caddy](caddy.md) | Service | ✓ | reverse proxy + automatic HTTPS |
| [jellyfin](jellyfin.md) | Service | ✓ | media server |
| [overleaf](overleaf.md) | Service | ✓ | LaTeX collaborative editor |
| [forgejo](forgejo.md) | Service | ✓ | Gitea alternative |
| [immich](immich.md) | Service | ✓ | self-hosted photo management (Google Photos-like) |
| [joplin](joplin.md) | Service | ✓ | note-taking backend (Google Keep-like) |
| [wg_easy](wg_easy.md) | Service | | WireGuard VPN server with a web interface |
| [openwebui](openwebui.md) | Service | ✓ | web interface for LLM chat (Ollama, OpenAI-compatible APIs) |
| [livesync](livesync.md) | Service | ✓ | Obsidian vault synchronization backend (CouchDB) |
| [homepage](homepage.md) | Service | ✓ | customizable dashboard listing the server's services and bookmarks |
| [stalwart](stalwart.md) | Service | ✓ | outgoing mail relay for the other services (SMTP submission + DKIM) |
| [prometheus](prometheus.md) | Service | ✓ | metrics collection and time series database, backing the Homepage widgets |

**Rootless** services run as a dedicated unprivileged user (`u_<template>`), with their Quadlet units under that user's home; the others need capabilities or host networking that only root can grant and are installed system-wide under `/etc/containers/systemd/`. See the [design rationale](../design-rationale.md) for what each kind puts on the system, and the [maintenance page](../getting-started/maintenance.md) for how to reach them.

## Conventions

- Every service that serves HTTP takes an `http_port` on which it is published on the host. Nothing is exposed to the internet by itself: publish it through a [Caddy](caddy.md) HTTPS redirection pointing at that port.
- Images are given in full (`registry/namespace/name:tag`) and follow their tag through Podman's automatic updates, so prefer a major or major.minor tag to `latest`.
- Services that need to know their public address take a `self_url`, which should match the Caddy route.
- Internal credentials between the containers of one service are hard-coded in the template and never reachable from outside the pod; only the credentials you must know are parameters.
