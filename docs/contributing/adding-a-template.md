# Adding a template

A service is one file, `templates/<key>.yaml.j2`, that `build_config.py` renders into a Butane fragment and merges with the others. Writing one is mostly mechanical once you have read a couple of existing templates; the time goes into making the container start, which is why the loop below applies the template to a running server with the ad hoc script rather than reprovisioning at every attempt.

Read the [design rationale](../design-rationale.md) first: it explains the units a template is made of. Then read the templates it names, which cover every pattern in use: [openwebui](../templates/openwebui.md) (single container), [joplin](../templates/joplin.md) (pod), [overleaf](../templates/overleaf.md) (one-shot initialization), [caddy](../templates/caddy.md) (socket activation), [adguardhome](../templates/adguardhome.md) and [wg_easy](../templates/wg_easy.md) (rootful).

## 1. Start from the upstream compose file

The upstream `docker-compose.yml` and self-hosting guide give almost everything: images, ports, environment variables, volumes, the `user:` the container expects, the health check and the steps the guide asks to run by hand. Pick a major or major.minor image tag rather than `latest`, because `AutoUpdate=registry` follows the tag.

Two things are worth checking early. Setup steps that upstream runs with a script (create an admin, initialize a database) must become a mounted configuration file or a one-shot unit, since the server has no Node or Python to run them. And the image's entrypoint often decides whether the container starts at all under rootless Podman: a `chown` on a mounted directory, for example, fails on a read-only mount and kills the container before the application logs anything.

## 2. Write the template

Copy `templates/openwebui.yaml.j2` or `templates/joplin.yaml.j2` and rename the key everywhere. The template receives two variables: the block of `metaconfig.yaml` under its key, and `id`, the position of that key in the file, which gives the user and group their ids (`1000 + id`).

Keep the structure of the file you copied: the `passwd` block, the directories under `/home/u_<key>/.config` (including `.config/systemd` itself, which must be created by the template so it does not end up owned by root), the `default.target.wants` symlink to the `.pod` or `.container`, the linger file, then configuration files, volumes, containers, init units and helper scripts. Everything is owned by `u_<key>:g_<key>`, mode `0644` except scripts and directories (`0755`).

The compose file maps almost line by line:

| compose | Quadlet |
|---|---|
| `image:` | `Image=` + `AutoUpdate=registry` |
| `ports:` | `PublishPort=<host>:<container>` (on the `.pod` when there is one) |
| `environment:` | one `Environment=K=V` per entry |
| named volume | a `<name>.volume` file and `Volume=<name>.volume:/path` |
| `./dir:/path` | a bind mount from the user's home or `/var/<key>`, with `:Z` (`:ro,Z` for configuration) |
| `user: U:G` | `UserNS=keep-id:uid=U,gid=G` + `User=U:G` |
| `depends_on:` | `Requires=` / `After=<other>.container` |
| `healthcheck:` | `HealthCmd=`, `HealthInterval=`, `HealthTimeout=`, `HealthRetries=` |
| `command:` | `Exec=` |
| `restart:` | `[Service] Restart=always`, `RestartSec=10`, `TimeoutStartSec=300` |

Containers that talk to each other go in a pod and reach each other on `localhost`; other services on the host are reached as `host.containers.internal:<port>`. Steps to run once become a `Type=oneshot` unit that waits for the application, does its job and touches a stamp file, guarded by `ConditionPathExists=!<stamp>` (see the overleaf template for the shape).

Expose as parameters only what a user must decide: images, `http_port`, credentials, the public URL, host paths. Credentials between the containers of one pod stay hard-coded. Rendering is strict, so every `{{ key.x }}` must exist in the block; guard optional ones with `{% if key.x is defined %}`.

!!! note "Escaping"
    `%` in a unit value is a systemd specifier: `%N` is intended, a `%` in a password must be `%%`. `$VAR` in `ExecStart` is expanded by systemd from the unit's environment, not the container's. Upstream Go templates use `{{ ... }}` too; wrap them in `{% raw %} ... {% endraw %}`.

