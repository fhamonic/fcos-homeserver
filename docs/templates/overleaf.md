# `overleaf`

Configuration for the [Overleaf](https://github.com/overleaf/overleaf) (ShareLaTeX) service, deployed as a pod of three containers: MongoDB, Redis and the application. A one-shot unit initializes the MongoDB replica set at first boot.

## `overleaf.mongo_image`

The image of MongoDB used by Overleaf.

* **Type:** String
* **Example:** `docker.io/mongo:8.0`

## `overleaf.redis_image`

The image of Redis used by Overleaf.

* **Type:** String
* **Example:** `docker.io/library/redis:7.4`

## `overleaf.sharelatex_image`

The image for the Overleaf application (named ShareLaTeX for historical reasons).

* **Type:** String
* **Example:** `docker.io/rigon/sharelatex-full:6.0.0`

## `overleaf.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3004`

## `overleaf.app_name`

Display name of the Overleaf instance.

* **Type:** String
* **Example:** `My Overleaf`

## `overleaf.self_url`

Public URL advertised by Overleaf to clients.

* **Type:** Domain name
* **Example:** `overleaf.mydomain.com`

## `overleaf.admin_email`

Administrator email login for Overleaf.
After the first boot, you have to log in as the `u_overleaf` user (see [Maintenance](../getting-started/maintenance.md#service-users)) and run:

```bash
./create_admin.sh
```

Then Ctrl+click or go to the generated URL and set a password.
Additional users can then be created from the Overleaf dashboard.

* **Type:** Email address
* **Purpose:** Used for system notifications and administrative access.
