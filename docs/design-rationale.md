# Design rationale

This repository provides a reproducible, provisioning-time approach to building a FCOS home server.
It is intentionally opinionated and closely follows FCOS design principles rather than abstracting them away:

- Declarative, first-boot configuration via Ignition
- Rootless containers managed with systemd and Podman Quadlet
- Minimal post-installation interaction

As a consequence, this repository is not intended to be a general-purpose configuration management system or a dynamic service orchestration framework. Before adapting it to your own setup, this page explains how the generated configuration maps to Fedora CoreOS, Ignition, systemd and Podman.

## Template architecture

### Composability

A template is a Jinja2 file, `templates/<key>.yaml.j2`, that renders to a complete [Butane](https://coreos.github.io/butane/) configuration for one service. It receives exactly two things: the block of `metaconfig.yaml` under its key, and `id`, the position of that key in the file.

`build_config.py` renders one template per key and merges the results into a single Butane document with a recursive merge: dictionaries are merged key by key, lists (users, directories, files, systemd units...) are concatenated, and two templates that set the same scalar to different values are a build error. Templates therefore never reference one another; they only agree on conventions:

- Each rootless template creates its own user `u_<key>` and group `g_<key>` with uid and gid `1000 + id`, so the numbering is stable across builds and has no collisions as long as keys are not reordered.
- Services reach each other exclusively through the host: a service publishes its `http_port` on the host, and Caddy, Homepage or Prometheus address it as `host.containers.internal:<port>`. Nothing depends on a shared network.
- Rendering uses Jinja's strict mode: a parameter referenced by the template but missing from `metaconfig.yaml` stops the build with the file and line number. Optional parameters are guarded in the template with `{% if key.x is defined %}`.

Removing a key from `metaconfig.yaml` removes the whole service from the generated configuration, and adding a service is adding a file under `templates/`.

### Rootless by default

Every template that can run unprivileged does, as a distinct user:

- The user's `.config/containers/systemd/` directory holds the Quadlet files, and `.config/systemd/user/default.target.wants/` the symlink that enables the generated service. Ignition also creates `.config/systemd` itself, because a parent directory created by Ignition would belong to root and break the user's `systemctl --user`.
- A file in `/var/lib/systemd/linger/` makes systemd start the user's session at boot, without any login.
- Containers use user namespaces (`UserNS=keep-id` or `UserNS=auto`): root inside a container is an unprivileged uid on the host, and bind mounts get the `:Z` SELinux label so that the container may use them.

The exceptions are [adguardhome](templates/adguardhome.md) and [wg_easy](templates/wg_easy.md), which need kernel capabilities (`NET_ADMIN`, `SYS_MODULE`), a macvlan network, sysctls or kernel modules. Their Quadlet files live in `/etc/containers/systemd/` and run as root, with their data under `/var/<key>`.

## Building blocks

The templates are assembled from a handful of systemd and Quadlet units. Reading one of the existing templates with these four blocks in mind is the fastest way to understand them all: [openwebui](templates/openwebui.md) is the smallest single container, [joplin](templates/joplin.md) the canonical pod, [overleaf](templates/overleaf.md) shows one-shot initialization, [caddy](templates/caddy.md) socket activation.

### Container

A `<name>.container` file is the Quadlet form of `podman run`. The templates always set:

```ini
[Container]
ContainerName=openwebui
Image=ghcr.io/open-webui/open-webui:main
AutoUpdate=registry
PublishPort=3009:8080
Volume=data.volume:/app/backend/data

[Service]
TimeoutStartSec=300
Restart=always
RestartSec=10
```

`AutoUpdate=registry` lets `podman auto-update` (and its `podman-auto-update.timer`, once enabled for the user) follow the image tag, which is why the examples pin a major or major.minor tag rather than `latest`. `TimeoutStartSec=300` leaves time for the first image pull, and the restart policy turns transient failures (a drive not mounted yet, a database still starting) into retries. Configuration that the application reads from a file is written by Ignition into the user's home and bind-mounted read-only (`:ro,Z`); configuration that the application takes from the environment is passed with `Environment=` lines.

### Volume

A `<name>.volume` file declares a Podman named volume:

```ini
[Volume]
VolumeName=postgres-data
```

Named volumes hold the state the application manages itself (databases, caches, generated keys): Podman creates them on first use and gives them the ownership the image expects, which a bind mount from the host would not. User data that must be reachable from outside the container, such as media libraries or photos, is a bind mount instead, from a directory under `/var` or from an [ext4 drive](templates/ext4_drives.md).

### Pod

Applications that ship as several containers (application, database, cache) are grouped in a `<key>.pod`:

```ini
[Pod]
PodName=joplin
ServiceName=joplin
PublishPort=3007:3000
```

The containers of a pod share a network namespace, so they reach each other on `localhost` or by container name, and only the pod publishes ports. Credentials between the containers of one pod are hard-coded in the template: they are not reachable from outside, and exposing them as parameters would only add decisions without adding security. Each container lists the ones it needs with `Requires=` and `After=` so the database starts first, and `ServiceName=` gives the whole pod the `<key>.service` name that the maintenance commands use.

### Systemd service

Everything that is not a container is a plain user unit:

- **One-shot initialization.** Steps that upstream guides ask to run by hand (initialize a replica set, create a database, run a setup wizard) are a `Type=oneshot` unit that waits for the application to answer, performs the step, then touches a stamp file in the user's home; `ConditionPathExists=!<stamp>` keeps it from running again. The main unit pulls it in with `Wants=`, so a failed initialization is visible in the journal and retried on the next start, without taking the application down.
- **Socket activation.** Caddy's `caddy.socket` unit opens ports 80 and 443 (TCP and UDP) and passes the file descriptors to the container, so the service starts on the first connection and the container never needs the privilege to bind those ports.
- **Helpers.** Jellyfin's `socat.service` forwards a TCP port to the UNIX socket the application creates, and mount units generated by [ext4_drives](templates/ext4_drives.md) mount data drives on demand.

## Scope

What is deliberately not here:

- **No configuration management after boot.** The configuration is applied once by Ignition. Changing a parameter means rebuilding and reprovisioning, or applying a single template by hand with `build_adhoc_script.py` as described in [Maintenance](getting-started/maintenance.md#applying-a-template-to-a-running-server).
- **No orchestration.** There is no scheduler, no service discovery and no shared overlay network; services are static and addressed by port on the host.
- **No secrets management.** `metaconfig.yaml` contains the credentials in clear and ends up, through Ignition, readable by root on the server. Keep the file out of version control.
