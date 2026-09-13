# `homeassistant`

Configuration for [Home Assistant](https://www.home-assistant.io/), the home automation hub, deployed as a pod that optionally bundles a Zigbee network: [Zigbee2MQTT](https://www.zigbee2mqtt.io/) drives a USB Zigbee coordinator (the "dongle") and publishes its devices to a [Mosquitto](https://mosquitto.org/) MQTT broker, from which Home Assistant picks them up. The Home Assistant interface is exposed on `http_port`, meant to be published through a [Caddy](caddy.md) site at `hostname`; the Zigbee2MQTT frontend on `zigbee2mqtt_port`.

Home Assistant keeps its configuration in `/home/u_homeassistant/config`. The template seeds it with the same `configuration.yaml` Home Assistant would generate, plus the reverse proxy settings it needs to accept requests from Caddy; everything else (account, location, integrations, automations) is set up from the web interface, starting with the onboarding page at `https://<hostname>`.

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

Every USB coordinator Zigbee2MQTT supports is wired the same way (a serial device passed to the container); the model only tells which USB device to pick and which Zigbee2MQTT serial driver speaks to it. Supported values:

| Value | USB identifiers | Zigbee2MQTT adapter |
|-------|-----------------|---------------------|
| `CC2531` | `0451:16a8` | `zstack` |

To support another model, add it to the table at the top of `templates/homeassistant.yaml.j2` with its `lsusb` identifiers and its [adapter driver](https://www.zigbee2mqtt.io/guide/configuration/adapter-settings.html).

* **Optional**
* **Type:** Enumerated string
* **Example:** `CC2531`
