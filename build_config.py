import os
import shutil
import subprocess
import sys
import traceback
import yaml
from jinja2 import Template, StrictUndefined
from jinja2.exceptions import TemplateError


# Recursively merge two dictionaries. Lists are appended, scalars must match.
def merge_dicts(a, b, path=[]):
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
                continue
            if isinstance(a[key], list) and isinstance(b[key], list):
                a[key] += b[key]
                continue
            if a[key] != b[key]:
                conflict_path = ".".join(path + [str(key)])
                raise ValueError(f"Conflict at '{conflict_path}': {a[key]} != {b[key]}")
        else:
            a[key] = b[key]
    return a


# A bad calendar expression only shows on the server, as a timer that refuses
# to load, so check it here when the build machine has systemd.
def check_auto_update(key, block, template_source):
    if not isinstance(block, dict) or "auto_update" not in block:
        return
    value = block["auto_update"]
    if "auto_update" not in template_source:
        sys.exit(f"{key}.auto_update: this template runs on the shared system "
                 f"timer and takes no schedule of its own")
    if not isinstance(value, str):
        sys.exit(f"{key}.auto_update: expected a systemd calendar expression "
                 f"(a string), got {value!r}; leave the key out for the daily default")
    if shutil.which("systemd-analyze") is None:
        return
    result = subprocess.run(["systemd-analyze", "calendar", value],
                            capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"{key}.auto_update: {(result.stderr or result.stdout).strip()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} metaconfig.yaml",
                            file=sys.stderr)
        sys.exit(1)

    metaconfig_file = sys.argv[1]
    with open(metaconfig_file, "r") as file:
        file_config = yaml.safe_load(file)

    merged_dict = {}
    for id, key in enumerate(file_config.keys(), 1):
        template_file = f"{key}.yaml.j2"
        with open(os.path.join("templates", template_file), "r") as file:
            template_source = file.read()
        check_auto_update(key, file_config[key], template_source)
        try:
            template = Template(template_source, undefined=StrictUndefined)
            rendered = template.render({key: file_config[key]}, id=id)
            data = yaml.safe_load(rendered)
            if not isinstance(data, dict):
                raise ValueError(f"YAML root must be a dictionary in {template_file}")
            merged_dict = merge_dicts(merged_dict, data)
        except TemplateError as e:
            for frame in traceback.extract_tb(e.__traceback__):
                if frame.filename in ["<template>", "<unknown>"]:
                    print(
                        f"{template_file}:{frame.lineno}: error: {e}",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            raise e

    output_file = "config.bu"
    with open(output_file, "w") as f:
        yaml.dump(merged_dict, f, default_flow_style=False)
    print(f"Configuration built to {output_file}")
