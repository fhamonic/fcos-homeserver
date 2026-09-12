# `prometheus`

Configuration for [Prometheus](https://prometheus.io/), a metrics collector and time series database. Each job of `prometheus.jobs` scrapes a static list of `host:port` targets over HTTP (`/metrics` by default) every `scrape_interval`, and the samples are kept for `retention` in a named volume. Prometheus also scrapes itself. The generated `/home/u_prometheus/config/prometheus.yml` is bind-mounted read-only into the container: edit it as `u_prometheus` and Prometheus re-reads it within 30 seconds, no restart needed.

Its purpose in this repository is to feed the [Homepage](homepage.md) dashboard: a `prometheus` entry in `homepage.services` shows the targets up and down, and an entry of `homepage.custom_services` with a `prometheusmetric` widget displays the result of any PromQL query, for any application exposing metrics (see there).

!!! note
    Prometheus has no authentication and its web interface lets anyone query the collected data. Homepage reaches it on `host.containers.internal:<http_port>` without any Caddy route, so either do not publish it at all or use a [`custom` route](caddy.md#caddyhttps_redirectionscustom) restricted to the local network, as in the example `metaconfig.yaml` (`@public not remote_ip 192.168.0.0/24` followed by `respond @public 403`).

## `prometheus.image`

The image of Prometheus to deploy.

* **Type:** String
* **Example:** `docker.io/prom/prometheus:v3`

## `prometheus.http_port`

Port to listen for HTTP requests (web interface and API).

* **Type:** Integer
* **Example:** `3013`

## `prometheus.retention`

How long samples are kept before being deleted from the data volume.

* **Type:** String (Prometheus duration: `y`, `w`, `d`, `h`, `m`, `s`)
* **Example:** `30d`

## `prometheus.scrape_interval`

Interval between two scrapes of a target, for the jobs that do not set their own.

* **Type:** String (Prometheus duration)
* **Example:** `15s`

## `prometheus.jobs`

Scrape jobs, one per monitored application. Each job has a `name` (the `job` label of its series) and a list of `targets` (`host:port`). An optional `labels` map is attached to every series of the job, and any other key is copied as-is into the generated `scrape_config` (`scrape_interval`, `metrics_path`, `scheme`, `basic_auth`, `params`..., see the [Prometheus configuration reference](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config)).

* **Type:** List of maps
* **Example:**

    ```yaml
    jobs:
      - name: vllm
        targets:
          - 192.168.0.27:8000
        scrape_interval: 5s
    ```
