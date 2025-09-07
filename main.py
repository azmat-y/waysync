import socket
import subprocess
import argparse
import threading

parser = argparse.ArgumentParser(description="Share clipboard over TCP.")
parser.add_argument(
    "mode", choices=["server", "client"], help="Run as 'server' or 'client'"
)
parser.add_argument(
    "--host",
    default="0.0.0.0",
    help="Host IP address to bind/connect to (server) or connect to (client).",
)
parser.add_argument(
    "--port", type=int, default=12345, help="Port to use for the connection."
)
args = parser.parse_args()
HOST = args.host
PORT = args.port
POLL_INTERVAL = 1


class ClipboardHandler:
    """
    A class to handle getting and setting clipboard content using wl-paste and wl-copy.
    """

    def __init__(self):
        self.last_clipboard = self.get_clipboard()

    def get_clipboard(self):
        """Get the current content of the clipboard using wl-paste."""
        try:
            return subprocess.check_output(["wl-paste"], text=True).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Warning: 'wl-paste' command not found. Clipboard can't be read.")
            return ""

    def set_clipboard(self, content):
        """Set the content of the clipboard using wl-copy."""
        try:
            subprocess.run(["wl-copy"], text=True, input=content, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Warning: 'wl-copy' command not found. Clipboard can't be set.")


def handle_client(conn, addr, clipboard_handler):
    """
    Handles communication with a connected client in a separate thread.
    This function runs on the server.
    """
    print(f"Connected by {addr}")
    try:
        while True:
            # Check for local clipboard changes to send to the client
            current_clipboard = clipboard_handler.get_clipboard()
            if current_clipboard != clipboard_handler.last_clipboard:
                print("Local clipboard changed. Sending update to client.")
                conn.sendall(current_clipboard.encode("utf-8"))
                clipboard_handler.last_clipboard = current_clipboard

            conn.settimeout(POLL_INTERVAL)
            try:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break  # Connection closed by client

                if data != clipboard_handler.last_clipboard:
                    print("Received update from client. Updating local clipboard.")
                    clipboard_handler.set_clipboard(data)
                    clipboard_handler.last_clipboard = data
            except socket.timeout:
                continue

    except (ConnectionResetError, BrokenPipeError):
        print(f"Connection with {addr} was lost.")
    finally:
        print(f"Closing connection with {addr}.")
        conn.close()


def run_server(clipboard_handler):
    """
    Starts the TCP server to listen for incoming connections.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(conn, addr, clipboard_handler)
            )
            client_thread.daemon = True
            client_thread.start()


def run_client(clipboard_handler):
    """
    Connects to the TCP server and synchronizes the clipboard.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"Connected to server at {HOST}:{PORT}")
        except ConnectionRefusedError:
            print(f"Error: Connection refused. Is the server running at {HOST}:{PORT}?")
            return

        while True:
            try:
                # Send local clipboard changes to the server
                current_clipboard = clipboard_handler.get_clipboard()
                if current_clipboard != clipboard_handler.last_clipboard:
                    print("Local clipboard changed. Sending update to server.")
                    s.sendall(current_clipboard.encode("utf-8"))
                    clipboard_handler.last_clipboard = current_clipboard

                # Receive clipboard updates from the server (with a timeout)
                s.settimeout(POLL_INTERVAL)
                try:
                    data = s.recv(4096).decode("utf-8")
                    if data and data != clipboard_handler.last_clipboard:
                        print("Received update from server. Updating local clipboard.")
                        clipboard_handler.set_clipboard(data)
                        clipboard_handler.last_clipboard = data
                except socket.timeout:
                    continue  # No data received, continue polling

            except (ConnectionResetError, BrokenPipeError):
                print("Connection to server lost. Exiting.")
                break


if __name__ == "__main__":
    clipboard_handler = ClipboardHandler()

    if args.mode == "server":
        try:
            run_server(clipboard_handler)
        except KeyboardInterrupt:
            print("\nShutting down server.")
    elif args.mode == "client":
        try:
            run_client(clipboard_handler)
        except KeyboardInterrupt:
            print("\nExiting client.")
