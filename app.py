
import os, re, yaml, fitz
from flask import Flask, request, render_template, send_file, abort, session
from openai import OpenAI
from zipfile import ZipFile
from pathlib import Path
import importlib.util
import copy

import textwrap
def fold_comment(text, width=80):
    return '\n'.join(textwrap.wrap(text, width=width))

app = Flask(__name__)
app.secret_key = "secret"

def normalize_slug(value: str) -> str:
    value = value.lower().replace(" ", "-")
    value = re.sub(r"[^a-z0-9-]", "", value)
    return "-".join(value.split("-")[:2])

def infer_interface_type(name: str) -> str:
    name = name.lower()
    if "10/100" in name:
        return "100base-tx"
    if "ethernet" in name or "copper" in name:
        return "1000base-t"
    elif "fiber" in name or "sfp" in name or "qsfp" in name:
        return "1000base-x-sfp"
    elif "wifi" in name or "wireless" in name:
        return "ieee802.11ac"
    elif "lag" in name:
        return "lag"
    elif "loopback" in name:
        return "virtual"
    elif "serial" in name:
        return "other"
    else:
        return "other"

VALID_INTERFACE_TYPES = ['1000base-t', '1000base-x-gbic', '1000base-x-sfp', '100base-tx', '100gbase-x-cfp', '100gbase-x-cfp2',
    '100gbase-x-cfp4', '100gbase-x-qsfp28', '10gbase-cx4', '10gbase-t', '10gbase-x-sfpp', '2.5gbase-t',
    '200gbase-x-qsfp56', '25gbase-x-sfp28', '400gbase-x-osfp', '400gbase-x-qsfp-dd', '40gbase-x-qsfpp', '50gbase-x-sfp28',
    '5gbase-t', '800gbase-x-osfp', '800gbase-x-qsfp-dd', 'cellular', 'coax', 'docsis', 'e1', 'e3', 'ieee802.11a',
    'ieee802.11ac', 'ieee802.11ad', 'ieee802.11ax', 'ieee802.11be', 'ieee802.11g', 'ieee802.11n', 'lag', 'other', 't1',
    't3', 'virtual', 'xdsl']

def validate_interface_type(value):
    if not isinstance(value, str): return 'other'
    cleaned = value.lower().strip()
    return cleaned if cleaned in VALID_INTERFACE_TYPES else 'other'

def sanitize_dict(d, allowed):
    return {k: v for k, v in d.items() if k in allowed}

def sanitize_yaml(dev):
    converted_items = []
    if 'device-bays' in dev:
        new_bays = []
        for entry in dev['device-bays']:
            name = entry.get('name', '').lower()
            if 'digital input' in name or 'digital output' in name:
                converted_items.append({
                    'name': entry.get('name', 'I/O Block'),
                    'label': entry.get('name'),
                    'description': entry.get('description', 'Fixed digital I/O block')
                })
            else:
                new_bays.append(entry)
        dev['device-bays'] = new_bays
    if converted_items:
        dev['inventory-items'] = dev.get('inventory-items', []) + converted_items

    allowed_top = {
        'model', 'manufacturer', 'part_number', 'slug', 'u_height', 'is_full_depth',
        'airflow', 'front_image', 'rear_image', 'comments',
        'console-ports', 'power-ports', 'power-outlets',
        'interfaces', 'rear-ports', 'module-bays', 'device-bays', 'inventory-items'
    }
    component_fields = {
        'interfaces': {'name', 'type', 'description'},
        'console-ports': {'name', 'type', 'description'},
        'power-ports': {'name', 'type', 'maximum_draw', 'description'},
        'module-bays': {'name', 'position', 'description'},
        'device-bays': {'name', 'count', 'description', 'position'},
        'power-outlets': {'name', 'type', 'description', 'power_port'},
        'rear-ports': {'name', 'type', 'description', 'positions'}
    }

    for section in ['interfaces', 'console-ports', 'power-ports', 'rear-ports']:
        for item in dev.get(section, []):
            if isinstance(item, dict) and 'type' in item:
                item['type'] = validate_interface_type(item['type'])
                if item['type'] == 'other':
                    item['type'] = infer_interface_type(item.get('name', '') + " " + item.get('description', ''))

    dev = sanitize_dict(dev, allowed_top)
    dev.pop('console-server-ports', None)

    for section, allowed_keys in component_fields.items():
        if section in dev and isinstance(dev[section], list):
            for idx, item in enumerate(dev[section]):
                 if isinstance(item, dict) and 'name' not in item:
                         item['name'] = f"{section[:-1].capitalize()} {idx+1}"
            dev[section] = [sanitize_dict(item, allowed_keys) for item in dev[section] if isinstance(item, dict)]

    dev = {k: v for k, v in dev.items() if v not in ("", None, [], {})}
    return dev


