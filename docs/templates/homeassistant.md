# `homeassistant`

Configuration for [Home Assistant](https://www.home-assistant.io/), the home automation hub, deployed as a pod that optionally bundles a Zigbee network: [Zigbee2MQTT](https://www.zigbee2mqtt.io/) drives a USB Zigbee coordinator (the "dongle") and publishes its devices to a [Mosquitto](https://mosquitto.org/) MQTT broker, from which Home Assistant picks them up. The Home Assistant interface is exposed on `http_port`, meant to be published through a [Caddy](caddy.md) site at `hostname`; the Zigbee2MQTT frontend on `zigbee2mqtt_port`.

Home Assistant keeps its configuration in `/home/u_homeassistant/config`. The template seeds it with the same `configuration.yaml` Home Assistant would generate, plus its `external_url`, and with the HTTP settings store (`.storage/http`) holding the reverse proxy settings it needs to accept requests from Caddy, as Home Assistant itself writes it once those settings are confirmed under *Settings › System › Network*. Everything else (account, location, integrations, automations) is set up from the web interface, starting with the onboarding page at `https://<hostname>`.

The Zigbee part is enabled by giving `zigbee_dongle`. The template then:

- installs a udev rule that recognizes the dongle by its USB vendor and product identifiers, hands it to `u_homeassistant`, labels it for containers and links it as `/dev/zigbee`, whatever `ttyACM`/`ttyUSB` number the kernel gave it;
- passes `/dev/zigbee` to the Zigbee2MQTT container, configured through environment variables (serial driver, MQTT broker at `localhost` inside the pod, frontend and Home Assistant discovery enabled). Zigbee2MQTT writes its own `configuration.yaml` in the `zigbee2mqtt-data` volume on first start, network keys included;
- runs Mosquitto with its stock configuration: anonymous access on port 1883, which only the containers of the pod can reach since the port is not published.

Once everything runs, add the **MQTT** integration in Home Assistant (*Settings › Devices & services › Add integration*), with broker `localhost` and port `1883`, no credentials. Zigbee2MQTT announces its devices to Home Assistant through that broker: a *Zigbee2MQTT Bridge* device appears under the integration at once, and each paired device follows by itself. Nothing else is configured on the Home Assistant side; in particular, its *Add device* button does not pair Zigbee devices.

Pairing happens in Zigbee2MQTT, whose frontend is reachable on the LAN at `http://<server>:<zigbee2mqtt_port>` even without a Caddy site. Before the first device, set the Zigbee channel under *Settings › Advanced* and restart from the frontend's menu: the default channel 11 overlaps Wi-Fi channel 1 and is the most crowded, 25 overlaps the least. Changing it later means re-pairing some devices. Then click *Permit join (All)*, which opens the network for about four minutes, and put the device in pairing mode with the gesture of its manual (typically holding its button five seconds until its LED blinks slowly). It shows up in the *Devices* tab, first as "interviewing", then with its model. The *Zigbee2MQTT Bridge* device in Home Assistant exposes the same *Permit join* switch. Install codes are not needed for ordinary Zigbee 3.0 devices.

To check the chain, from the udev rule to Home Assistant:

```bash
ls -lZ /dev/zigbee /dev/ttyUSB0 /dev/ttyACM0
sudo machinectl shell u_homeassistant@ /bin/bash -c 'journalctl --user -u homeassistant-zigbee2mqtt.service -n 40 --no-pager'
```

The device node must belong to `u_homeassistant` with the `container_file_t` label. The log must show "Serialport opened", a "Coordinator firmware version" line, "Connected to MQTT server" and "Zigbee2MQTT started!"; a join attempt then logs the device's address and its interview. On the Home Assistant side, the MQTT integration's *Configure* page can *Listen to a topic*: `zigbee2mqtt/bridge/state` answers a retained `{"state":"online"}` at once when the broker settings are right.

Everything to keep is in the `zigbee2mqtt-data` volume: the configuration with the network keys, the coordinator backup and the database of paired devices. Home Assistant's own state is in `/home/u_homeassistant/config`.

!!! note
    The coordinator firmware a dongle ships with can be years behind the one the [Zigbee2MQTT adapter page](https://www.zigbee2mqtt.io/guide/adapters/) links for it; the "Coordinator firmware version" log line gives its date. Flashing it takes a minute from a laptop with the vendor's web flasher, and is best done before pairing anything. A re-flash empties the coordinator, and Zigbee2MQTT then has to form the network again, the one moment it transmits at full power on a fresh coordinator; on a USB port with a weak supply it can hang there for good, logging "network commissioning timed out" at every start. The way out is to form the network on a workstation: run the Zigbee2MQTT image against the stick with a copy of the server's `configuration.yaml` (which carries the network keys once Zigbee2MQTT has run once), wait for "Zigbee2MQTT started!", stop it, and move the stick back; the server then resumes the network instead of forming it. Range and joining problems are otherwise most often a matter of interference: put the dongle on a short USB extension cable, away from USB 3 ports, SSDs and Wi-Fi access points, and pair devices within a metre of it first. A device that was paired to another hub keeps that network until factory reset, and never shows up otherwise.

!!! note
    Podman fails to start the Zigbee2MQTT container while the dongle is unplugged, and retries every 10 seconds; Home Assistant and Mosquitto are not affected. Plugging the dongle after the fact is enough. On a running server where the template was applied with the ad hoc script, reload udev once so the rule applies to the already plugged dongle: `sudo udevadm control --reload && sudo udevadm trigger`.

!!! note
    Home Assistant trusts the `X-Forwarded-For` header of requests coming from any private address, as rootless Podman delivers Caddy's requests from the host's own address (or its gateway's). A machine on the LAN can thus spoof the client address Home Assistant records, which matters only for its login attempt bans. The Zigbee2MQTT frontend has no authentication by default, so anyone on the LAN can open the network for joining: give its Caddy site the LAN-only `directives` of the example rather than a plain `port`, and set an *Auth token* under its *Settings › Frontend* if the LAN is not trusted either.

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
