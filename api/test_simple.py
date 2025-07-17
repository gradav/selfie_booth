def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/html')]
    start_response(status, headers)
    
    html = """
    <html>
    <head><title>Simple Test</title></head>
    <body>
    <h1>Basic WSGI Working!</h1>
    <p>If you see this, WSGI is functioning.</p>
    </body>
    </html>
    """
    return [html.encode()]