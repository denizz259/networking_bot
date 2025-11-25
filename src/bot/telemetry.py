from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    # не засоряем stdout access-логами http.server
    def log_message(self, format, *args):  # noqa: A003
        return


def start_health_server(host: str = "0.0.0.0", port: int = 8000) -> HTTPServer:
    httpd = HTTPServer((host, port), _HealthHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd
