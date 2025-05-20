import yaml

def validate_config(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("YAML is not a valid dictionary")
    if 'model' not in data or not data['model']:
        raise ValueError("Missing or empty 'model' field")
    if 'manufacturer' not in data or not data['manufacturer']:
        raise ValueError("Missing or empty 'manufacturer' field")
    if 'slug' not in data or not data['slug']:
        raise ValueError("Missing or empty 'slug' field")
    if not isinstance(data.get('slug', ''), str) or not data['slug'].islower():
        raise ValueError("Slug must be a lowercase string")
    return True