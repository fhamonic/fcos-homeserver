# `livesync`

Configuration for the CouchDB backend of the [Obsidian Self-hosted LiveSync](https://github.com/vrtmrz/obsidian-livesync) plugin.

The plugin synchronizes Obsidian vaults between devices through a CouchDB database.
This template deploys a single CouchDB container, applies the settings expected by the plugin (mandatory authentication, CORS for the Obsidian desktop and mobile apps, raised request and document size limits) and creates the vault database at first boot, so the upstream initialization script does not need to be run.

CouchDB is exposed over plain HTTP on the internal port and is meant to be published through a [Caddy](caddy.md) HTTPS redirection.

Once the server is up, in Obsidian, install the **Self-hosted LiveSync** community plugin and enter the remote database settings:

* **URI:** `https://livesync.mydomain.com` (the Caddy route)
* **Username** / **Password:** as configured below
* **Database name:** as configured below

Enabling **End-to-End Encryption** with a passphrase is recommended since the vault content is otherwise stored in clear on the server.

!!! note
    The credentials below are those of the CouchDB administrator account, which is also the account used by the plugin, as in the upstream setup guide.

## `livesync.image`

The image of CouchDB to deploy.

* **Type:** String
* **Example:** `docker.io/library/couchdb:3.5`

## `livesync.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3010`

## `livesync.username`

Username of the CouchDB administrator account.

* **Type:** String
* **Purpose:** Used by the Obsidian plugin to authenticate.
* **Example:** `admin`

## `livesync.password`

Password of the CouchDB administrator account.

* **Type:** String
* **Purpose:** Used by the Obsidian plugin to authenticate.
* **Example:** `L0NgP@SsW0rD`

## `livesync.database`

Name of the CouchDB database holding the vault, created automatically at first boot.
One database can hold one vault; additional vaults require additional databases, which can be created from the CouchDB web interface at `https://livesync.mydomain.com/_utils`.

* **Type:** String
* **Example:** `obsidiannotes`
