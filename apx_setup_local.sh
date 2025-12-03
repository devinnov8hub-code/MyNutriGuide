#!/usr/bin/env bash
set -euo pipefail

# Run this from your Flask project root (the folder that contains app.py, templates/, static/)
# Example: cd /path/to/R4I-team6 && ./apx_setup_local.sh

PROJECT_ROOT="$(pwd)"
FLASK_DIR="$PROJECT_ROOT"
APX_DIR="$PROJECT_ROOT/apx"
WWW_DIR="$APX_DIR/www"

echo "Running from PROJECT_ROOT=$PROJECT_ROOT"
echo "FLASK_DIR=$FLASK_DIR"
echo "APX_DIR=$APX_DIR"
echo "WWW_DIR=$WWW_DIR"

# cleanup previous apx if exists
if [ -d "$APX_DIR" ]; then
  echo "Removing existing $APX_DIR"
  rm -rf "$APX_DIR"
fi

mkdir -p "$WWW_DIR"
cd "$APX_DIR"

echo ">>> npm init (apx)"
npm init -y >/dev/null

echo ">>> installing Capacitor packages"
npm install @capacitor/core @capacitor/cli --no-audit --no-fund --save-dev >/dev/null
npm install @capacitor/android --no-audit --no-fund --save >/dev/null

echo ">>> writing capacitor.config.json"
cat > capacitor.config.json <<JSON
{
  "appId": "com.foodscan.app",
  "appName": "FoodScan",
  "webDir": "www",
  "bundledWebRuntime": false
}
JSON

cd "$PROJECT_ROOT"

echo ">>> Copying static files from $FLASK_DIR/static to $WWW_DIR/static"
mkdir -p "$WWW_DIR/static"
if [ -d "$FLASK_DIR/static" ]; then
  cp -r "$FLASK_DIR/static/." "$WWW_DIR/static/"
  echo "Copied static files."
else
  echo "Warning: $FLASK_DIR/static not found. Please verify your static assets."
fi

echo ">>> Copying any prebuilt HTML from templates/ (if any exist)"
if [ -d "$FLASK_DIR/templates" ]; then
  shopt -s nullglob
  templates=( "$FLASK_DIR/templates"/*.html )
  if [ ${#templates[@]} -gt 0 ]; then
    cp "$FLASK_DIR/templates/"*.html "$WWW_DIR/" 2>/dev/null || true
    echo "Copied templates/*.html to $WWW_DIR"
  else
    echo "No top-level .html files in templates/ to copy."
  fi
else
  echo "templates/ not found; skipping copy."
fi

# create a Python renderer helper in the flask project root
RENDER_SCRIPT="$FLASK_DIR/render_templates_to_www.py"
cat > "$RENDER_SCRIPT" <<'PY'
#!/usr/bin/env python3
"""
Render top-level templates/*.html to static HTML into output dir, and copy static/ folder.
Usage:
  python3 render_templates_to_www.py <output_www_dir>

Run this from your Flask project root.
"""
import sys, os, shutil
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python3 render_templates_to_www.py <output_www_dir>")
    sys.exit(1)

output_dir = Path(sys.argv[1]).resolve()
project_root = Path.cwd().resolve()
sys.path.insert(0, str(project_root))

# Try to import common Flask app modules: app.py, wsgi.py, application.py
app = None
for name in ("app","wsgi","application"):
    try:
        mod = __import__(name)
        app = getattr(mod, "app", getattr(mod, "application", None))
        if app:
            break
    except Exception:
        pass

if not app:
    print("Could not import Flask app (tried app/wsgi/application). If your entrypoint is named differently, edit this script.")
    sys.exit(1)

from flask import render_template

templates_dir = Path(app.template_folder or (project_root / "templates"))
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Rendering templates from {templates_dir} to {output_dir}")
for tpl in templates_dir.glob("*.html"):
    try:
        with app.test_request_context("/"):
            rendered = render_template(tpl.name)
        (output_dir / tpl.name).write_text(rendered, encoding="utf-8")
        print("Rendered", tpl.name)
    except Exception as e:
        print("Skipping", tpl.name, "due to", e)

# copy static folder
static_src = Path(app.static_folder or (project_root / "static"))
static_dst = output_dir / "static"
if static_src.exists():
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)
    print("Copied static to", static_dst)
else:
    print("Static folder not found at", static_src)
PY

chmod +x "$RENDER_SCRIPT"

echo ">>> Attempting to render templates to $WWW_DIR using Python helper"
if python3 "$RENDER_SCRIPT" "$WWW_DIR"; then
  echo "Rendered templates and copied static successfully (if templates existed)."
else
  echo "Rendering helper failed or templates require runtime context. Continue anyway."
fi

# ensure index.html exists
if [ ! -f "$WWW_DIR/index.html" ]; then
  echo "Creating fallback index.html in $WWW_DIR"
  cat > "$WWW_DIR/index.html" <<HTML
<!doctype html>
<html>
  <head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FoodScan</title></head>
  <body>
    <h1>FoodScan</h1>
    <p>Replace this file with your real index.html or make sure your templates rendered correctly.</p>
    <img src="/static/logo_b.svg" alt="logo" style="max-width:200px;">
  </body>
</html>
HTML
fi

cd "$APX_DIR"

echo ">>> adding android platform (npx cap add android)"
npx cap add android

echo ">>> copying web assets into native android project (npx cap copy android)"
npx cap copy android

echo ">>> building debug apk via Gradle (./gradlew assembleDebug)"
cd android
if [ -f "./gradlew" ]; then
  ./gradlew assembleDebug
else
  echo "gradlew not found. You can run 'npx cap open android' and build via Android Studio."
  exit 0
fi

echo ">>> Debug APK location:"
echo "$APX_DIR/android/app/build/outputs/apk/debug/app-debug.apk"

echo ">>> done. To open in Android Studio: (from $APX_DIR) npx cap open android"
