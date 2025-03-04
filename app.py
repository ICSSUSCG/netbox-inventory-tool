import os
import yaml
import fitz  # PyMuPDF for PDF parsing
import openai  # OpenAI API for ChatGPT
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store API key, selected fields, and model selection in memory
user_api_key = None
selected_fields = []
selected_model = "gpt-4-turbo"

# List of available fields from NetBox device type library
AVAILABLE_FIELDS = [
    "model", "manufacturer", "part_number", "slug", "u_height", "is_full_depth", "comments",
    "console-ports", "power-ports", "interfaces", "module-bays", "device-bays"
]

AVAILABLE_MODELS = ["gpt-4-turbo", "gpt-3.5-turbo"]

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text[:8000]  # Truncate to fit within ChatGPT's token limit

# Function to generate YAML using ChatGPT with validation
def generate_yaml_with_chatgpt(prompt, api_key, fields, model):
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Generate a structured YAML file based on the provided description. Include only these fields: {', '.join(fields)}."},
                {"role": "user", "content": prompt[:8000]}  # Truncate input to fit model limits
            ],
            temperature=0.3
        )
        yaml_content = response.choices[0].message.content.strip().replace('```yaml', '').replace('```', '').strip()

        # Validate YAML output
        try:
            parsed_yaml = yaml.safe_load(yaml_content)
            return yaml.dump(parsed_yaml, default_flow_style=False, sort_keys=False, indent=2)
        except yaml.YAMLError as e:
            return f"YAML Validation Error: {str(e)}"
    except openai.APIConnectionError:
        return "Error: Cannot connect to OpenAI. Please check your internet connection."
    except openai.OpenAIError as e:
        if "insufficient_quota" in str(e):
            return "Error: You exceeded your OpenAI API quota. Check your billing details at https://platform.openai.com/account/billing."
        if "context_length_exceeded" in str(e):
            return "Error: Input is too long. Try reducing the text size."
        return f"OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html', title="Netbox YAML Generator", available_fields=AVAILABLE_FIELDS, available_models=AVAILABLE_MODELS)

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    global user_api_key
    user_api_key = request.form['api_key']
    return jsonify({"message": "API key set successfully"})

@app.route('/set_fields', methods=['POST'])
def set_fields():
    global selected_fields
    selected_fields = request.json.get('fields', [])
    return jsonify({"message": "Fields updated successfully", "selected_fields": selected_fields})

@app.route('/set_model', methods=['POST'])
def set_model():
    global selected_model
    selected_model = request.json.get('model', "gpt-4-turbo")
    return jsonify({"message": "Model updated successfully", "selected_model": selected_model})

@app.route('/upload', methods=['POST'])
def upload_file():
    global user_api_key, selected_fields, selected_model
    if not user_api_key:
        return jsonify({"error": "API Key is required."}), 400
    if not selected_fields:
        return jsonify({"error": "At least one field must be selected."}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    extracted_text = extract_text_from_pdf(file_path)
    yaml_content = generate_yaml_with_chatgpt(extracted_text, user_api_key, selected_fields, selected_model)
    yaml_path = os.path.join(OUTPUT_FOLDER, f"{filename}.yaml")

    with open(yaml_path, "w") as file:
        file.write(yaml_content)

    yaml_filename = os.path.join(OUTPUT_FOLDER, f"netbox_device_{filename.replace('.pdf', '')}.yaml")
    with open(yaml_filename, "w") as file:
        file.write(yaml_content)
    return send_file(yaml_filename, as_attachment=True, mimetype='text/yaml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Updated index.html with model selection
template_content = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <script>
        function setModel() {
            let selectedModel = document.getElementById("model_select").value;
            fetch("/set_model", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({model: selectedModel})
            });
        }
    </script>
</head>
<body>
    <h1>🚀 Netbox YAML Generator 🚀</h1>
    <p>Select AI Model:</p>
    <select id="model_select" onchange="setModel()">
        {% for model in available_models %}
            <option value="{{ model }}">{{ model }}</option>
        {% endfor %}
    </select>
    <br><br>
    <p>Upload a PDF to generate YAML:</p>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Generate YAML</button>
    </form>
</body>
</html>
"""

with open("templates/index.html", "w") as html_file:
    html_file.write(template_content)
