import yaml

def validate_manifest(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("YAML is not a valid dictionary")
    # Ensure no unsupported keys are present
    unsupported = {'quantity', 'extras', 'module-slots'}
    for key in unsupported:
        if key in data:
            raise ValueError(f"Unsupported field found: {key}")
    return True