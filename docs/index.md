---
# The H1 below is the hero wordmark; without this the tab reads
# "Fedora CoreOS Homeserver - Fedora CoreOS Homeserver".
# An empty title makes the template fall through to the bare site_name.
title: ""
---

<div class="fcos-hero" markdown>

![fcos-homeserver logo](assets/logo.svg)

# Fedora CoreOS Homeserver

**A set-and-forget home server, provisioned at first boot from a single YAML file.**

[Get started](getting-started/index.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/fhamonic/fcos-homeserver){ .md-button }

---

</div>

This project explores a pragmatic way to use Fedora CoreOS (FCOS) as a "set-and-forget" home server by lowering the barrier to its initial provisioning, while staying aligned with FCOS design principles.

It consists of:

- A set of **Jinja2 templates** describing self-contained services (storage, reverse proxy, applications).
- A single `metaconfig.yaml` that declaratively selects and parametrizes those templates.
- A `build_config.py` script that renders and merges the templates into a valid Butane configuration, which is then consumed by the standard FCOS installation workflow.

```yaml title="metaconfig.yaml (excerpt)"
core:
  ssh_authorized_keys:
    - <MY PUBLIC SSH KEY>

caddy:
  image: docker.io/library/caddy:2.10
  http_port: 80
  https_port: 443
  https_redirections:
    - route: jellyfin.mydomain.com
      internal_port: 3002

jellyfin:
  image: docker.io/jellyfin/jellyfin:10
  http_port: 3002
  media_volumes:
    - /var/hdd/Movies:/media/Movies:ro,Z
  self_url: jellyfin.mydomain.com
```

Each top-level key selects one [template](templates/index.md); the values under it are the only decisions the template leaves to you.

## Why Fedora CoreOS?

Fedora CoreOS is primarily known as a building block for enterprise container platforms. That background is precisely what makes it attractive for a long-lived home server:

- **Immutable OS**
    - The base system is read-only and versioned.
    - Configuration drift and vulnerabilities are minimized.
- **Reproducibility**
    - All configuration is done at first boot using a configuration file.
    - Manual configuration through SSH should be exceptional.
- **Optimized for containers**
    - The OS provides a minimal, container-focused userland.
    - Podman is the default container runtime, rootless mode is well supported.
    - systemd Quadlet is a first-class mechanism for managing containers as services.
- **Automatic, transactional updates**
    - OS updates are applied atomically and rolled back automatically on failure.
    - No manual maintenance is expected.

The main barrier to entry therefore remains the initial configuration, which is the purpose of this project.

## Where to start

- [**Installation**](getting-started/index.md) — edit `metaconfig.yaml`, build the Butane configuration and install Fedora CoreOS with it.
- [**Maintenance**](getting-started/maintenance.md) — SSH access, the per-service users, reading logs and tweaking a running service.
- [**Debugging services**](getting-started/debugging.md) — the commands for a service that does not come up: journal, Quadlet generator, health checks, volumes.
- [**Templates**](templates/index.md) — every available service and the parameters it takes.
- [**Design rationale**](design-rationale.md) — how the generated configuration maps to Fedora CoreOS, Ignition, systemd and Podman. Recommended reading before adapting the project to your own setup.
- [**Adding a template**](contributing/adding-a-template.md) — writing a new service template, trying it on a running server with the ad hoc script, and documenting it.

## What is in the box

| | |
| --- | --- |
| **Administration** | [core](templates/core.md) (SSH keys), [ext4_drives](templates/ext4_drives.md) (automatic mounting of data drives) |
| **Network** | [caddy](templates/caddy.md) (reverse proxy, automatic HTTPS), [adguardhome](templates/adguardhome.md) (DNS filter, DHCP), [wg_easy](templates/wg_easy.md) (WireGuard VPN) |
| **Applications** | [jellyfin](templates/jellyfin.md), [immich](templates/immich.md), [forgejo](templates/forgejo.md), [overleaf](templates/overleaf.md), [joplin](templates/joplin.md), [livesync](templates/livesync.md), [openwebui](templates/openwebui.md) |
| **Dashboard and plumbing** | [homepage](templates/homepage.md), [prometheus](templates/prometheus.md), [stalwart](templates/stalwart.md) (outgoing mail relay) |

## License

Licensed under the [MIT License](https://github.com/fhamonic/fcos-homeserver/blob/main/LICENSE).
