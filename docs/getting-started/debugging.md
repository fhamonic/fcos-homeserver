# Debugging services

Most problems show up as a service that restarts in a loop or never becomes active. This page lists the commands that answer the frequent questions first, then the less common ones. Everything here runs on the server, as the user of the service:

```bash
sudo machinectl --uid=u_<key> shell
```

`machinectl` starts the user's systemd instance and sets up the session bus; `sudo -u u_<key> systemctl --user` does not and fails with `Failed to connect to bus`. For the rootful templates ([adguardhome](../templates/adguardhome.md), [wg_easy](../templates/wg_easy.md)), drop `--user` from every command below and prefix it with `sudo`.

## What failed

```bash
systemctl --user --failed                       # units in failed state
systemctl --user status <key>.service           # state, exit code, last log lines
systemctl --user list-dependencies <key>.service   # containers and init units pulled in by a pod
```

A pod gives one unit per Quadlet file: `<key>.service` for the pod itself and `<name>.service` for each `<name>.container` (for example `joplin-postgres.service`), so the failing unit is often not the one named after the template.

## Logs of a container that no longer exists

Quadlet runs every container with `--rm` and removes it again in `ExecStopPost`, so after a failure `podman ps -a` shows nothing and `podman logs` has nothing to read. The output is not lost: Podman's default log driver on Fedora CoreOS is `journald`, and the container runs inside the unit's cgroup, so its stdout and stderr are in the journal under the unit:

```bash
journalctl --user -u <key>.service -b -e          # this boot, jump to the end
journalctl --user -u <key>.service -o cat -n 200  # raw output, no timestamps
journalctl --user -u <key>.service -f             # follow while restarting it
journalctl --user -u <key>.service --since "10 min ago"
```

The journald driver also tags every line with the container name, which is the easiest way to find the output of one container of a pod, or of a container whose unit name you are not sure of:

```bash
journalctl --user CONTAINER_NAME=<container> -b -e
```

Combine several units to see an init unit next to the service it waits for, and add `-g <regex>` to filter on the message:

```bash
journalctl --user -u <key>.service -u '<key>-init-*' -b -g 'error|denied|refused'
```

!!! tip
    A container that "died" less than a second after starting, with exit code 1 and no application output, was killed by its entrypoint, not by the application: look for a `chown` or `set -e` in the entrypoint script that hits a read-only or foreign-uid mount, and run the container as the image's own uid with `UserNS=keep-id:uid=U,gid=G` and `User=U:G`.

## Keeping a failed container around

To inspect the file system, mounts or environment of a container that exits immediately, run it by hand from the same command line systemd uses. Print the generated unit, copy the `podman run` line of `ExecStart`, and drop `--rm`, `-d` and the `--sdnotify` option:

```bash
systemctl --user stop <key>.service
systemctl --user cat <name>.service              # ExecStart=/usr/bin/podman run ...
podman run --name <container> --replace ... <image>   # the same line, without --rm -d --sdnotify=...
podman logs <container>
podman inspect <container> --format '{{ .State.ExitCode }} {{ .State.Error }}'
podman rm -f <container>
```

To look around inside the container with the real mounts and environment before its entrypoint runs, add a drop-in to the Quadlet file that replaces the entrypoint, then `exec` into the running container. Remove the drop-in afterwards:

```bash
mkdir -p ~/.config/containers/systemd/<name>.container.d
printf '[Container]\nEntrypoint=/bin/sleep\nExec=infinity\n' > ~/.config/containers/systemd/<name>.container.d/debug.conf
systemctl --user daemon-reload && systemctl --user restart <name>.service
podman exec -it <container> sh
rm -r ~/.config/containers/systemd/<name>.container.d
systemctl --user daemon-reload && systemctl --user restart <name>.service
```

Reading the entrypoint itself does not need the server at all:

```bash
podman run --rm --entrypoint sh <image> -c 'cat /docker-entrypoint.sh'
```

## Quadlet refused the files

`systemctl --user daemon-reload` runs the Quadlet generator, which turns every `.container`, `.pod`, `.volume` and `.socket` under `~/.config/containers/systemd/` into a service. The generator is silent on success and, on failure, drops the unit without stopping `daemon-reload`, so the symptom is `Unit <key>.service not found` on the next `start`, or a service that is not listed at all. Ask the generator directly, which prints the generated units, or the reason it refused a file:

```bash
/usr/lib/systemd/system-generators/podman-system-generator --user --dryrun
```

Its messages from the last `daemon-reload` are also in the journal, prefixed with `quadlet-generator`:

```bash
journalctl --user -b -g quadlet-generator
```

Once the unit exists, `systemd-analyze` checks it the way systemd will load it (unknown directives, missing dependencies, bad `ExecStart` lines), and `cat` shows the final `podman run` command line, with every `Volume=`, `PublishPort=` and `Environment=` translated:

```bash
systemd-analyze --user --generators=true verify <key>.service
systemctl --user cat <key>.service
```

To check a file before copying it in place, point the generator at any directory:

```bash
QUADLET_UNIT_DIRS=/var/home/u_<key>/scratch /usr/lib/systemd/system-generators/podman-system-generator --user --dryrun
```

Frequent causes: a key not supported by the Podman version on the server, a `Volume=<name>.volume` or `Pod=<key>.pod` whose file does not exist, a `Requires=` on a Quadlet file name where the generated service name is expected in a plain `.service` unit, and a `default.target.wants` symlink whose target is wrong (the `Wants dependency dropin ... has different name` warning for that symlink is expected and harmless).

