# `immich`

Configuration for the [Immich](https://immich.app/) photo management service, deployed as a pod: PostgreSQL (with the vector extensions Immich requires), Valkey, the optional machine learning service and the server.

## `immich.postgres_image`

The image of PostgreSQL to deploy, including vector extension support. Use the image published by the Immich project, which pins the extensions to what the server version expects.

* **Type:** String
* **Example:** `ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0`

## `immich.valkey_image`

The image of Valkey (Redis-compatible datastore) to deploy.

* **Type:** String
* **Example:** `docker.io/valkey/valkey:8`

## `immich.immich_ml_image`

The image of the Immich Machine Learning service to deploy.
This may be omitted to disable the feature.

* **Optional**
* **Type:** String
* **Example:** `ghcr.io/immich-app/immich-machine-learning:v2`

## `immich.immich_image`

The image of the Immich server to deploy.

* **Type:** String
* **Example:** `ghcr.io/immich-app/immich-server:v2`

## `immich.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3006`

## `immich.host_drive_type`

Type of host storage used for metadata (e.g. database and cache), **not** photos.

* **Type:** String
* **Values:** `SSD` or `HDD`

## `immich.photos_volume`

The directory to bind mount where photos are stored.

* **Type:** Absolute path
* **Example:** `/var/hdd/Photos`
