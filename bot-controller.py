from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
import time
import threading
import logging
import mysql.connector

# Initialization
port = 80
app_protected = "TITCSL"
rate_limit_interval = 20
max_requests_per_interval = 8
ban_duration = 300  # in seconds

# Setup logging
logging.basicConfig(filename='server.log', level=logging.INFO)

class RedirectHandler(SimpleHTTPRequestHandler):
    reload_counts = {}
    reload_lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        self.db_conn = mysql.connector.connect(
            user='root',
            password='admin',
            host='localhost',
            port=3306,
            database='tpsl'
        )
        self.create_banned_ips_table()
        super().__init__(*args, **kwargs)

    def create_banned_ips_table(self):
        with self.db_conn.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS banned_ip_s (ban_ip_address VARCHAR(15) PRIMARY KEY, ban_time INTEGER)")

    def do_GET(self):
        ip_address = self.client_address[0]

        if self.is_banned(ip_address):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Request webpage not available for *you* try after some time COPYRIGHT 2023-24 -- **TITCSL** -- **MADE IN INDIA**")
        elif self.is_potential_bot(ip_address):
            self.ban_ip(ip_address)
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Request webpage not available for *you* try after some time COPYRIGHT 2023-24 -- **TITCSL** -- **MADE IN INDIA**")
        else:
            redirect_url = "http://192.168.0.103:443/"
            self.send_response(302)
            self.send_header("Location", redirect_url)
            self.end_headers()

    def is_banned(self, ip_address):
        with self.db_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM banned_ips WHERE ip_address = %s", (ip_address,))
            result = cursor.fetchone()
            if result:
                ban_time = result[1]
                if time.time() - ban_time < ban_duration:
                    return True
                else:
                    cursor.execute("DELETE FROM banned_ips WHERE ip_address = %s", (ip_address,))

        return False

    def is_potential_bot(self, ip_address):
        with RedirectHandler.reload_lock:
            if ip_address in RedirectHandler.reload_counts:
                last_reload_time, reload_count = RedirectHandler.reload_counts[ip_address]

                if time.time() - last_reload_time < rate_limit_interval:
                    reload_count += 1
                    RedirectHandler.reload_counts[ip_address] = (time.time(), reload_count)

                    return reload_count >= max_requests_per_interval

            RedirectHandler.reload_counts[ip_address] = (time.time(), 1)

        return False

    def ban_ip(self, ip_address):
        with self.db_conn.cursor() as cursor:
            cursor.execute("INSERT INTO banned_ips (ip_address, ban_time) VALUES (%s, %s)", (ip_address, time.time()))
        self.db_conn.commit()

if __name__ == "__main__":

    with ThreadingTCPServer(("", port), RedirectHandler) as httpd:
        print("App Protection Started By **TITCSL** TO {} ON {}".format(app_protected, port))

        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            server_thread.join()
        except KeyboardInterrupt:
            httpd.shutdown()
            print("Server stopped.")
