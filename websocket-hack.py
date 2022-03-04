#!/usr/bin/python
from __future__ import print_function
import socketserver,ssl
from http.server import BaseHTTPRequestHandler,HTTPServer
from itsdangerous import json
from sqlalchemy import JSON
from websocket import create_connection, WebSocket
from urllib.parse import parse_qs #urlparse
import argparse
import json
import os

LOOP_BACK_PORT_NUMBER = 8000
def FuzzWebSocket(fuzz_value):
    #print(fuzz_value)
    ws.send(ws_message.replace("[FUZZ]", str(fuzz_value[0])))
    result =  ws.recv()
    #print(result)
    return result

def LoadMessage(file):
    file_contents = ""
    try:
        if os.path.isfile(file):
            f = open(file,'r')
            file_contents = f.read()
            f.close()
    except:
        print("Error reading file: %s" % file)
        exit()
    return file_contents

#decode
def ws_encode_frame(msg):
    # Setting fin to 1
    preamble = 1 << 7
    if isinstance(msg, str):
        preamble |= 1
        msg = msg.encode('utf-8')
    else:
        preamble |= 2
    frame = bytes([preamble])
    if len(msg) <= 125:
        frame += bytes([len(msg)])
    elif len(msg) < 2 ** 16:
        frame += bytes([126])
        frame += len(msg).to_bytes(2, 'big')
    else:
        frame += bytes([127])
        frame += len(msg).to_bytes(4, 'big')
    frame += msg
    return frame

class myWebServer(BaseHTTPRequestHandler):

    #Handler for the GET requests
    def do_GET(self):
        qs = parse_qs(self.path[2:])
        fuzz_value = qs['fuzz']
        result = FuzzWebSocket(fuzz_value)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(ws_encode_frame(result))
        self.wfile.write('\n')
        
        return

parser = argparse.ArgumentParser(description='Web Socket Harness: Use traditional tools to assess web sockets')
parser.add_argument('-u','--url', help='The remote WebSocket URL to target.',required=True)
parser.add_argument('-m','--message', help='A file that contains the WebSocket message template to send. Please place [FUZZ] where injection is desired.',required=True)
args = parser.parse_args()

ws_message = LoadMessage(args.message)

ws = create_connection(args.url,sslopt={"cert_reqs": ssl.CERT_NONE},header={},http_proxy_host="", http_proxy_port=8080)

try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPServer(('', LOOP_BACK_PORT_NUMBER), myWebServer)
    print('Started httpserver on port ' , LOOP_BACK_PORT_NUMBER)

    #Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt:
    print('^C received, shutting down the web server')
    server.socket.close()
    ws.close()
