# `homeassistant`

Configuration for [Home Assistant](https://www.home-assistant.io/), the home automation hub, deployed as a pod that optionally bundles a Zigbee network: [Zigbee2MQTT](https://www.zigbee2mqtt.io/) drives a USB Zigbee coordinator (the "dongle") and publishes its devices to a [Mosquitto](https://mosquitto.org/) MQTT broker, from which Home Assistant picks them up. The Home Assistant interface is exposed on `http_port`, meant to be published through a [Caddy](caddy.md) site at `hostname`; the Zigbee2MQTT frontend on `zigbee2mqtt_port`.

Home Assistant keeps its configuration in `/home/u_homeassistant/config`. The template seeds it with the same `configuration.yaml` Home Assistant would generate, plus its `external_url`, and with the HTTP settings store (`.storage/http`) holding the reverse proxy settings it needs to accept requests from Caddy, as Home Assistant itself writes it once those settings are confirmed under *Settings › System › Network*. Everything else (account, location, integrations, automations) is set up from the web interface, starting with the onboarding page at `https://<hostname>`.

The Zigbee part is enabled by giving `zigbee_dongle`. The template then:

- installs a udev rule that recognizes the dongle by its USB vendor and product identifiers, hands it to `u_homeassistant`, labels it for containers and links it as `/dev/zigbee`, whatever `ttyACM`/`ttyUSB` number the kernel gave it;
- passes `/dev/zigbee` to the Zigbee2MQTT container, configured through environment variables (serial driver, MQTT broker at `localhost` inside the pod, frontend and Home Assistant discovery enabled). Zigbee2MQTT writes its own `configuration.yaml` in the `zigbee2mqtt-data` volume on first start, network keys included;
- runs Mosquitto with its stock configuration: anonymous access on port 1883, which only the containers of the pod can reach since the port is not published.

Once everything runs, add the **MQTT** integration in Home Assistant (*Settings › Devices & services › Add integration*), with broker `localhost` and port `1883`, no credentials. Zigbee2MQTT announces its devices to Home Assistant through that broker. Pair devices from the Zigbee2MQTT frontend (*Permit join*) or from the *Zigbee2MQTT Bridge* device in Home Assistant.

!!! note
    Podman fails to start the Zigbee2MQTT container while the dongle is unplugged, and retries every 10 seconds; Home Assistant and Mosquitto are not affected. Plugging the dongle after the fact is enough. On a running server where the template was applied with the ad hoc script, reload udev once so the rule applies to the already plugged dongle: `sudo udevadm control --reload && sudo udevadm trigger`.

!!! note
    Home Assistant trusts the `X-Forwarded-For` header of requests coming from any private address, as rootless Podman delivers Caddy's requests from the host's own address (or its gateway's). A machine on the LAN can thus spoof the client address Home Assistant records, which matters only for its login attempt bans. The Zigbee2MQTT frontend has no authentication at all: give its Caddy site the LAN-only `directives` of the example rather than a plain `port`.

!!! note
    The HTTP settings are not seeded through an `http:` block of `configuration.yaml` on purpose: since 2026.7 Home Assistant migrates such a block into a five-minute trial that reverts to the previous settings unless confirmed in the web interface, then ignores the block and reports it as a repair issue. Without the settings, every request coming through Caddy is answered `400 Bad Request`. Change them from *Settings › System › Network*, not from a YAML block.

!!! note
    Home Assistant discovers devices on the local network (Chromecast, HomeKit, Sonos, ESPHome...) by multicast, which does not cross the pod's network. Such devices can still be added by entering their address by hand. The Zigbee devices are not concerned, since they arrive through MQTT.

## `homeassistant.image`

The image of Home Assistant to deploy. Home Assistant releases a `YYYY.M` version every month, with breaking changes listed in its release notes; the example follows the patch releases of one month.

* **Type:** String
* **Example:** `ghcr.io/home-assistant/home-assistant:2026.9`

## `homeassistant.mosquitto_image`

The image of the Mosquitto MQTT broker between Zigbee2MQTT and Home Assistant. Only used when `zigbee_dongle` is set.

* **Type:** String
* **Example:** `docker.io/library/eclipse-mosquitto:2`

## `homeassistant.zigbee2mqtt_image`

The image of Zigbee2MQTT. Only used when `zigbee_dongle` is set.

* **Type:** String
* **Example:** `ghcr.io/koenkk/zigbee2mqtt:2`

## `homeassistant.http_port`

Port to listen for HTTP requests.

* **Type:** Integer
* **Example:** `3020`

## `homeassistant.zigbee2mqtt_port`

Port on which the Zigbee2MQTT frontend is published. Only used when `zigbee_dongle` is set.

* **Type:** Integer
* **Example:** `3021`

## `homeassistant.hostname`

Public host name of the service, given as `https://<hostname>` to Home Assistant as its external URL, used in the links it generates and by the mobile apps. It should match its [Caddy](caddy.md) site.

* **Type:** Fully qualified domain name
* **Example:** `ha.mydomain.com`

## `homeassistant.zigbee_dongle`

Model of the USB Zigbee coordinator plugged into the server. Leaving it out deploys Home Assistant alone, without Mosquitto and Zigbee2MQTT.

Every USB coordinator Zigbee2MQTT supports is wired the same way (a serial device passed to the container); the model only tells which USB devices to pick and which Zigbee2MQTT serial driver speaks to them. Supported values:

| Value | Stick | Radio | USB identifiers | Zigbee2MQTT adapter |
|-------|-------|-------|-----------------|---------------------|
| `CC2531` | the TI CC2531 dongle, USB on chip | CC2531 | `0451:16a8` | `zstack` |
| `CC2652P` | Sonoff ZBDongle-P, Nous E16, zzh!, slae.sh, SMLIGHT SLZB-02 and the other CC2652P/CC2652R sticks, which reach USB through a Silicon Labs CP210x or a WCH CH340 UART bridge | CC2652P/R | `10c4:ea60`, `1a86:7523` | `zstack` |
| `ZBDongle-E` | Sonoff Zigbee 3.0 USB Dongle Plus V2, CH9102F bridge, software flow control | EFR32MG21 | `1a86:55d4` | `ember` |
| `SkyConnect` | Home Assistant SkyConnect and its successor the Connect ZBT-1, CP2102N bridge, hardware flow control | EFR32MG21 | `10c4:ea60` | `ember`, `rtscts: true` |
| `SLZB-07` | SMLIGHT SLZB-07, CP2102N bridge, hardware flow control | EFR32MG21 | `10c4:ea60` | `ember`, `rtscts: true` |

The Silicon Labs sticks are keyed by model rather than by radio because they share the driver but not the serial flow control. To support another model, add it to the table at the top of `templates/homeassistant.yaml.j2` with its `lsusb` identifiers, its [adapter driver](https://www.zigbee2mqtt.io/guide/configuration/adapter-settings.html) and, for `ember`, its flow control.

!!! note
    The `ember` driver requires EmberZNet firmware 7.4 or newer on the stick. Early ZBDongle-E batches ship an older firmware: flash the stick from a workstation with the vendor's web flasher before plugging it into the server. Multiprotocol firmware (Zigbee and Thread on one radio) is not supported by Zigbee2MQTT, and Home Assistant recommends one radio per protocol.

!!! note
    Except for the CC2531, the identifiers are those of generic USB-UART bridges, found on many other boards (ESP32 development kits, some Z-Wave sticks...), and shared between sticks: a ZBDongle-P, a SkyConnect and a SLZB-07 all report `10c4:ea60`, only `zigbee_dongle` tells them apart. Every such device plugged into the server is handed to `u_homeassistant`, and the last one enumerated becomes `/dev/zigbee`. Keep the server free of other CP210x, CH340 and CH9102 devices, or narrow the udev rule with the stick's `ATTRS{product}` string (`udevadm info -a /dev/ttyUSB0` shows it).

* **Optional**
* **Type:** `CC2531`, `CC2652P`, `ZBDongle-E`, `SkyConnect` or `SLZB-07`
* **Example:** `CC2531`
