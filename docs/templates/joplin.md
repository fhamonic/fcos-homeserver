# `joplin`

Configuration for the [Joplin Server](https://joplinapp.org/help/apps/sync/#joplin-server), the synchronization backend of the Joplin note-taking apps, deployed as a pod with its PostgreSQL database.

## `joplin.image`

The image of Joplin Server to deploy.

* **Type:** String
* **Example:** `docker.io/joplin/server:3.5`

## `joplin.postgres_image`

The image of PostgreSQL used by Joplin.

* **Type:** String
* **Example:** `docker.io/postgres:16`

## `joplin.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3007`

## `joplin.hostname`

Public host name of the service, used as `https://<hostname>` in the links Joplin generates. It should match its [Caddy](caddy.md) site.

* **Type:** Fully qualified domain name
* **Example:** `joplin.mydomain.com`
