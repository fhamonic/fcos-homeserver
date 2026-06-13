import os
import questionary
import sys
import traceback
import yaml
from jinja2 import Template, StrictUndefined
from jinja2.exceptions import TemplateError


def handle_ch(element):
    if "user" in element:
        owner = element["user"]["name"]
        if "group" in element:
            owner += f":{element['group']['name']}"
        print(f"sudo chown {owner} {element['path']}")
    if "mode" in element:
        print(f"sudo chmod {oct(element['mode']).replace('o','')} {element['path']}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} metaconfig.yaml", file=sys.stderr)
        sys.exit(1)

    metaconfig_file = sys.argv[1]
    with open(metaconfig_file, "r") as file:
        file_config = yaml.safe_load(file)

    key = questionary.select(
        "Select a configuration:", choices=list(file_config.keys())
    ).ask()
    id = list(file_config.keys()).index(key) + 1

    template_file = f"{key}.yaml.j2"
    with open(os.path.join("templates", template_file), "r") as file:
        try:
            template = Template(file.read(), undefined=StrictUndefined)
            rendered = template.render({key: file_config[key]}, id=id)
            data = yaml.safe_load(rendered)
            if not isinstance(data, dict):
                raise ValueError(f"YAML root must be a dictionary in {file}")
        except TemplateError as e:
            for frame in traceback.extract_tb(e.__traceback__):
                if frame.filename in ["<template>", "<unknown>"]:
                    print(
                        f"{template_file}:{frame.lineno}: error: {e}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            raise e

    if "passwd" in data:
        if "groups" in data["passwd"]:
            for group in data["passwd"]["groups"]:
                print(f"sudo groupadd --gid {group['gid']} {group['name']}")
        if "users" in data["passwd"]:
            for user in data["passwd"]["users"]:
                print(
                    f"sudo useradd --password \"*\" --uid {user['uid']} --create-home {user['name']} --groups {','.join(user['groups'])}"
                )

    if "storage" in data:
        if "directories" in data["storage"]:
            for directory in data["storage"]["directories"]:
                print(f"sudo mkdir -p {directory['path']}")
                handle_ch(directory)

        if "files" in data["storage"]:
            for file in data["storage"]["files"]:
                if "contents" in file:
                    print(
                        f"echo \"{file['contents']['inline']}\" | sudo tee {file['path']}"
                    )
                else:
                    print(f"sudo touch {file['path']}")
                handle_ch(file)

        if "links" in data["storage"]:
            for link in data["storage"]["links"]:
                if link["hard"]:
                    print(f"sudo ln {link['target']} {link['path']}")
                    handle_ch(link)
                else:
                    print(f"sudo ln -s {link['target']} {link['path']}")
