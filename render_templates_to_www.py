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
