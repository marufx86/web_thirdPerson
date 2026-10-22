"""Local test server for the deployable folder (dist/), behaving like a plain static web host.

Unlike the development servers, it sends NO special headers (no COOP/COEP, no wasm MIME tricks): if the game runs
here, it runs on any static host. It only adds the same caching rules as _headers / vercel.json.

Usage: py serve_dist.py [folder=dist] [--port 8080]
"""
import argparse
import http.server
import os
import socketserver
import sys


class Handler(http.server.SimpleHTTPRequestHandler):
	extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".json": "application/json",
		".bin": "application/octet-stream", ".html": "text/html"}

	def end_headers(self):
		path = self.path.split("?")[0]
		if path.startswith("/game/"):
			self.send_header("Cache-Control", "public, max-age=31536000, immutable")
		else:
			self.send_header("Cache-Control", "no-cache")
		super().end_headers()

	def log_message(self, fmt, *args):
		pass  # quiet: the page shows its own progress


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("folder", nargs="?", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist"))
	parser.add_argument("--port", type=int, default=8080)
	args = parser.parse_args()
	folder = os.path.abspath(args.folder)
	if not os.path.isfile(os.path.join(folder, "manifest.json")):
		sys.exit(f"No manifest.json in {folder}. Run make_deploy.bat first.")
	os.chdir(folder)
	socketserver.TCPServer.allow_reuse_address = True
	with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), Handler) as httpd:
		print(f"Serving {folder} like a plain static host")
		print(f"Open http://localhost:{args.port}/ in Chrome. Press Ctrl+C to stop.")
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			pass


if __name__ == "__main__":
	main()
