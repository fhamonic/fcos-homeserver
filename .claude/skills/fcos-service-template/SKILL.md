---
name: fcos-service-template
description: Add a new self-hosted service to this Fedora CoreOS home server as a Jinja2 Butane template (rootless Podman Quadlet), validate it, debug container failures with a local docker mirror, and document it in the wiki. Use when asked to add, template, port, fix, or document a service (from a docker-compose file, an upstream setup guide, or journal logs of a failing unit).
---

# Purpose

Every service in this repo is one `templates/<key>.yaml.j2` file rendered by
`build_config.py` into a Butane fragment and merged with the others. The
conventions are strict enough that most of the work is mechanical, and most
failures come from a small set of container-runtime pitfalls that can be
reproduced locally with docker before touching the server. This skill is the
checklist for both halves: writing the template, and debugging it.

Read the existing templates before writing a new one. `joplin` is the
canonical pod (multi-container) example, `openwebui` the canonical single
container, `overleaf` the stamped one-shot initialization, `caddy` socket
activation, `adguardhome` and `wg_easy` the rootful exceptions.

# Part 1 — Writing the template

## 1. Gather the upstream facts

Fetch, in this order, and extract concrete values (images, ports, env vars,
volumes, `user:`, healthcheck, init steps):

1. The upstream `docker-compose.yml` (raw URL on GitHub, not the rendered page).
2. The setup guide for self-hosting.
3. Any init/provisioning script the guide tells the user to run. If it only
   sets configuration keys or creates a database, bake that into a mounted
   config file or a one-shot unit instead of requiring the script at runtime
   (FCOS has no Deno, Node, etc.).
4. The image's entrypoint (`docker run --rm --entrypoint sh <image> -c 'cat /docker-entrypoint.sh'`
   or `grep -n "id -u\|chown\|set -e"`). This is where read-only mounts,
   `user:` requirements and chown behaviour hide.

Tag check: confirm the image tag exists (`https://hub.docker.com/v2/repositories/<ns>/<name>/tags?name=<tag>`
or the GHCR page) and prefer a major or major.minor tag, never `latest`,
because `AutoUpdate=registry` follows the tag.

## 2. Compose to Quadlet mapping

| compose | Quadlet (`[Container]`) |
|---|---|
| `image:` | `Image=` + `AutoUpdate=registry` |
| `ports: "H:C"` | `PublishPort={{ key.http_port }}:C` (on the `.pod` when there is a pod) |
| `ports: "H:C/udp"` | `PublishPort=...:C/udp` |
| `environment:` | one `Environment=K=V` per entry (`{{ key.field }}` for user-facing ones) |
| `volumes: name:/path` | a `<name>.volume` file (`[Volume] VolumeName=<name>`) and `Volume=<name>.volume:/path` |
| `volumes: ./dir:/path` | bind mount from `/home/u_<key>/...` or `/var/<key>` with `:Z` (`:ro,Z` for config) |
| `user: U:G` | `UserNS=keep-id:uid=U,gid=G` + `User=U:G` (see pitfalls) |
| `depends_on:` | `[Unit] Requires=/After=<other>.container` (or `.service`) |
| `healthcheck:` | `HealthCmd=` `HealthInterval=` `HealthTimeout=` `HealthRetries=` |
| `command:` | `Exec=` |
| `shm_size:` | `ShmSize=` |
| `cap_add:` / `sysctls:` | `AddCapability=` / `Sysctl=` (rootful templates only) |
| `restart:` | `[Service] Restart=always` `RestartSec=10` `TimeoutStartSec=300` |

Multiple containers that talk to each other go in a pod (`<key>.pod`,
`PodName=<key>`, `ServiceName=<key>`); they reach each other on `localhost`
or by `ContainerName`. A single container publishes its own port.

## 3. File skeleton (rootless)

Copy `templates/openwebui.yaml.j2` (single container) or
`templates/joplin.yaml.j2` (pod) and rename `openwebui`/`joplin` to `<key>`
everywhere. Keep the blocks in this order and with the same `# ####` banners:

