# `immich`

Configuration for the [Immich](https://immich.app/) photo management service, deployed as a pod: PostgreSQL (with the vector extensions Immich requires), Valkey, the optional machine learning service and the server.

## `immich.image`

The image of the Immich server to deploy.

* **Type:** String
* **Example:** `ghcr.io/immich-app/immich-server:v2`

## `immich.ml_image`

The image of the Immich machine learning service (face recognition, smart search). Omit it to not deploy the service.

* **Optional**
* **Type:** String
* **Example:** `ghcr.io/immich-app/immich-machine-learning:v2`

## `immich.postgres_image`

The image of PostgreSQL to deploy, including vector extension support. Use the image published by the Immich project, which pins the extensions to what the server version expects.

* **Type:** String
* **Example:** `ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0`

## `immich.valkey_image`

The image of Valkey (Redis-compatible datastore) to deploy.

* **Type:** String
* **Example:** `docker.io/valkey/valkey:8`

## `immich.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3006`

## `immich.db_storage_type`

Type of the disk holding the database and caches (the named volumes, on the system disk), **not** the photos. Immich tunes its database for it.

* **Type:** String
* **Values:** `SSD` or `HDD`

## `immich.photos_dir`

Directory of the host where the photos are stored, bind mounted into the server.

* **Type:** Absolute path
* **Example:** `/var/hdd/Photos`
