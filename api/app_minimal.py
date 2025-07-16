#!/usr/bin/env python3
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'message': 'Minimal API working!'
        }
    })

if __name__ == '__main__':
    app.run(debug=True)