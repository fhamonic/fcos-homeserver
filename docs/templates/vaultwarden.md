# `vaultwarden`

Configuration for [Vaultwarden](https://github.com/dani-garcia/vaultwarden), a lightweight password manager server compatible with the Bitwarden clients (browser extensions, desktop and mobile apps, command line) and bundling the Bitwarden web vault. The template deploys the single container with a named volume for its SQLite database, attachments and keys, exposed over plain HTTP on `http_port` and meant to be published through a [Caddy](caddy.md) site at `hostname`. The clients refuse to talk to a server over plain HTTP, so the service is only usable through that site.

Nobody can register by themselves: accounts are created by invitation from the administration page at `https://<hostname>/admin`, protected by `admin_password`. Invite an address under *Users › Invite*, then the invitee opens `https://<hostname>`, chooses *Create account* and registers with that address. No mail is sent as long as SMTP is not configured, so tell them yourself.

In each client, open the settings of the login page (*Logging in on: Self-hosted*) and enter `https://<hostname>` as *Server URL* before logging in.

!!! note
    The administration page is reachable from anywhere the Caddy site is, with the password as its only protection. To keep it on the LAN, give its [`caddy.public_sites`](caddy.md#caddypublic_sitesdirectives) entry `directives` instead of a plain `port`:

    ```yaml
    - hostname: vault.mydomain.com
      directives: |
        @admin_outside {
            path /admin*
            not remote_ip 192.168.0.0/24
        }
        respond @admin_outside 403
        reverse_proxy host.containers.internal:3019
    ```

!!! note
    Vaultwarden prints a notice at each start about the `ADMIN_TOKEN` being given in plain text rather than as an Argon2 hash. It is expected: the password sits in the Quadlet unit, readable by `u_vaultwarden` only, like the credentials of the other templates.

To send mail (invitations, address verification, emergency access, two-factor codes by mail), fill the *SMTP Email Settings* of the administration page with the [stalwart](stalwart.md) relay: host `host.containers.internal`, its `smtp_port`, security `starttls`, `sender.username` / `sender.password` and `sender.username@domain` as From address, and enable *Accept Invalid Certs* since the relay's certificate is self-signed. Settings saved from the administration page are stored in the data volume and take precedence over the environment of the container.

Everything to keep is in the `data` volume. Vaultwarden writes a consistent copy of the SQLite database with `podman exec vaultwarden /vaultwarden backup` (run as `u_vaultwarden`, see the [maintenance page](../getting-started/maintenance.md)), next to it in the volume, as `db_<date>.sqlite3`.

## `vaultwarden.image`

The image of Vaultwarden to deploy. The project publishes only exact version tags (`1.37.2`) next to `latest`, so updating means bumping the tag.

* **Type:** String
* **Example:** `docker.io/vaultwarden/server:1.37.2`

## `vaultwarden.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3019`

## `vaultwarden.hostname`

Public host name of the service, given as `https://<hostname>` to Vaultwarden, which the clients compare with the server URL they were configured with. It should match its [Caddy](caddy.md) site.

* **Type:** Fully qualified domain name
* **Example:** `vault.mydomain.com`

## `vaultwarden.admin_password`

Password of the administration page at `/admin` (Vaultwarden's `ADMIN_TOKEN`), which has no username.

* **Type:** String
* **Purpose:** Inviting users and changing the server settings.
* **Example:** `L0NgP@SsW0rD`
