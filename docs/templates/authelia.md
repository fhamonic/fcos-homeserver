# `authelia`

Configuration for [Authelia](https://www.authelia.com/), the login portal of Caddy's [protected sites](caddy.md#caddyprotected_sites). Before serving a request from outside the LAN, Caddy asks Authelia whether the browser has a session, and sends it to the portal at `hostname` otherwise; once logged in, the user comes back to the page they asked for. The session is shared by every host name under `domain`, so one login covers all the protected sites. The template deploys the single container, with its SQLite database in the `data` volume and the users listed in `users`.

On the Caddy side, publish the portal with a [`caddy.public_sites`](caddy.md#caddypublic_sites) entry for `hostname` pointing at `http_port`, and set [`caddy.authelia.port`](caddy.md#caddyauthelia) to `http_port` as well:

```yaml
caddy:
  authelia:
    port: 3023
  public_sites:
    - hostname: auth.mydomain.com
      port: 3023
  protected_sites:
    - hostname: prometheus.mydomain.com
      port: 3013
```

Every host under `domain` requires the login: Authelia only decides for the sites that Caddy asks it about, which are the protected sites. A session lasts one hour; tick *Remember me* on the portal for a longer one.

The users file is generated from `users` and mounted read-only, so the portal offers no password reset or change: to change a password, replace its hash in `metaconfig.yaml` and apply the template again with the [ad hoc script](../getting-started/maintenance.md#applying-a-template-to-a-running-server). The hash is printed by Authelia itself, which asks for the password twice:

```bash
podman run --rm -it docker.io/authelia/authelia:4.39 authelia crypto hash generate argon2
```

The session secret and the storage encryption key are generated at first start by `authelia-init-secrets.service`, into `/var/home/u_authelia/authelia.env`. Keep that file with the `data` volume when backing up: the database cannot be read without the key.

!!! note
    With `policy: two_factor`, each user registers a second factor (an authenticator app or a security key) at their first login. Authelia confirms the registration with a one-time code that it would normally send by mail; without a mail server, it writes the message to a file in its volume instead. Read it as `u_authelia` (see the [maintenance page](../getting-started/maintenance.md)) with `podman exec authelia cat /data/notification.txt`.

## `authelia.image`

The image of Authelia to deploy.

* **Type:** String
* **Example:** `docker.io/authelia/authelia:4.39`

## `authelia.http_port`

Port to listen for HTTP requests. Caddy sends it both the requests for the portal and the checks of the protected sites.

* **Type:** Integer
* **Example:** `3023`

## `authelia.hostname`

Host name of the login portal, published as a public Caddy site. It must be under `domain`.

* **Type:** Fully qualified domain name
* **Example:** `auth.mydomain.com`

## `authelia.domain`

Domain of the session cookie. The portal and every protected site must be `domain` itself or a host under it, or the browser does not send them the session.

* **Type:** Domain name
* **Example:** `mydomain.com`

## `authelia.policy`

What a login requires: `one_factor` for the password alone, `two_factor` for the password and a second factor.

* **Optional**, `one_factor` when left out
* **Type:** `one_factor` or `two_factor`
* **Example:** `two_factor`

## `authelia.users`

List of the accounts that can log in.

* **Type:** List

### `authelia.users[].username`

Name to log in with, also passed to the applications in the `Remote-User` header.

* **Type:** String
* **Example:** `admin`

### `authelia.users[].email`

Address of the user, passed to the applications in the `Remote-Email` header.

* **Type:** Email address
* **Example:** `admin@mydomain.com`

### `authelia.users[].password_hash`

Argon2 hash of the user's password, printed by the command above.

* **Type:** String
* **Example:** `$argon2id$v=19$m=65536,t=3,p=4$...`
