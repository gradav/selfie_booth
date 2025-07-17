#!/usr/bin/env python3
try:
    from flask import Flask
    print("Content-Type: text/html\n")
    print("<h1>✅ Flask Import Successful!</h1>")
    print("<p>Python environment is properly configured.</p>")
except ImportError as e:
    print("Content-Type: text/html\n")
    print(f"<h1>❌ Import Error:</h1><p>{e}</p>")