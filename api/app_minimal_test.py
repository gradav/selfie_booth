#!/home/n99fc05/virtualenv/lockhartlovesyou.com/selfie_booth/api/3.9/bin/python
"""
Minimal test version to isolate the issue
"""
from flask import Flask, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

@app.route('/test')
def test():
    return jsonify({'success': True, 'message': 'Basic Flask working'})

@app.route('/test_session')
def test_session():
    from flask import session
    session['test'] = 'working'
    return jsonify({'success': True, 'message': 'Sessions working'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)