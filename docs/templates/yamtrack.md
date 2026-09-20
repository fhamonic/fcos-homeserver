# `yamtrack`

Configuration for [Yamtrack](https://github.com/FuzzyGrim/Yamtrack), a media tracker for movies, TV shows, anime, manga, video games, books, comics and board games: each user keeps a score, a status, a progress and a history per title, with a calendar of upcoming releases, personal lists and imports from Trakt, Simkl, MyAnimeList, AniList and Kitsu. The template deploys a pod with the application (nginx, gunicorn and the Celery workers in one container) and its Redis cache, exposed over plain HTTP on `http_port` and meant to be published through a [Caddy](caddy.md) site at `hostname`. The database is SQLite, the upstream default, kept in the `db` volume.

Nobody can register by themselves: the template creates the `admin_username` account at first start, and further accounts are created from the Django administration interface at `https://<hostname>/admin/` (*Users › Add*). The metadata comes from public APIs (TMDB, MyAnimeList, IGDB, Hardcover, ComicVine) with keys built into the image; the [environment variables page](https://fuzzygrim.github.io/Yamtrack/release/env-variables/) of Yamtrack lists how to give your own when the shared ones hit their rate limits.

!!! note
    The administration interface is reachable from anywhere the Caddy site is, protected by the administrator's password only. To keep it on the LAN, give the Caddy site `directives` instead of a plain `port`:

    ```yaml
    - hostname: yamtrack.mydomain.com
      directives: |
        @admin_public {
            path /admin*
            not remote_ip 192.168.0.0/24
        }
        respond @admin_public 403
        reverse_proxy host.containers.internal:3022
    ```

Everything to keep is in the `db` volume (the Redis volume only holds the metadata cache and the queue of the background tasks). Yamtrack also exports every user's tracked media as a CSV file from its settings page, which it can import back.

## `yamtrack.image`

The image of Yamtrack to deploy.

* **Type:** String
* **Example:** `ghcr.io/fuzzygrim/yamtrack:0.26`

## `yamtrack.redis_image`

The image of the Redis cache and task queue of the pod.

* **Type:** String
* **Example:** `docker.io/library/redis:8-alpine`

## `yamtrack.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3022`

## `yamtrack.hostname`

Public host name of the service, given as `https://<hostname>` to Yamtrack, which only accepts requests and form submissions for that origin. It should match its [Caddy](caddy.md) site.

* **Type:** Fully qualified domain name
* **Example:** `yamtrack.mydomain.com`

## `yamtrack.secret_key`

Key with which Yamtrack signs the sessions and the tokens it hands out (Django's `SECRET_KEY`). Changing it logs every user out.

* **Type:** String
* **Purpose:** Any long random string, kept across reprovisioning.
* **Example:** `<LONG RANDOM STRING>`

## `yamtrack.admin_username`

Username of the administrator account, created at first start.

* **Type:** String
* **Example:** `admin`

## `yamtrack.admin_password`

Password of the administrator account.

* **Type:** String
* **Purpose:** Logging in to Yamtrack and to the administration interface at `/admin/`, where the other accounts are created.
* **Example:** `L0NgP@SsW0rD`

## `yamtrack.timezone`

Time zone of the server (its `TZ`), used for the calendar and the dates of the tracking history of every user. UTC when left out.

* **Optional**
* **Type:** [tz database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
* **Example:** `Europe/Paris`
