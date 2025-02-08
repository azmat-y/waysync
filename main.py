import os
import time
import subprocess
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

parser = argparse.ArgumentParser()
parser.add_argument("path", help="Path to shared file")
args = parser.parse_args()

target_dir = args.path
if not Path(target_dir).exists():
    parser.exit(1, "Invalid path\n")

# Shared file path, It may be different for guest and host
SHARED_FILE = target_dir
POLL_INTERVAL = 1  # Seconds between clipboard checks


class SharedClipboardHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_clipboard = self.get_clipboard()
        self.last_file_content = self.read_shared_file()
        self.last_file_mtime = (
            os.path.getmtime(SHARED_FILE) if os.path.exists(SHARED_FILE) else 0
        )

    def get_clipboard(self):
        try:
            return subprocess.check_output(["wl-paste"], text=True).strip()
        except:
            return ""

    def set_clipboard(self, content):
        subprocess.run(["wl-copy"], text=True, input=content)

    def read_shared_file(self):
        try:
            with open(SHARED_FILE, "r") as f:
                return f.read().strip()
        except:
            return ""

    def write_shared_file(self, content):
        with open(SHARED_FILE, "w") as f:
            f.write(content)

    def on_modified(self, event):
        if event.src_path == SHARED_FILE:
            # Shared file changed: update local clipboard
            new_content = self.read_shared_file()
            if new_content != self.last_clipboard:
                self.set_clipboard(new_content)
                self.last_clipboard = new_content
                print("Clipboard updated from shared file.")

    def sync_clipboard_to_file(self):
        # Check local clipboard changes
        current_clipboard = self.get_clipboard()
        if current_clipboard != self.last_clipboard:
            self.write_shared_file(current_clipboard)
            self.last_clipboard = current_clipboard
            print("Shared file updated from clipboard.")

    def sync_file_to_clipboard(self):
        # Check shared file changes (fallback if watchdog misses events)
        if not os.path.exists(SHARED_FILE):
            return
        current_mtime = os.path.getmtime(SHARED_FILE)
        if current_mtime > self.last_file_mtime:
            new_content = self.read_shared_file()
            if new_content != self.last_clipboard:
                self.set_clipboard(new_content)
                self.last_clipboard = new_content
                self.last_file_mtime = current_mtime
                print("Clipboard updated from shared file (fallback).")


if __name__ == "__main__":
    event_handler = SharedClipboardHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(SHARED_FILE), recursive=False)
    observer.start()

    try:
        while True:
            event_handler.sync_clipboard_to_file()  # Local -> Shared
            event_handler.sync_file_to_clipboard()  # Shared -> Local
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
