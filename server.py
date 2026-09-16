#!/usr/bin/env python3
"""
Rustic Recipe Card Maker & Storage Server
Pure Python 3 standard library HTTP Server with SQLite backend.
"""

import os
import sys
import json
import mimetypes
import argparse
import signal
import uuid
import base64
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import db

# Setup Directories
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
PID_FILE = BASE_DIR / "server.pid"

# Ensure directories exist
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Register common mimetypes
mimetypes.init()
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("font/woff2", ".woff2")


class RecipeAppHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for REST API and Static Assets."""

    server_version = "RusticRecipeCardServer/1.0"

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status_code, payload):
        """Helper to send JSON response."""
        response_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(response_bytes)

    def _send_error_json(self, status_code, message):
        """Helper to send structured JSON error."""
        self._send_json(status_code, {"error": message})

    def _read_json_body(self):
        """Reads and parses JSON from request body."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                return {}
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        except Exception as e:
            print(f"[ERROR] Failed to read JSON body: {e}")
            return None

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Route GET requests to API or static file serving."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        # API Routes
        if path == "/api/recipes":
            search_query = query_params.get("search", [None])[0]
            category = query_params.get("category", [None])[0]
            recipes = db.get_all_recipes(search_query, category)
            self._send_json(200, {"recipes": recipes})
            return

        if path.startswith("/api/recipes/"):
            try:
                recipe_id = int(path.split("/api/recipes/")[1])
                recipe = db.get_recipe_by_id(recipe_id)
                if recipe:
                    self._send_json(200, {"recipe": recipe})
                else:
                    self._send_error_json(404, f"Recipe with ID {recipe_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid recipe ID")
            return

        if path == "/api/ingredients":
            q = query_params.get("q", [None])[0]
            cat = query_params.get("category", [None])[0]
            ingredients = db.get_prepopulated_ingredients(q, cat)
            self._send_json(200, {"ingredients": ingredients})
            return

        if path.startswith("/api/ingredients/"):
            try:
                ing_id = int(path.split("/api/ingredients/")[1])
                ingredient = db.get_ingredient_by_id(ing_id)
                if ingredient:
                    self._send_json(200, {"ingredient": ingredient})
                else:
                    self._send_error_json(404, f"Ingredient with ID {ing_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid ingredient ID")
            return

        if path == "/api/health":
            self._send_json(200, {"status": "ok", "time": os.path.getmtime(db.DB_PATH) if db.DB_PATH.exists() else 0})
            return

        # Static files route
        self._serve_static(path)

    def do_POST(self):
        """Route POST requests to API."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/recipes":
            data = self._read_json_body()
            if data is None:
                self._send_error_json(400, "Invalid JSON data")
                return
            if not data.get("title") or not data.get("title").strip():
                self._send_error_json(400, "Recipe title is required")
                return

            new_recipe = db.create_recipe(data)
            self._send_json(201, {"recipe": new_recipe, "message": "Recipe created successfully"})
            return

        if path == "/api/ingredients":
            data = self._read_json_body()
            if data is None:
                self._send_error_json(400, "Invalid JSON data")
                return
            if not data.get("name_en") or not data.get("name_en").strip():
                self._send_error_json(400, "Ingredient name (English) is required")
                return

            new_ing = db.create_ingredient(data)
            self._send_json(201, {"ingredient": new_ing, "message": "Ingredient added successfully"})
            return

        if path == "/api/upload":
            # Handle image upload
            content_type = self.headers.get("Content-Type", "")
            
            if "application/json" in content_type:
                data = self._read_json_body()
                if not data or "data" not in data:
                    self._send_error_json(400, "Missing image data")
                    return

                try:
                    data_uri = data["data"]
                    # Format: data:image/png;base64,....
                    if "," in data_uri:
                        header, encoded = data_uri.split(",", 1)
                        if "png" in header:
                            ext = ".png"
                        elif "webp" in header:
                            ext = ".webp"
                        elif "gif" in header:
                            ext = ".gif"
                        else:
                            ext = ".jpg"
                    else:
                        encoded = data_uri
                        ext = ".jpg"

                    image_bytes = base64.b64decode(encoded)
                    filename = f"img_{uuid.uuid4().hex[:12]}{ext}"
                    filepath = UPLOADS_DIR / filename
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)

                    self._send_json(200, {
                        "url": f"/uploads/{filename}",
                        "filename": filename,
                        "size": len(image_bytes)
                    })
                    return
                except Exception as e:
                    self._send_error_json(500, f"Error processing image: {str(e)}")
                    return

            elif "multipart/form-data" in content_type:
                # Handle raw multipart upload
                try:
                    boundary = content_type.split("boundary=")[1].strip()
                    content_length = int(self.headers.get("Content-Length", 0))
                    raw_body = self.rfile.read(content_length)

                    # Simple multipart extraction for single image file
                    parts = raw_body.split(f"--{boundary}".encode())
                    for part in parts:
                        if b'filename="' in part:
                            header_part, file_data = part.split(b"\r\n\r\n", 1)
                            file_data = file_data.rstrip(b"\r\n--")
                            # Detect extension from filename
                            orig_filename = "upload.jpg"
                            for line in header_part.split(b"\r\n"):
                                if b'filename="' in line:
                                    name_start = line.find(b'filename="') + 10
                                    name_end = line.find(b'"', name_start)
                                    orig_filename = line[name_start:name_end].decode("utf-8", errors="ignore")
                            ext = Path(orig_filename).suffix.lower()
                            if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
                                ext = ".jpg"

                            new_filename = f"img_{uuid.uuid4().hex[:12]}{ext}"
                            out_path = UPLOADS_DIR / new_filename
                            with open(out_path, "wb") as f:
                                f.write(file_data)

                            self._send_json(200, {
                                "url": f"/uploads/{new_filename}",
                                "filename": new_filename,
                                "size": len(file_data)
                            })
                            return

                    self._send_error_json(400, "No file found in multipart upload")
                    return
                except Exception as e:
                    self._send_error_json(500, f"Upload error: {str(e)}")
                    return
            else:
                self._send_error_json(400, "Unsupported media type. Use JSON base64 or multipart/form-data")
                return

        self._send_error_json(404, "Endpoint not found")

    def do_PUT(self):
        """Route PUT requests to API for updating recipes."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/recipes/"):
            try:
                recipe_id = int(path.split("/api/recipes/")[1])
                data = self._read_json_body()
                if data is None:
                    self._send_error_json(400, "Invalid JSON data")
                    return

                updated = db.update_recipe(recipe_id, data)
                if updated:
                    self._send_json(200, {"recipe": updated, "message": "Recipe updated successfully"})
                else:
                    self._send_error_json(404, f"Recipe with ID {recipe_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid recipe ID")
            return

        if path.startswith("/api/ingredients/"):
            try:
                ing_id = int(path.split("/api/ingredients/")[1])
                data = self._read_json_body()
                if data is None:
                    self._send_error_json(400, "Invalid JSON data")
                    return

                updated = db.update_ingredient(ing_id, data)
                if updated:
                    self._send_json(200, {"ingredient": updated, "message": "Ingredient updated successfully"})
                else:
                    self._send_error_json(404, f"Ingredient with ID {ing_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid ingredient ID")
            return

        self._send_error_json(404, "Endpoint not found")

    def do_DELETE(self):
        """Route DELETE requests to API for deleting recipes and ingredients."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path.startswith("/api/recipes/"):
            try:
                recipe_id = int(path.split("/api/recipes/")[1])
                success = db.delete_recipe(recipe_id)
                if success:
                    self._send_json(200, {"message": f"Recipe {recipe_id} deleted successfully"})
                else:
                    self._send_error_json(404, f"Recipe with ID {recipe_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid recipe ID")
            return

        if path.startswith("/api/ingredients/"):
            try:
                ing_id = int(path.split("/api/ingredients/")[1])
                success = db.delete_ingredient(ing_id)
                if success:
                    self._send_json(200, {"message": f"Ingredient {ing_id} deleted successfully"})
                else:
                    self._send_error_json(404, f"Ingredient with ID {ing_id} not found")
            except ValueError:
                self._send_error_json(400, "Invalid ingredient ID")
            return

        self._send_error_json(404, "Endpoint not found")

    def _serve_static(self, req_path):
        """Serves static frontend files and uploaded media."""
        # Clean path
        req_path = unquote(req_path.lstrip("/"))
        if not req_path or req_path == "":
            req_path = "index.html"

        # Check if uploads directory
        if req_path.startswith("uploads/"):
            target_file = (BASE_DIR / req_path).resolve()
            # Security check: must remain inside UPLOADS_DIR
            if not str(target_file).startswith(str(UPLOADS_DIR.resolve())):
                self._send_error_json(403, "Access denied")
                return
        else:
            target_file = (PUBLIC_DIR / req_path).resolve()
            # Fallback to index.html if file doesn't exist but isn't an asset
            if not target_file.exists() and not (req_path.startswith("css/") or req_path.startswith("js/") or req_path.startswith("assets/")):
                target_file = (PUBLIC_DIR / "index.html").resolve()
            elif not str(target_file).startswith(str(PUBLIC_DIR.resolve())):
                self._send_error_json(403, "Access denied")
                return

        if not target_file.exists() or target_file.is_dir():
            self._send_error_json(404, "File not found")
            return

        content_type, _ = mimetypes.guess_type(str(target_file))
        if content_type is None:
            content_type = "application/octet-stream"

        try:
            with open(target_file, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            # Cache static assets but not HTML
            if target_file.suffix in [".svg", ".png", ".jpg", ".css", ".js"]:
                self.send_header("Cache-Control", "public, max-age=3600")
            else:
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error_json(500, f"Error reading file: {str(e)}")

    def log_message(self, format, *args):
        """Custom clean logging to stderr."""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def write_pid():
    """Writes process PID to server.pid."""
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"[WARNING] Could not write PID file: {e}")


def remove_pid():
    """Removes server.pid on shutdown."""
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Rustic Recipe Card Maker & Storage Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    # Initialize SQLite database
    print("[INIT] Checking and initializing database...")
    db.init_db()

    # Write PID
    write_pid()

    # Signal handlers
    def shutdown_signal(signum, frame):
        print(f"\n[INFO] Received signal {signum}. Stopping server...")
        remove_pid()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_signal)
    signal.signal(signal.SIGTERM, shutdown_signal)

    # Allow address reuse
    ThreadingHTTPServer.allow_reuse_address = True
    server_address = (args.host, args.port)
    httpd = ThreadingHTTPServer(server_address, RecipeAppHandler)

    # Background thread to monitor .server_stop file
    import threading
    import time
    def stop_watcher():
        stop_trigger = BASE_DIR / ".server_stop"
        while True:
            if stop_trigger.exists():
                try:
                    stop_trigger.unlink()
                except Exception:
                    pass
                print("\n[INFO] Stop sentinel detected. Shutting down server...")
                remove_pid()
                os._exit(0)
            time.sleep(0.3)

    watcher_thread = threading.Thread(target=stop_watcher, daemon=True)
    watcher_thread.start()

    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host
    print("=" * 60)
    print(" 📖 RUSTIC RECIPE CARD MAKER & STORAGE SERVER 📖")
    print(f" Server running at: http://{display_host}:{args.port}")
    print(f" Database: {db.DB_PATH}")
    print(f" Process PID: {os.getpid()}")
    print(" Press Ctrl+C to stop the server.")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        remove_pid()
        httpd.server_close()
        print("[INFO] Server stopped gracefully.")


if __name__ == "__main__":
    main()
