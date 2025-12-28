# Fedora CoreOS Home Server

This project explores a pragmatic way to use Fedora CoreOS (FCOS) as a "set-and-forget" home server by lowering the barrier to its initial provisioning, while staying aligned with FCOS design principles.

It consists of:
- A set of **Jinja2 templates** describing self-contained services (storage, reverse proxy, applications).
- A single `metaconfig.yaml` that declaratively selects and parametrizes those templates.
- A `build_config.py` script that renders and merges the templates into a valid Butane configuration, which is then consumed by the standard FCOS installation workflow.

## Why Fedora CoreOS?

Fedora CoreOS is primarily known as a building block for container platforms in enterprise environments. That background is precisely what makes it attractive for a long-lived home server:

- **Immutable OS**: 
	- The base system is read-only and versioned.
	- Configuration drift and vulnerabilities are minimized.
- **Reproducibility**: 
	- All configuration is done at first boot using a configuration file.
	- Manual configuration through SSH should be exceptional.
- **Optimized for Containers**:
	- The OS provides a minimal, container-focused userland.
	- Podman is the default container runtime, rootless mode is well supported.
	- systemd Quadlet is a first-class mechanism for managing containers as services.
- **Automatic, transactional updates**:
	- OS updates are applied atomically and rolled back automatically on failure
	- No manual maintenance is expected.

The main barrier to entry therefore remains the initial configuration, which is the purpose of this project.

## Getting started

**1.** Edit `metaconfig.yaml`
- Each top-level key corresponds to a service or feature implemented as a template.
- Remove unwanted keys.
- Fill in the parameters for the ones you keep (cf. [Templates documentation](https://github.com/fhamonic/fcos-homeserver/wiki/Templates)).

**2.** Generate the Butane configuration
```bash
python build_config.py
```

**3.** Proceed with the standard FCOS installation workflow

- Convert the configuration from Butane to Ignition and host it on the network :
```bash
docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign && python -m http.server 8000
```
- Boot the Fedora CoreOS Live USB and install (replace xxx as appropriate):
```bash
sudo coreos-installer install /dev/xxx --ignition-url http://192.168.xxx.xxx:8000/config.ign --insecure-ignition && sudo reboot
```

> For maintenance and debugging instructions you can reffer to the [Maintenance documentation](https://github.com/fhamonic/fcos-homeserver/wiki/Maintenance)

## Documentation and scope

This repository focuses on providing a reproducible entry point into Fedora CoreOS–based home servers.
It is intentionally opinionated and closely follows FCOS design principles.

Before adapting this project to your own setup, it is recommended to [review the wiki](https://github.com/fhamonic/fcos-homeserver/wiki) to understand the design choices and how the generated configuration maps to Fedora CoreOS, Ignition, systemd, and Podman.
