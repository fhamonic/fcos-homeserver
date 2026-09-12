# `homepage`

Configuration for [Homepage](https://gethomepage.dev/), a static dashboard that lists your services, bookmarks and status widgets. The container runs as the image's unprivileged `node` user, mapped to `u_homepage` on the host. Its configuration directory is `/home/u_homepage/config`: Homepage fills it with default `settings.yaml`, `services.yaml`, `bookmarks.yaml` and `widgets.yaml` files on first start, and changes made there as `u_homepage` are applied live without a restart. Expose it through Caddy with a [`caddy.sites`](caddy.md#caddysites) entry pointing at `homepage.http_port`, and list that host name in `homepage.allowed_hosts`.

!!! note
    Homepage has no authentication of its own. Only expose it behind Caddy on a host name you control, and keep widget API keys in `homepage.environment` (as `HOMEPAGE_VAR_*` variables referenced from the YAML files) rather than in the config files themselves. The Docker socket integration is not supported here: a rootless Podman socket would only see the Homepage container, so use each service's API integration instead.

## `homepage.image`

The image of Homepage to deploy.

* **Type:** String
* **Example:** `ghcr.io/gethomepage/homepage:v1`

## `homepage.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3011`

## `homepage.allowed_hosts`

Host names Homepage accepts requests for, joined into the required `HOMEPAGE_ALLOWED_HOSTS` variable. Include the Caddy site's host name and, if you access it directly, `<server-ip>:<http_port>`.

* **Type:** List of strings
* **Example:** `[home.mydomain.com, 192.168.0.11:3011]`

## `homepage.environment`

Optional extra environment variables passed to the container, typically `HOMEPAGE_VAR_*` secrets referenced as `{{HOMEPAGE_VAR_*}}` in the YAML configuration files.

* **Optional**
* **Type:** Map of string to string
* **Purpose:** Keep API tokens out of the configuration directory.
* **Example:** `{ HOMEPAGE_VAR_JELLYFIN_KEY: <MY API TOKEN> }`

## `homepage.services`

Services of this repository to list on the dashboard, each with its status widget. The key is the template name (`adguardhome`, `forgejo`, `immich`, `jellyfin`, `prometheus`, `wg_easy`): the widget type, icon and description come from a built-in catalog. `href` is the link of the tile and `port` the `http_port` of the service, reached as `host.containers.internal:<port>` (or give a complete `url`). The tile can be adjusted with `name`, `group` (`Services` by default), `icon` and `description`; every other key (`key`, `username`, `password`, `fields`...) is passed through to the [widget](https://gethomepage.dev/widgets/) as-is.

* **Type:** Map of maps
* **Example:**

    ```yaml
    services:
      jellyfin:
        href: https://jellyfin.mydomain.com
        port: 3002
        key: <JELLYFIN API KEY>
      prometheus:
        href: https://prometheus.mydomain.com
        port: 3013
    ```

## `homepage.custom_services`

Additional tiles written in Homepage's own [service format](https://gethomepage.dev/configs/services/): a `name`, an optional `group` (`Services` by default) and any service key (`href`, `icon`, `description`, `siteMonitor`, `widget`...), copied verbatim into `services.yaml`. Combined with the [Prometheus](prometheus.md) template, a `prometheusmetric` widget displays any PromQL query on any application that exposes metrics.

* **Type:** List of maps
* **Example:**

    ```yaml
    custom_services:
      - name: vLLM
        group: Workstation
        href: http://192.168.0.27:8000/v1/models
        icon: mdi-brain
        description: Qwen3.8-27B
        widget:
          type: prometheusmetric
          url: http://host.containers.internal:3013
          metrics:
            - label: Running / waiting
              query: vllm:num_requests_running + vllm:num_requests_waiting
            - label: KV cache used
              query: vllm:kv_cache_usage_perc
              format: { type: number, scale: 100, suffix: " %" }
    ```
