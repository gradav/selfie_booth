#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python

import sys
import os

print("Content-Type: application/json")
print("")

# Add virtual environment to path
venv_site_packages = "/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/lib/python3.9/site-packages"
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

result = {
    "python_executable": sys.executable,
    "python_version": sys.version,
    "venv_exists": os.path.exists(venv_site_packages),
    "venv_path": venv_site_packages
}

# Test Flask import
try:
    import flask
    result["flask_available"] = True
    result["flask_version"] = flask.__version__
    result["flask_location"] = flask.__file__
except ImportError as e:
    result["flask_available"] = False
    result["flask_error"] = str(e)

# Test Flask-CORS import
try:
    import flask_cors
    result["flask_cors_available"] = True
except ImportError as e:
    result["flask_cors_available"] = False
    result["flask_cors_error"] = str(e)

# List packages in virtual environment
try:
    if os.path.exists(venv_site_packages):
        packages = [d for d in os.listdir(venv_site_packages) if not d.startswith('.')]
        result["installed_packages"] = packages[:20]  # First 20 packages
    else:
        result["installed_packages"] = []
except:
    result["installed_packages"] = ["Error listing packages"]

import json
print(json.dumps(result, indent=2))