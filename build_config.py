import os
import yaml
from jinja2 import Template, StrictUndefined


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


with open("metaconfig.yaml", "r") as file:
    file_config = yaml.safe_load(file)

output_file = "config.bu"
merged_dict = {}
for id, key in enumerate(file_config.keys()):
    with open(os.path.join("templates", f"{key}.yaml.j2"), "r") as file:
        template = Template(file.read(), undefined=StrictUndefined)
        rendered = template.render(file_config, id=id)
        data = yaml.safe_load(rendered)
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a dictionary in {file}")
        merged_dict = merge_dicts(merged_dict, data)

with open(output_file, "w") as f:
    yaml.dump(merged_dict, f, default_flow_style=False)
print(f"Configuration built to {output_file}")
