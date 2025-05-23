# 🧰 NetBox YAML Generator

A Flask-based web application that extracts structured device information from manufacturer spec sheets (PDF or YAML) and generates validated, NetBox-compliant device-type YAML files.

This tool automates spec parsing, field formatting, file naming, and compliance checks according to the [NetBox Device Type Library Contribution Guide](https://github.com/netbox-community/devicetype-library/blob/master/CONTRIBUTING.md).

---

## 📦 Features

- ✅ Upload **PDF spec sheets** or **YAML files**
- 🤖 Uses **OpenAI (GPT-4o)** to parse PDFs and generate structured YAML
- ✂️ **Splits multiple part numbers** into individual YAMLs
- 🏷️ Enforces slug/filename conventions (`model` or `part_number`)
- 📑 Adds autogenerated `comments` field with traceable source info
- 🧹 Removes unsupported fields, validates interfaces, adds defaults
- 📦 Bundles multiple files into a downloadable `.zip`

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-org/netbox-yaml-generator.git
cd netbox-yaml-generator
```

### 2. (Recommended) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

This ensures your environment is isolated and dependencies won't conflict with system-wide packages.

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**`requirements.txt` includes:**
- `Flask` (web framework)
- `PyMuPDF` (`fitz`) for PDF parsing
- `PyYAML` for YAML parsing/formatting
- `Werkzeug` for secure file handling
- `openai` for LLM integration

### 4. Run the application
```bash
python app.py
```
---

## 🌐 Usage

1. Visit `http://localhost:5000` in your browser.
2. Select your preferred **OpenAI model** (e.g., `gpt-4o`).
3. Upload a manufacturer PDF or YAML.
4. The app:
   - Parses the file
   - Validates and sanitizes fields
   - Generates one `.yml` per part number
5. Download the result as a `.yml` or `.zip`.

> 💡 YAMLs are automatically validated using the internal NetBox scripts:
> `validate_config_standalone.py` and `validate_manifest_standalone.py`.

---

## 🧠 Field Rules & Validation

The app enforces the following:

| Field        | Behavior |
|--------------|----------|
| `slug`       | Normalized from `model`; capped to 2 hyphen segments |
| `filename`   | Derived from `model` or `part_number`, lowercased |
| `interfaces` | Unknown types fallback to `other`, `name` always required |
| `comments`   | Auto-tagged with filename origin |
| `device-bays`| Converts digital I/O bays into `inventory-items` |
| `null/empty` | Removed before saving |
| `multi-model`| Split into separate YAMLs |
| `validation` | YAMLs validated before download; invalid ones are blocked |

---

## 🧪 Example Output

```yaml
model: SEL-311C-1
manufacturer: Schweitzer Engineering Laboratories, Inc.
slug: sel-311c-1
part_number: SEL-311C-1
comments: The SEL-311C-1 is a transmission relay... — Generated from 311C-1_DS.pdf using the NetBox YAML Generator
interfaces:
  - name: Ethernet
    type: 1000base-t
```

---

## 🛡️ API Key Required

To use OpenAI functionality, provide your API key in the UI form before uploading a PDF.

Environment fallback:
```bash
export OPENAI_API_KEY=your-key-here
```

---

## 🛠 Project Structure

```
├── app_v3.1.py                  # Latest application version
├── templates/
│   └── index.html              # HTML interface
├── output/                     # Generated YAMLs
├── scripts/                    # Local validation modules
│   ├── validate_config_standalone.py
│   └── validate_manifest_standalone.py
├── requirements.txt
```

---

## 📬 Contributing

If you'd like to contribute improvements or additional validation tools, please open an issue or pull request.


---

## 🐳 Docker Deployment

If you prefer to run the application using Docker:

### 1. Ensure you have the following files:
- `Dockerfile` — defines how the image is built
- `docker-compose.yml` — defines how the app runs and maps ports/volumes

### 2. Build and run the app using Docker Compose
```bash
docker-compose up --build
```

This will:
- Build the Docker image
- Launch the Flask app on `http://localhost:5000`
- Mount `./uploads` and `./output` as persistent volumes

### 3. Stop the app
```bash
docker-compose down
```

This is ideal for clean, repeatable deployments in development or production.



### 🔐 Setting Your OpenAI API Key

Make sure to provide your API key before starting the container:
```bash
export OPENAI_API_KEY=your-api-key-here
docker-compose up --build
```

This key will be passed into the container using the `environment` block in `docker-compose.yml`.

---

### 📁 .dockerignore

Add a `.dockerignore` file to prevent unnecessary files from being copied into the container:
```
__pycache__/
*.pyc
*.pyo
*.pyd
output/
uploads/
.venv
.env
.DS_Store
*.log
```

This keeps the container lightweight and avoids leaking local state or sensitive data.
---

## 🐳 Docker Installation Instructions

### 🖥 macOS (via Terminal)
1. Install Homebrew (if not already installed):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install Docker Desktop:
```bash
brew install --cask docker
open /Applications/Docker.app
```

3. Wait for the whale icon in your macOS menu bar to confirm Docker is running.

---

### 🐧 Linux (Ubuntu/Debian)
1. Install Docker Engine:
```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable --now docker
```

2. (Optional) Add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```
Then log out and back in to apply.

3. Install Docker Compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

### 🌐 Docker Network Behavior Explained

When you run the app inside Docker, you might see output like:

```bash
Running on http://127.0.0.1:5000
Running on http://172.18.0.2:5000
```

- `127.0.0.1:5000` is the address you should use in your **browser**.
- `172.18.0.2:5000` is the container’s **internal IP address** on Docker’s bridge network. It's only used for container-to-container communication.
- Docker maps `0.0.0.0` inside the container to your local `localhost` (127.0.0.1), as long as your `docker-compose.yml` exposes the correct port (`5000:5000`).

You can safely ignore `172.18.x.x` addresses when accessing the app from your browser.
---

## 🔐 API Key Scope and IP Address Notes

When you enter your OpenAI API key in the browser interface, it is saved in your browser’s `sessionStorage`. This means:

- It is **only available on the specific IP or domain** where you entered it.
- If you visit the app at `http://127.0.0.1:5000`, then later switch to `http://10.7.216.167:5000`, the API key will not carry over.
- You will need to re-enter the key for each address (origin) you use.

> ✅ To avoid errors like “OpenAI API key not found,” always use the same address (e.g., `http://127.0.0.1:5000`) throughout your session.