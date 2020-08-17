"""

Reverse proxy windows auth verify service

"""

from flask import Flask
from flask import render_template
import sys
import os
import time
import datetime
from flask import jsonify
import socket
from functools import wraps
from flask import redirect, request, current_app, app

import base64
import struct


logfile = "C:\\scripts\\Reverse proxy windows auth verify service\\Reverse proxy windows auth verify service log.txt"

port = 9995

hostname = socket.gethostname()
app = Flask(__name__)

# Wrapper functions to support JSONP requests should we want to access this API from a browser in the future
def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            resp = func(*args, **kwargs)
            resp.set_data('{}({})'.format(
                str(callback),
                resp.get_data(as_text=True)
            ))
            resp.mimetype = 'application/javascript'
            return resp
        else:
            return func(*args, **kwargs)
    return decorated_function

# Add a log entry + datetime
def log_entry(log_message):
	with open(logfile, 'a') as f:
		f.write(str(datetime.datetime.now()) + " : ")
		f.write(log_message + '\n')


@app.route("/getWinAuthInfo", methods=['GET'])
@jsonp
def getWinAuthInfo():
    
    # Some magic to decode an NTLM auth header for username/domain/pc info
    auth_type = 'NTLM'
    actual_header = request.headers.get('Authorization', '')
    expected_signature = b'NTLMSSP\x00'
    msg = base64.b64decode(actual_header[len(auth_type):])
    signature = msg[0:8]

    if signature != expected_signature:
        jsonify(success=False,
                error="Mismatch on NTLM message signature, expecting: %s, actual: %s" % (expected_signature,
                                                                                            signature)
        )

    try:
        domain_length = str(int.from_bytes(msg[28:29], 'little'))
        domain_offset = str(int.from_bytes(msg[32:33], 'little'))
        user_length = str(int.from_bytes(msg[36:37], 'little'))
        user_offset = str(int.from_bytes(msg[40:41], 'little'))
        host_length = str(int.from_bytes(msg[44:45], 'little'))
        host_offset = str(int.from_bytes(msg[48:49], 'little'))
        domain_txt = msg[int(domain_offset):int(domain_offset)+int(domain_length):2].decode()
        user_txt = msg[int(user_offset):int(user_offset)+int(user_length):2].decode()
        host_txt = msg[int(host_offset):int(host_offset)+int(host_length):2].decode()
    except Exception as e:
        jsonify(success=False,
                error="Error trying to decode NTLM auth header",
                exception=str(repr(e))
        )

    if user_txt:
        return jsonify(success=True,
                       domain_txt=domain_txt,
                       user_txt=user_txt,
                       host_txt=host_txt,
                       message='This is the Reverse proxy windows auth verify service API, please contact Matthew.Brown.mls@gmail.com with any questions.')
    else:
        return jsonify(success=False,
                       error="Error, no NTLM auth header found")

if __name__ == "__main__":
    #app.run(ssl_context='adhoc', debug=True, host='0.0.0.0', port=9990)
    app.run(debug=True, host='0.0.0.0', port=port)