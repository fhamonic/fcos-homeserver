# Automatic updates

Every container of every template carries `AutoUpdate=registry`, and every template enables Podman's update timer: once a day, each service checks the registry for a newer image behind its tag, pulls it, restarts the service, and rolls back if the new image fails to start. The OS itself is updated by Zincati; this page is about the containers.

## What a run does

Podman ships `podman-auto-update.timer`, which fires `podman auto-update` daily with up to fifteen minutes of random delay, and catches up at boot when the server was off at the time. A run:

1. Resolves the tag of every container with `AutoUpdate=registry` and compares the digest with the running image.
2. Pulls the changed images and restarts the units of the containers that use them.
3. Rolls a unit back to the previous image when the new one does not start.
4. Removes the images nothing uses any more.

The timer is a per-user unit. Each rootless service runs its own systemd instance, so each template enables the timer for its user, exactly as it enables its service: a symlink in `~/.config/systemd/user/timers.target.wants/`. The rootful templates ([adguardhome](../templates/adguardhome.md), [wg_easy](../templates/wg_easy.md)) share the system instance, whose timer is enabled once by [core](../templates/core.md).

## What may change: the image tag

The timer decides how soon an update lands; the image tag decides what an update may be. Podman follows the tag, so the tag of every `image` parameter is the only knob that matters:

| Tag | Effect of a run |
|---|---|
| `jellyfin:10` | patch and minor releases of the major version, which is what the examples use |
| `jellyfin:10.10` | patch releases only |
| `jellyfin:10.10.7` | nothing ever changes, the run still checks |
| `jellyfin:latest` | anything, including breaking releases |

!!! note "Pin the tag, keep the timer"
    Disabling updates on a service to avoid a breaking change also stops its security fixes. Pin the tag to the version you want instead: a fully pinned tag makes the daily run a no-op, and moving the tag later is one line in `metaconfig.yaml`. This is also why the timer has no off switch.

## `<key>.auto_update`

Every rootless template takes the same optional parameter, which replaces the daily schedule of its timer with a [systemd calendar expression](https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html#Calendar%20Events). The usual reason is not the cadence but the restart: a service that is in use at midnight is better updated in a quiet hour.

* **Optional**
* **Type:** String, a systemd calendar expression
* **Purpose:** When the service checks for a new image, and therefore when it may restart. Without it, Podman's default: daily, with up to fifteen minutes of random delay.
* **Example:** `Sun 04:00`

Other useful values: `weekly` (Monday at midnight), `monthly`, `*-*-* 05:30` (every day at half past five). Quote a value that starts with `*`, which YAML would otherwise read as an alias. The random delay and the catch-up after a missed run stay as they are.

The build checks the expression with `systemd-analyze calendar` when the machine that runs `build_config.py` has systemd, and stops with the message systemd gives. Without that check, a wrong expression only shows on the server, where the timer refuses to load. The rootful templates share one timer and take no schedule of their own; giving them the parameter is a build error.

The parameter is rendered as a drop-in on the user's timer:

```ini title="~/.config/systemd/user/podman-auto-update.timer.d/schedule.conf"
[Timer]
OnCalendar=
OnCalendar=Sun 04:00
```

The empty line matters: `OnCalendar=` accumulates, and without it the timer would fire on the daily schedule as well as the new one.

## Checking on it

As the service's user (see [Maintenance](maintenance.md#service-users)):

```bash
systemctl --user list-timers                     # next and last run of the timer
podman auto-update --dry-run                     # what a run would change now
journalctl --user -u podman-auto-update.service  # what the last runs did, rollbacks included
```

For the rootful services, the same commands with `sudo` and without `--user`.

## Enabling it on a running server

Applying a template with the ad hoc script (see [Maintenance](maintenance.md#applying-a-template-to-a-running-server)) creates the symlink and the drop-in, but does not tell the running systemd instance about them. As the service's user:

```bash
systemctl --user daemon-reload
systemctl --user start podman-auto-update.timer
```

The ad hoc script does not handle the `systemd` block of `core`, so the system timer for the rootful services is enabled by hand:

```bash
sudo systemctl enable --now podman-auto-update.timer
```