def clean_yaml_response(text):
    lines = text.strip().splitlines()
    return "\n".join(line for line in lines if not line.strip().startswith("```"))

@app.route("/")
def index():
    return render_template(
        "index.html",
        title="NetBox YAML Generator",
        available_fields=[
            "model", "manufacturer", "part_number", "slug", "u_height", "is_full_depth",
            "console_ports", "interfaces", "power_ports", "module_bays", "device_bays", "comments"
        ],
        available_models=[
            "gpt-4o", "gpt-4o-mini"
        ]
    )

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        abort(400, "No file uploaded")
    file_bytes = file.read()
    if file.content_type == 'application/pdf' or file_bytes.startswith(b'%PDF'):
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        text = "\n".join(page.get_text() for page in doc)
        text = "\n".join(page.get_text() for page in doc)
        api_key = session.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            abort(400, "OpenAI API key not found.")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=session.get("model", "gpt-4o"),
            messages=[
                {"role": "system", "content": "You must output only valid NetBox device-type YAML. No explanation, no markdown, no text."},
                {"role": "user", "content": text[:4000]}
            ],
            temperature=0.2
        )
        raw = response.choices[0].message.content
    else:
        raw = file_bytes.decode('utf-8', errors='ignore')

    raw = raw.strip()
    raw = clean_yaml_response(raw)
    raw = ''.join(c for c in raw if c.isprintable() or c in '\n\r\t')
    if not raw.strip().startswith(("model:", "---", "manufacturer:", "slug:", "part_number:")):
        abort(400, "Uploaded file does not appear to be valid YAML.")

    parsed = yaml.safe_load(raw)
    if not parsed:
        abort(400, "Parsed YAML is empty or invalid.")
    dev = parsed
    model_raw = dev.get("model", "") or dev.get("part_number", "")
    if not re.match(r"^\d{4}-", str(model_raw)):
        model_raw = dev.get("part_number", model_raw)

    if isinstance(model_raw, list):
        model_candidates = model_raw
    else:
        model_candidates = re.split(r"[/,]", str(model_raw))

    model_variants = [m.strip() for m in model_candidates if re.match(r"^\d{4}-[A-Z0-9-]+$", m.strip(), re.I)]
    file_paths = []

    if len(model_variants) > 1:
        for model_name in model_variants:
            dev_copy = copy.deepcopy(dev)
            dev_copy["model"] = model_name
            dev_copy["slug"] = normalize_slug(model_name)
            dev_copy["part_number"] = model_name
            prior_comment = dev_copy.get("comments", "")
            gen_tag = f"Generated from {file.filename} using the NetBox YAML Generator"
            if prior_comment:
                dev_copy["comments"] = fold_comment(f"{prior_comment} — {gen_tag}")
            else:
                dev_copy["comments"] = gen_tag
            for section in ["interfaces", "console_ports", "power_ports", "module_bays", "device_bays"]:
                if section in dev_copy:
                    dev_copy[section] = [
                        item for item in dev_copy[section]
                        if model_name.lower() in str(item).lower()
                        or not any(
                            alt.lower() in str(item.get("description", "")).lower() or
                            alt.lower() in str(item.get("name", "")).lower()
                            for alt in model_variants if alt != model_name
                        )
                    ]
            dev_copy = sanitize_yaml(dev_copy)
            filename_base = "-".join(model_name.lower().replace(" ", "-").split("-")[:2])
            os.makedirs("output", exist_ok=True)
            yaml_path = os.path.join("output", f"{filename_base}.yml")
            with open(yaml_path, "w") as f:
                yaml.safe_dump(dev_copy, f, sort_keys=False)
            file_paths.append(yaml_path)
        if len(file_paths) > 1:
            zip_path = os.path.join("output", "netbox_yamls.zip")
            with ZipFile(zip_path, "w") as zf:
                for path in file_paths:
                    zf.write(path, Path(path).name)
            return send_file(zip_path, as_attachment=True, mimetype="application/zip")
        else:
            return send_file(file_paths[0], as_attachment=True, mimetype="text/yaml")

    dev = sanitize_yaml(dev)
    prior_comment = dev.get("comments", "")
    gen_tag = f"Generated from {file.filename} using the NetBox YAML Generator"
    dev["comments"] = f"{prior_comment} — {gen_tag}" if prior_comment else gen_tag
    filename_base = "-".join(dev.get("model", "device").lower().replace(" ", "-").split("-")[:2])
    os.makedirs("output", exist_ok=True)
    yaml_path = os.path.join("output", f"{filename_base}.yml")
    with open(yaml_path, "w") as f:
        yaml.safe_dump(dev, f, sort_keys=False)
    return send_file(yaml_path, as_attachment=True, mimetype="text/yaml")

if __name__ == "__main__":
    app.run(debug=True)
