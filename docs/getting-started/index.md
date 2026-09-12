# Installation

The whole provisioning happens at first boot: you describe the server in `metaconfig.yaml`, render it into a Butane configuration, and hand that configuration to the standard Fedora CoreOS installer. Nothing has to be configured over SSH afterwards.

## 1. Edit `metaconfig.yaml`

- Each top-level key corresponds to a service or feature implemented as a template.
- Remove the keys you do not want.
- Fill in the parameters of the ones you keep, as described in the [templates documentation](../templates/index.md).

The [`core`](../templates/core.md) key is mandatory: without an authorized SSH key there is no way to administer the server.

!!! tip
    Keep the file with your real secrets out of version control. The repository ignores `secret.yaml` for that purpose, and the scripts accept any file name.

## 2. Generate the Butane configuration

```bash
python build_config.py metaconfig.yaml
```

This renders one template per key of `metaconfig.yaml`, merges the results and writes `config.bu`. Rendering stops with the template file and line number on the first missing or misspelled parameter.

## 3. Proceed with the standard FCOS installation workflow

Convert the configuration from Butane to Ignition and host it on the local network:

```bash
docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign && python -m http.server 8000
```

Boot the [Fedora CoreOS live ISO](https://fedoraproject.org/coreos/download) on the server and install, replacing the device and the address of the machine hosting the file as appropriate:

```bash
sudo coreos-installer install /dev/xxx --ignition-url http://192.168.xxx.xxx:8000/config.ign --insecure-ignition && sudo reboot
```

The server provisions itself during the first boot. Container images are pulled at that point, so the first start of each service takes a few minutes.

!!! note
    If you reprovision several times, comment out the [Caddy HTTPS redirections](../templates/caddy.md#caddyhttps_redirections) in between: each installation requests new certificates, and too many requests get the address rate limited by Let's Encrypt.

## Next steps

- [Maintenance](maintenance.md) explains how to log in, check services and read their logs.
- The [design rationale](../design-rationale.md) describes what the generated configuration puts on the system.