## 3. Append the block to `metaconfig.yaml`

Add an example block for the new key, with the next free port in the `30xx` range, and a matching [`caddy.https_redirections`](../templates/caddy.md#caddyhttps_redirections) route.

!!! warning "Append only"
    `id` is the position of the key in the file, and the user and group of the template get uid and gid `1000 + id`. Inserting a key in the middle shifts the id of every key after it: those templates get new uids on the next build, and the ad hoc script, run against a server provisioned with the old numbering, fails on `useradd` or creates users that no longer own their files. New keys go at the end.

## 4. Render and validate

```bash
python build_config.py metaconfig.yaml
docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign
```

Rendering stops at the first missing parameter with the template file and line; Butane rejects unknown fields and duplicate paths. Neither tells you whether the unit files make sense to Quadlet, so read them as they will land on the server. The repository ships a helper that renders only the new template next to `core` in a scratch directory, validates it and prints every unit file, and another one that checks the ad hoc script reproduces the template's files byte for byte:

```bash
bash .claude/skills/fcos-service-template/scripts/render_check.sh <key> metaconfig.yaml
python .claude/skills/fcos-service-template/scripts/adhoc_roundtrip.py <key> metaconfig.yaml
```

## 5. Try it on a running server

Generate the shell script that writes the files of the template onto a running server, as described in [Maintenance](../getting-started/maintenance.md#applying-a-template-to-a-running-server):

```bash
python build_adhoc_script.py metaconfig.yaml
```

Select the key and paste the printed commands into an SSH session as `core`. They create the user, the directories, the files and the links in the order Ignition would. The linger file only takes effect at boot, so start the user's session by hand, then the service:

```bash
sudo loginctl enable-linger u_<key>
sudo machinectl --uid=u_<key> shell
systemctl --user daemon-reload && systemctl --user start <key>.service
systemctl --user status <key>.service
```

The first start pulls the images and may take a few minutes. When the service does not come up, the [debugging page](../getting-started/debugging.md) has the commands: the container's output stays in the journal after Quadlet removed it, and the Quadlet generator can be asked what it made of the files.

To apply a change, run the script again and paste only the `tee` blocks of the files that changed, then `systemctl --user daemon-reload && systemctl --user restart <key>.service`. An init unit that never succeeded runs again on the next start; to rerun one that did, delete its stamp in the user's home. To start from scratch, stop the service, remove its named volumes with `podman volume rm`, leave the shell, then `sudo loginctl disable-linger u_<key>` and `sudo userdel -r u_<key> && sudo groupdel g_<key>`.

Consider the template done when the service survives a restart with its data intact, its init units have their stamps, and it is reachable through Caddy.

## 6. Document it

Every template has a page `docs/templates/<key>.md`: a paragraph on what the service is and how it is meant to be exposed, then one section per parameter with its type and an example, in the order of the block in `metaconfig.yaml`. Copy the page of a similar template. Add the page to the `Templates` list of `zensical.toml`, a row to the table of `docs/templates/index.md` and a link in the "What is in the box" table of `docs/index.md`, then check the build:

```bash
pip install zensical
zensical build --clean
```

It must end with `No issues found`; `zensical serve` previews the site.

## Letting an LLM do the first draft

The conventions above are also written down for machines, as a [Claude Code skill](https://github.com/fhamonic/fcos-homeserver/tree/main/.claude/skills/fcos-service-template) in `.claude/skills/fcos-service-template/`. It contains the same rules in a form an agent can follow, plus the two helper scripts of step 4 and a procedure for reproducing a failing container locally with Docker.

If you have access to a frontier model through an agent that can read the repository (Claude Code picks the skill up by itself; other agents can be pointed at `SKILL.md`), asking for "a template for `<service>` from its docker-compose file" gets a draft that follows the layout, renders, passes the two helpers and comes with its documentation page. Treat it as a draft: the agent has no server to try it on. Apply it with the ad hoc script, read the generated units, and check the points of step 5 (restart with data intact, init units stamped, reachable through Caddy) before opening a pull request.
