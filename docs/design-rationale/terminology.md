# Terminology

The templates share a small vocabulary for their parameters, so that a name read in one block of `metaconfig.yaml` means the same thing in every other block. The rules below are the ones the existing templates follow; a new template picks its names here before inventing one, and a name that fits none of the rules is a sign that the parameter needs a second look.

Names are `snake_case`. A parameter says what the value *is* (`hostname`, `photos_dir`), not what the template does with it (`enable_...`, `use_...`).

## Images

- **`image`** is the image of the service itself, as a full reference (`registry/namespace/name:tag`). Every service template has one, whether it deploys a single container or a pod. Prefer a major or major.minor tag to `latest`, since `AutoUpdate=registry` follows the tag.
- **`<component>_image`** is the image of a companion container of a pod, named after the component and not after the service: `postgres_image`, `mongo_image`, `redis_image`, `valkey_image`, `ml_image`.

## Ports

- **`http_port`** is the port on which the HTTP interface of the service is published on the host. It is unique across the file: Caddy, Homepage and Prometheus reach the service as `host.containers.internal:<http_port>`, and nothing is reachable from the internet without a Caddy site pointing at it. The examples use the `30xx` range, one port per template in file order.
- **`<protocol>_port`** is any other published port, named after its protocol: `https_port`, `ssh_port`, `smtp_port`, `wireguard_port`.
- **`port`**, inside an entry that points at another service of the file (`caddy.sites[]`, `homepage.services.*`), is the `http_port` of that service.

## Addresses

- **`hostname`** is the fully qualified domain name under which a service is reached from outside, that is the `hostname` of its Caddy site: `jellyfin.mydomain.com`. It carries no scheme and no port; where the application expects a URL, the template prepends `https://`.
- **`host`** is a machine to connect to, given as a host name or an IP address: the endpoint of the VPN in `wg_easy.host`, the SMTP server of the provider in `stalwart.relay.host`.
- **`ip`** and **`<role>_ip`** are IP addresses: `adguardhome.ip` for the container, `adguardhome.host_proxy_ip` for the proxy interface that puts the host on the same network.
- **`domain`** is a DNS domain rather than a host, such as the part of a mail address after the `@` in `stalwart.domain`.

## Credentials

- **`admin_username`** and **`admin_password`** are the credentials of the first administrator account, created at first start. When the application identifies accounts by email, the username is **`admin_email`**; when it fixes the administrator's name (Stalwart's `admin`), only `admin_password` exists.
- Accounts for a specific purpose are a nested block named after their role, with **`username`** and **`password`** inside, plus **`host`** and **`port`** when the account is used on another machine: `stalwart.relay` (the provider's mailbox), `stalwart.sender` (the account the applications send with).
- Credentials between the containers of one pod are not parameters at all: they are hard-coded in the template and never reachable from outside the pod.

## Storage

- **`<content>_dir`** is the absolute path of a directory on the host, bind mounted into the container: `immich.photos_dir`. On Fedora CoreOS it lives under `/var`, typically on an [ext4 drive](../templates/ext4_drives.md).
- **`<content>_volumes`** is a list of bind mounts written in Podman's `host:container:options` syntax, for services whose libraries are several directories: `jellyfin.media_volumes`.
- **`mount_point`** is where a drive is mounted, and **`placeholder_dirs`** the names of directories created under it.

## Optional parameters

An optional feature is enabled by giving its parameter and disabled by leaving it out, never by a boolean next to the value: the machine learning service of Immich exists when `immich.ml_image` is set, the host-side macvlan interface of AdGuard Home when `adguardhome.host_proxy_ip` is set. The template guards the corresponding units with `{% if key.x is defined %}`, and the documentation marks the parameter **Optional**.

## Pass-through blocks

Where a template wraps a configuration format of the application itself, the keys are those of the application and are not renamed: the widget keys of `homepage.services.*` and `homepage.custom_services[]`, the `scrape_config` keys of `prometheus.jobs[]`, the `HOMEPAGE_*` variables of `homepage.environment`, the Caddyfile lines of `caddy.sites[].directives`. Their documentation links the upstream reference instead of repeating it.
