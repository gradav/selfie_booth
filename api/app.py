#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
Minimal debug version to test what's breaking
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/selfie_booth/api/debug')
def debug():
    return jsonify({'success': True, 'message': 'Minimal Flask working'})

@app.route('/selfie_booth/api/health') 
def health():
    return jsonify({'success': True, 'message': 'Health check working'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)