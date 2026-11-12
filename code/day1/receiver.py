#!/usr/bin/env python3
"""A tiny HTTP receiver: prints every reading a neighbour's gateway POSTs to it."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            reading = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self.send_response(400)  # Bad Request
            self.end_headers()
            return

        print(f"From {reading.get('gateway')} ({self.client_address[0]}): "
              f"level {reading.get('tank_level_pct')}%  "
              f"temp {reading.get('pump_temp_c')}  {reading.get('status')}")
        self.send_response(204)  # No Content: received, nothing to send back
        self.end_headers()

    def log_message(self, *args) -> None:
        pass  # keep the screen clean: our print above is enough


if __name__ == "__main__":
    print(f"Listening on port {PORT}, Ctrl+C to stop")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
