# `stalwart`

Configuration for the [Stalwart](https://stalw.art) mail server, deployed as the outgoing mail relay of the other services.

A home server usually cannot deliver mail by itself: residential ISPs block outbound port 25 and their address ranges are rejected by the major providers.
This template therefore deploys Stalwart as a *submission* server for the applications of the home server (Forgejo, Joplin, Immich, Overleaf...), which hands every message to the SMTP service of a mail provider (the one hosting the mailboxes of the domain, or a transactional service such as Brevo or Amazon SES) over authenticated submission on port 465 or 587, which are not blocked.
The applications get a single set of credentials, a persistent queue with retries when the provider is unreachable, DKIM signing, and a web administration interface.

Stalwart keeps its whole configuration in its database and only exposes it through its management API, so `stalwart-init.service` runs the setup wizard and applies the relay configuration at first boot:

* setup wizard: hostname, domain, DKIM keys, logs to the journal, no Let's Encrypt certificate (port 443 belongs to Caddy);
* a relay route to the provider, used for every recipient, including the addresses of the domain itself since their mailboxes are hosted by the provider;
* a submission listener (STARTTLS) published on `smtp_port`;
* an account for the applications;
* the administrator password.

The web administration interface is exposed over plain HTTP on the internal port and is meant to be published through a [Caddy](caddy.md) HTTPS redirection at `self_url`: open `https://mail.mydomain.com/admin` and log in as `admin` with `admin_password`.

## Configuring the applications

Each application that sends mail is then configured with:

* **SMTP host:** `host.containers.internal`
* **Port:** `smtp_port`
* **Security:** STARTTLS. The certificate is self-signed, so enable the option of the application that skips certificate verification (`FORCE_TRUST_SERVER_CERT` in Forgejo, `EMAIL_SMTP_TLS_REJECT_UNAUTH=false` in Overleaf, *Ignore certificate errors* in Immich...).
* **Username** / **Password:** `sender.name` / `sender.password`
* **From address:** `sender.name@domain`. Stalwart rejects messages from any other address; the display name is free (`Forgejo <noreply@mydomain.com>`).

## DNS records

DNS records to publish at the DNS provider of the domain:

* **DKIM:** once the service is up, open *Management › Domains* in the web interface, then *View DNS Zone file* on the domain, and copy only the `_domainkey` TXT records. Do not import the whole file: the other records (MX, SPF, MTA-STS...) describe a full mail server hosted at home.
* **DMARC:** `_dmarc.mydomain.com. TXT "v=DMARC1; p=none; rua=mailto:postmaster@mydomain.com"`, tightened to `p=quarantine` once the reports show SPF and DKIM passing.
* **SPF:** no change. Messages leave from the provider, so the SPF record must include the provider, not the home IP address.
* **MX:** no change, incoming mail keeps going to the provider.

!!! note
    Mailbox providers usually require the From address to match the authenticated mailbox and cap the hourly volume (OVH: about 200 messages per hour). In that case set `sender.name` to the local part of the mailbox given in `relay.username`. Transactional services accept any address of a verified domain.

!!! note
    Stalwart checks passwords against a strength policy (zxcvbn score of at least 3); a weak `admin_password` or `sender.password` makes `stalwart-init.service` fail, with the reason in `journalctl --user -u stalwart-init.service`. The service can be started again once the password has been changed.

!!! note
    Automatic DKIM key rotation requires DNS management by Stalwart through the API of the DNS provider, which can be enabled later from the domain settings; until then the initial keys stay in use.

## `stalwart.image`

The image of Stalwart to deploy.

* **Type:** String
* **Example:** `docker.io/stalwartlabs/stalwart:v0.16`

## `stalwart.http_port`

Port to listen for HTTP requests (web administration interface).

* **Type:** Integer
* **Example:** `3012`

## `stalwart.smtp_port`

Port to listen for SMTP submissions from the applications (STARTTLS).

* **Type:** Integer
* **Example:** `2525`

## `stalwart.self_url`

Public hostname of the server.

* **Type:** String
* **Purpose:** Caddy route of the web interface, to which the web login is bound; also used in SMTP greetings and message headers.
* **Example:** `mail.mydomain.com`

## `stalwart.domain`

Mail domain of the applications, created in Stalwart with its DKIM keys.

* **Type:** String
* **Example:** `mydomain.com`

## `stalwart.admin_password`

Password of the `admin` account of the web interface.

* **Type:** String
* **Example:** `Sunny-Meadow-Cactus-42`

## `stalwart.relay`

Provider to which every message is handed.

### `stalwart.relay.host`

SMTP server of the mail provider.

* **Type:** String
* **Example:** `smtp.mail.ovh.net`

### `stalwart.relay.port`

Port of the provider's SMTP server: `465` for implicit TLS, any other value for STARTTLS.

* **Type:** Integer
* **Example:** `465`

### `stalwart.relay.username`

Username to authenticate with the provider, usually the full address of the mailbox.

* **Type:** String
* **Example:** `me@mydomain.com`

### `stalwart.relay.password`

Password to authenticate with the provider.

* **Type:** String
* **Purpose:** Passed to the container as an environment variable read by the relay route, so it can be changed without touching the database.
* **Example:** `<PROVIDER MAILBOX PASSWORD>`

## `stalwart.sender`

The Stalwart account used by the applications.

### `stalwart.sender.name`

Name of the account, whose address is `sender.name@domain`.

* **Type:** String
* **Purpose:** SMTP username of the applications and local part of their From address.
* **Example:** `noreply`

### `stalwart.sender.password`

Password of the account.

* **Type:** String
* **Example:** `Sunny-Meadow-Cactus-42`