1. `passwd`: `g_<key>` / `u_<key>` with `gid`/`uid` `{{ 1000 + id }}`.
2. `storage.directories`: the rootless boilerplate, **including**
   `/home/u_<key>/.config/systemd` (Ignition creates missing parents as root,
   which breaks the user's `systemctl --user`).
3. `storage.links`: `default.target.wants/<key>.service` pointing at the
   `.pod` (pod) or `.container` (single). systemd logs a "has different name"
   warning for this; it is expected.
4. `storage.files`: linger file, then configuration files, then volumes,
   then containers, then one-shot init units, then helper scripts.

Every file owned by `u_<key>`/`g_<key>`, mode `0644` (scripts `0755`),
directories `0755`. Rootful templates (need `NET_ADMIN`, macvlan, kernel
modules) skip `passwd` and write to `/etc/containers/systemd/` with
`[Install] WantedBy=default.target` instead of a symlink.

## 4. One-shot initialization

For "create the database / init the replica set / register admin" steps:

```ini
[Unit]
Description=...
Requires=<key>.service
After=<key>.service
ConditionPathExists=!/var/home/u_<key>/%N.stamp

[Service]
Type=oneshot
ExecStart=/bin/sh -c " \
  while ! <readiness probe>; do echo \"Waiting for X...\"; sleep 1; done; \
  <init command>"
ExecStart=/usr/bin/touch /var/home/u_<key>/%N.stamp
Restart=no
```

Add `Wants=<key>-init-xxx.service` to the `[Unit]` of the pod or container.
Probe from the host with `curl` against `http://127.0.0.1:{{ key.http_port }}`
or with `podman exec <container> ...`; both exist on FCOS. Use the unit
literally as the ordering target (`<key>.service`, not `.container`) in
`Requires=`/`After=` of plain systemd units.

## 5. Parameters and metaconfig

Expose only what a user must decide: images, `http_port`, credentials,
public URL (`self_url`), host paths. Hard-code internal passwords between
containers of the same pod (existing templates do). Add an example block to
`metaconfig.yaml` (next free port in the 30xx range) and a matching
`caddy.https_redirections` route. Never edit `secret.yaml`.

## 6. Validate before reporting done

Run the helper, which renders only the new template in a scratch directory
(so the user's `config.bu` is untouched), validates with butane strict, and
prints the decoded unit files. Export `SCRATCHPAD` to the session scratchpad
first so nothing is written under `/tmp`:

```bash
export SCRATCHPAD=<session scratchpad directory>
bash .claude/skills/fcos-service-template/scripts/render_check.sh <key> [metaconfig.yaml]
```

Then confirm the ad hoc script (used to apply a template to a live server
without reprovisioning) reproduces every file byte for byte:

```bash
python .claude/skills/fcos-service-template/scripts/adhoc_roundtrip.py <key> [metaconfig.yaml]
```

Both must pass. Report their output faithfully.

# Part 2 — Debugging with a local docker mirror

The local machine has docker, the server has rootless podman. A container
that dies in the first second on the server almost always dies the same way
under docker if the run is mirrored. Mirror the quadlet exactly:

```bash
docker run --rm --name mirror \
  --user U:G \                       # only if the template sets User=
  -e K=V ... \                       # every Environment=
  -v <scratch>/file:/path:ro \       # every bind mount, same :ro
  -v mirror-data:/path \             # every named volume
  -p 127.0.0.1:15984:C \             # the published container port
  <image>
```

Then, in order:

1. **Exit code and last log lines.** Exit 1 within ~100 ms means the
   entrypoint aborted, not the application; read the entrypoint.
2. **Entrypoint as root vs as the image uid.** If it runs `chown`/`find -exec
   chown` under `set -e`, a read-only or foreign-uid mount kills it. Fix by
   running as the image's service uid: `UserNS=keep-id:uid=U,gid=U` and
   `User=U:U` (the upstream compose `user:` line is the hint). Named volumes
   still get the right owner because podman chowns a fresh volume to the
   image directory's owner.
3. **Health and readiness probes.** Check whether the endpoint needs auth
   (`curl -s -o /dev/null -w '%{http_code}' URL` with and without `-u`), and
   whether the service listens on IPv6 (`curl 'http://[::1]:PORT/'` inside
   the container, or look for the port in `/proc/net/tcp6`). If not, use
   `127.0.0.1` everywhere: on the host, `localhost` may resolve to `::1` and
   pasta accepts then resets the forwarded connection, which curl reports as
   exit 56 instead of a clean refusal.
4. **Configuration actually applied.** Query the application's config API or
   inspect files inside the container to prove the mounted config took
   effect, then exercise the init step (create DB, login) against the mirror.
5. Tear down: `docker rm -f mirror; docker volume rm mirror-data`.

Distinguish harness artifacts from real failures: a fake root missing
`/var/lib/systemd/linger`, a sed that rewrote paths inside file contents, a
port already in use locally. Fix the harness and rerun before concluding.

## Reading server logs

Ask for or run `journalctl --user -u <key>.service -u <key>-init-*.service`
as `u_<key>` (`sudo machinectl shell u_<key>@`). Signatures seen so far:

| Symptom | Cause | Fix |
|---|---|---|
| container "died" < 1 s after start, exit 1, no app logs | entrypoint aborted (chown on ro mount) | run as image uid (`keep-id:uid=`) |
| healthcheck `unhealthy`, app logs `GET /_up 401` | probe hits an authenticated endpoint | add `-u user:pass` to `HealthCmd` |
| init unit exits 56, no request in app access log | curl used `::1` through pasta | use `127.0.0.1` |
| init unit "killed, status=15/TERM" repeatedly | main service restarting under it | fix the main service first; this is collateral |
| `Wants dependency dropin ... has different name` | the `.service` symlink to a `.container` | expected, ignore |
| permission denied on a named volume after a failed root run | volume chowned by an earlier run | `podman volume rm <name>` as `u_<key>` once |

## Applying a fix to the running server

Regenerate the changed unit(s) with `python build_adhoc_script.py secret.yaml`
(select the key, paste only the relevant `tee` blocks), then:

```bash
sudo machinectl shell u_<key>@ /bin/bash -c 'systemctl --user daemon-reload && systemctl --user restart <key>.service'
```

A stamped init unit that never succeeded has no stamp and will rerun.

# Part 3 — Systemd/Quadlet gotchas in templates

- `%` in a unit value is a systemd specifier; `%N` is intended, anything else
  (for example in a password) must be `%%`.
- `$VAR` in `ExecStart` is expanded by systemd from the unit environment, not
  the container's; do not rely on it in `HealthCmd`. Template the value in
  with Jinja instead.
- Comments (`# ...`) are allowed in both `[Unit]` and `[Container]`.
- Jinja and Go templates collide: wrap upstream `{{...}}` in `{% raw %}`.
- Inline file contents go through `build_adhoc_script.py` as a quoted
  heredoc, so quotes, `$` and backslashes are safe there.
- `build_config.py` uses `StrictUndefined`: every `{{ key.x }}` must exist in
  the metaconfig block, so optional fields need `{% if key.x is defined %}`.

# Part 4 — Documentation

The docs live in the GitHub wiki, page `Templates`
(`git clone git@github.com:fhamonic/fcos-homeserver.wiki.git`). Do not push;
output the raw markdown for the user. Two pieces:

1. A summary-table row:
   `| [Name](https://github.com/fhamonic/fcos-homeserver/wiki/Templates#<key>) | Service | :white_check_mark: | one-line description |`
2. A section appended after the last one:

```markdown
---

# `<key>`

Configuration for the <Service> ... (what it is, what the template does for
it, how it is meant to be exposed through Caddy, client-side setup steps,
security notes as a `> **Note:**`).

## `<key>.image`

The image of <Service> to deploy.

* **Type:** String
* **Example:** `docker.io/...:tag`

## `<key>.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `30xx`

## `<key>.<field>`

One sentence on what it is and where it is used.

* **Type:** ...
* **Purpose:** ... (when not obvious)
* **Example:** `...`
```

Rootless column is `:white_check_mark:` unless the template writes to
`/etc/containers/systemd/`.
