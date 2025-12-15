# Fedora CoreOS Homeserver

A modern, rootless Podman homeserver template for Fedora CoreOS using Quadlet and declarative configuration.

## Edit metaconfig.yaml to your needs

## Generate the Ignition configuration

	python build_config.py
	docker run --interactive --rm quay.io/coreos/butane:release --pretty --strict < config.bu > config.ign
	python -m http.server 8000

## Boot the Fedora CoreOS Live USB and install

    sudo coreos-installer install /dev/xxx --ignition-url http://192.168.xxx.xxx:8000/config.ign --insecure-ignition
    sudo reboot
