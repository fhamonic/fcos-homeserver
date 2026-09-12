# Maintenance

The server is meant to run without intervention. When something needs a look, this page covers the few commands involved.

## SSH

All administrative access to the FCOS home server should be performed from the machine holding the **registered SSH key**, replacing the address as appropriate:

```bash
ssh core@192.168.xxx.xxx
```

The `core` user has no password: the key listed in [`core.ssh_authorized_keys`](../templates/core.md#coressh_authorized_keys) is the only way in, and `sudo` does not ask for a password.

## Service users

Each rootless service runs under its own **dedicated user** and group:

- Usernames are prefixed with `u_`
- Group names are prefixed with `g_`

These service users:

- Do **not** have SSH keys or passwords
- Can only be accessed from the host via `machinectl`:

```bash
sudo machinectl --uid=u_jellyfin shell
```

This opens a shell in the context of the service's user, allowing inspection and debugging.

The few rootful templates ([adguardhome](../templates/adguardhome.md), [wg_easy](../templates/wg_easy.md)) have no user of their own: their units live in `/etc/containers/systemd/` and are managed with plain `sudo systemctl`.

## Viewing service status and logs

Once logged in as a service user:

- Check **service status**:

```bash
systemctl --user status
```

- View **service logs**:

```bash
journalctl --user
```

!!! tip
    Use `journalctl` [filtering options](https://man7.org/linux/man-pages/man1/journalctl.1.html#FILTERING_OPTIONS) (`-u jellyfin.service`, `--since today`, `-f`...) or `grep` to locate relevant entries quickly.

When a service does not come up, the [debugging page](debugging.md) lists the commands for the usual questions: the logs of a container Quadlet already removed, what the Quadlet generator made of the unit files, health checks, init units and volumes.

## Modifying service containers

To update or tweak a service container:

1. Edit the Quadlet configuration file:

    ```bash
    nano .config/containers/systemd/jellyfin.container
    ```

2. Reload the systemd user daemon:

    ```bash
    systemctl --user daemon-reload
    ```

3. Restart the service:

    ```bash
    systemctl --user restart jellyfin
    ```

Such changes are lost at the next reprovisioning. Once a tweak is settled, fold it back into the template or into `metaconfig.yaml` so the next installation reproduces it.

## Applying a template to a running server

Reprovisioning is the only way to apply a new template entirely, but `build_adhoc_script.py` generates a shell script that writes the files of one template onto a running server, for trying a new service or updating an existing one without reinstalling:

```bash
python build_adhoc_script.py metaconfig.yaml
```

The script asks which key to apply (it needs the `questionary` package) and prints the shell commands that create the user, directories, files and links of that template. Run them on the server, then start the service as its user with `systemctl --user daemon-reload && systemctl --user start <key>.service`.

This is also the loop for developing a template: write it, apply it with the ad hoc script, debug it, fold the fix back into the template. [Adding a template](../contributing/adding-a-template.md) walks through every step, from the upstream compose file to the documentation page.