## Health checks

A container with a `HealthCmd=` turns `unhealthy` when the probe fails, which shows in `podman ps` and in the unit status when `Notify=healthy` is set. Run the probe by hand and read the last results:

```bash
podman healthcheck run <container>; echo $?
podman inspect <container> --format '{{ json .State.Health }}'
```

The probe runs inside the container, so `localhost` is the container's own loopback there, and it needs the container's tools (`curl` or `wget` may be missing from the image). Two signatures seen so far: the endpoint needs authentication (the application log shows `401` on every probe; add `-u user:pass` to the command), and the probe uses `localhost` when the application only listens on IPv4 (use `127.0.0.1`).

## One-shot init units

The `<key>-init-*.service` units run once, then touch a stamp in the user's home; `ConditionPathExists=!.../%N.stamp` keeps them from running again:

```bash
systemctl --user status '<key>-init-*'
journalctl --user -u '<key>-init-*' -b
ls ~/*.stamp
```

A unit that failed has no stamp and runs again on the next start of the service; to rerun one that succeeded, delete its stamp and `systemctl --user start` it. An init unit that is repeatedly `killed, status=15/TERM` is collateral of the main service restarting under it: fix the main service first.

An init unit that probes the service with `curl` and exits with code 56 without any request reaching the application used `localhost`, which resolved to `::1`: the rootless network stack accepts the IPv6 connection and resets it. Use `127.0.0.1`.

## Images and volumes

Image pulls happen at the first start, inside `TimeoutStartSec=300`. To see the registry's own error (wrong tag, rate limit, private image):

```bash
podman pull <image>
podman images
```

Named volumes are created on first use and owned by whoever the image expects, but they keep the ownership of their first use. A volume that was first written by a container running as a different uid gives `permission denied` on every later start; remove it once (this deletes its data):

```bash
podman volume ls
podman volume inspect <name> --format '{{ .Mountpoint }}'
podman unshare ls -ln "$(podman volume inspect <name> --format '{{ .Mountpoint }}')"
podman volume rm <name>
```

`podman unshare` shows the files with the uids of the container's user namespace, which is what the container sees. Bind mounts from the user's home need the `:Z` label; a mount that works as root and fails as the user is usually an SELinux denial, visible with `sudo ausearch -m avc -ts recent`.

## Ports and networking

Check that the port is published and that the application answers behind it:

```bash
ss -ltn                                          # published ports listen on the host
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<http_port>/
podman port <container>
```

Rootless containers get their network from pasta, which forwards published ports to the container. From the host, use `127.0.0.1` rather than `localhost` when probing: `localhost` may resolve to `::1`, which pasta accepts and resets when the application does not listen on IPv6, and `curl` reports that as exit 56 instead of a clean refusal. Inside a container, other services on the host are reached as `host.containers.internal:<port>`.

## Automatic updates

`podman auto-update` follows the tag of every container with `AutoUpdate=registry` and rolls back a container whose new image fails to start. To see what would change, or why a rollback happened:

```bash
podman auto-update --dry-run
journalctl --user -u podman-auto-update.service
```

## Starting over

To reset a service without reprovisioning, as its user:

```bash
systemctl --user stop <key>.service
systemctl --user reset-failed
podman rm -af                     # any container left behind
podman volume rm <name>           # its named volumes, data included
rm ~/<key>-init-*.stamp           # so the init units run again
systemctl --user daemon-reload && systemctl --user start <key>.service
```

## Reproducing a failure locally

A container that dies in the first second on the server almost always dies the same way under Docker on a workstation, if the run mirrors the Quadlet file: same `--user`, every `Environment=` as `-e`, every bind mount with the same `:ro`, every named volume, and the published port.

```bash
docker run --rm --name mirror \
  --user U:G \
  -e K=V \
  -v "$PWD/config.yml:/etc/app/config.yml:ro" \
  -v mirror-data:/data \
  -p 127.0.0.1:18080:8080 \
  <image>
```

Then, in order: read the exit code and the last log lines; if the container exits in about 100 ms, read the entrypoint rather than the application; check whether the health and readiness endpoints need authentication or IPv6; prove the mounted configuration was applied by querying the application; and exercise the init step (create the database, log in) against the mirror. Tear down with `docker rm -f mirror; docker volume rm mirror-data`.

## Signatures seen so far

| Symptom | Cause | Fix |
|---|---|---|
| container "died" < 1 s after start, exit 1, no application logs | entrypoint aborted (`chown` on a read-only mount) | run as the image's uid (`UserNS=keep-id:uid=...`, `User=`) |
| `unhealthy`, application logs `401` on the probe path | health check hits an authenticated endpoint | add `-u user:pass` to `HealthCmd` |
| init unit exits 56, no request in the application log | `curl` used `::1` through pasta | use `127.0.0.1` |
| init unit `killed, status=15/TERM` repeatedly | the main service restarts under it | fix the main service; this is collateral |
| `Unit <key>.service not found` after `daemon-reload` | Quadlet refused a file | `podman-system-generator --user --dryrun` |
| `Failed to connect to bus` | `systemctl --user` outside a session | use `machinectl`, not `sudo -u` |
| `permission denied` on a named volume | volume chowned by an earlier run as another uid | `podman volume rm <name>` once |
| `Wants dependency dropin ... has different name` | the `.service` symlink to a `.container` or `.pod` | expected, ignore |
