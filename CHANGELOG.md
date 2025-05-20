# 📋 CHANGELOG – NetBox YAML Generator

This document summarizes all changes made to the original NetBox YAML Generator project, including app logic, user interface, deployment tooling, and documentation enhancements.

---

## ✅ COMPLETE CHANGELOG

### 🧠 Python Backend (`app.py` → `app_v2.py` and beyond)

#### 🧩 Functional Enhancements:
- **Multi-model splitting:** Automatically splits `/` or `,`-separated `model` or `part_number` fields into **multiple individual YAMLs**.
- **Slug and filename standardization:** Enforces NetBox-compliant slugs using `normalize_slug()`, and filenames based on `model` or `part_number`.
- **Comment field injection:** Adds `comments: Generated from <filename>` or appends to any existing comment.
- **Field sanitization and type enforcement:**
  - Removes unsupported or null fields
  - Validates and maps `type` values for interfaces and ports
  - Ensures every component (interfaces, power_ports, etc.) has a `name`
- **Zip output generation:** Bundles multiple YAMLs into a `.zip` if >1 model is detected.
- **Support for list-style and delimited fields:** Handles part numbers as strings, lists, or `/,`-delimited formats.
- **Field fallback logic:** Applies default interface `type: other` when type is missing or invalid.
- **Integrated validation scripts:** Runs `validate_config_standalone` and `validate_manifest_standalone` on each YAML before returning it.
- **Refactored OpenAI integration:** LLM-generated YAML content is cleaned using `clean_yaml_response()` and `strip_non_printable()`.

---

### 🎨 Frontend (`index.html`)

#### 📐 Original Design:
- Simple layout using `<div class="container">`
- Dark mode background (`#0b0f19`) and neon blue button highlights
- Included OpenAI key input, model select, YAML field selection

#### 🚀 Enhancements:
- **Complete visual overhaul:**
  - Rebranded with NetBox Labs–inspired dark blue theme
  - Converted to `Inter` font, grid layout, accent colors (`#00d7c3`, `#f6b400`)
- **Drag-and-drop UX cues:**
  - Modified label: `"Choose file or drag and drop"`
- **Dynamic UI elements:**
  - Auto-displayed dancing hedgehog GIF when YAML generation is in progress
  - Key character counter and session persistence using `sessionStorage`
- **Animated mascot:**
  - Dancing purple hedgehog added to `<div id="hedgehog">`, toggled on form submit

---

### 🧾 README.md

- **Full rewrite and expansion** to include:
  - Project purpose, features, and field behavior
  - Installation steps with `pip` and `Docker`
  - Usage instructions and examples
  - Project structure overview
  - Versioning strategy (semantic, e.g. `v2.1`, `v3.0`)
  - Contribution section

---

### 🐳 Docker Support

#### 📄 `Dockerfile` (added):
- Uses `python:3.11-slim`
- Sets working directory, installs dependencies via `pip`
- Launches `app_v2.py` directly

#### ⚙️ `docker-compose.yml` (added or revised):
- Defines build context and port mapping
- Mounts `uploads/` and `output/` volumes for persistence
- Injects OpenAI API key from environment

#### 🚫 `.dockerignore` (new):
- Excludes unnecessary build content like:
  - `__pycache__/`, `.venv/`, `.DS_Store`
  - `uploads/`, `output/`, `.env`, `*.log`

---

### 🧾 requirements.txt

- Rewritten with version-pinned package list:
  - `Flask>=2.3.0`
  - `PyYAML>=6.0`
  - `PyMuPDF>=1.23.0`
  - `openai>=1.3.5`
  - `Werkzeug>=2.3.0`

---

### 🎯 Summary of Impact

| Area             | Status |
|------------------|--------|
| Python Logic     | ✅ Refactored, validated, expanded |
| Frontend UI      | ✅ Fully modernized and responsive |
| Docs             | ✅ Rewritten for clarity and usability |
| Docker Support   | ✅ Added for deployment and portability |
| LLM Integration  | ✅ Structured, cleaned, and validated |
| UX Polish        | ✅ Drag-and-drop, dancing hedgehog, style consistency |