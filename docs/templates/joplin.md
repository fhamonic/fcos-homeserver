# `joplin`

Configuration for the [Joplin Server](https://joplinapp.org/help/apps/sync/#joplin-server), the synchronization backend of the Joplin note-taking apps, deployed as a pod with its PostgreSQL database.

## `joplin.postgres_image`

The image of PostgreSQL used by Joplin.

* **Type:** String
* **Example:** `docker.io/postgres:16`

## `joplin.joplin_image`

The image of the Joplin Server application.

* **Type:** String
* **Example:** `docker.io/joplin/server:3.5`

## `joplin.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3007`

## `joplin.self_url`

Public URL advertised by Joplin to clients.

* **Type:** Domain name
* **Example:** `joplin.mydomain.com`
