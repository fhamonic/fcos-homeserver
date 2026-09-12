# `adguardhome`

Configuration for the [AdGuard Home](https://adguard.com/adguard-home/overview.html) service, including networking and versioning.

AdGuard Home DNS and DHCP features are best suited to a **macvlan** network, where the container behaves as an independent device on the local network.

This allows AdGuard Home to bind to:

* Port **53** (DNS), which is already used by `systemd-resolved` on the FCOS host
* Port **67** (DHCP server)

Before enabling AdGuard Home's DHCP feature, you should disable any other DHCP server on your local network.

After AdGuard Home has issued IP leases to all local devices, you may re-enable another DHCP server on a **different IP range** as a fallback, in case the home server becomes unavailable.

Devices that already hold a lease will typically attempt to renew it from the same DHCP server at approximately **50% of the lease duration**. If that fails, they will behave like new devices at around **87.5% of the lease duration**, broadcasting a DHCP request and accepting the first valid offer received.

In practice, a locally hosted AdGuard Home instance often responds faster than ISP-provided routers, but this behavior should not be relied upon as a strict guarantee.

!!! note
    macvlan networks isolate containers from the host by default. The FCOS host will not be able to directly communicate with the AdGuard Home container unless [`enable_host_proxy`](#adguardhomeenable_host_proxy) is set.

This template is **rootful**: the container needs the `NET_ADMIN`, `NET_RAW` and `NET_BIND_SERVICE` capabilities and a macvlan network, so its units are installed under `/etc/containers/systemd/` and its data lives in `/var/adguardhome`.

## `adguardhome.image`

The image of AdGuard Home to deploy.

* **Type:** String
* **Example:** `docker.io/adguard/adguardhome:latest`

## `adguardhome.macvlan`

Macvlan network configuration allowing AdGuard Home to appear as a separate device on the LAN.

### `adguardhome.macvlan.interface`

The physical network interface used for the macvlan network.

* **Type:** String
* **Example:** `eth0`

### `adguardhome.macvlan.subnet`

The subnet assigned to the macvlan network.

* **Type:** CIDR notation string
* **Example:** `192.168.0.0/24`

### `adguardhome.macvlan.gateway`

The default gateway for the macvlan network.

* **Type:** IP address
* **Example:** `192.168.0.1`

## `adguardhome.ip`

Static IP address assigned to the AdGuard Home instance.

* **Type:** IP address
* **Example:** `192.168.0.10`

!!! note
    Ensure this IP is not and cannot be used by another device, e.g. it is not part of any DHCP IP range.

## `adguardhome.enable_host_proxy`

Whether to create a macvlan interface on the host itself, bridged on the same physical interface, so that the host can reach the AdGuard Home container (and use it as its DNS server). Without it, the kernel drops traffic between the host and its macvlan children.

* **Type:** Boolean
* **Example:** `true`

## `adguardhome.host_proxy`

Address of the host on that macvlan interface, in the macvlan subnet. Only read when `enable_host_proxy` is `true`.

* **Type:** IP address
* **Purpose:** Address from which the host talks to AdGuard Home; also the address the other services see it from.
* **Example:** `192.168.0.11`
