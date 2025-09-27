#!/usr/bin/env python3
"""
MorphStrike Server Setup
Creates a local file server for multi-VM agent communication
"""

import os
import socket
import threading
import http.server
import socketserver
from pathlib import Path
import json
import argparse
import logging
from typing import Dict, List

class MorphStrikeHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for agent file sharing"""
    
    def __init__(self, *args, shared_dir=None, **kwargs):
        self.shared_dir = shared_dir
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for file retrieval"""
        # Set CORS headers for cross-origin requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Serve files from shared directory
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests for file uploads"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Extract file path from URL
        file_path = self.path.lstrip('/')
        full_path = Path(self.shared_dir) / file_path
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, 'wb') as f:
            f.write(post_data)
        
        self.send_response(201)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'File uploaded successfully')

class MorphStrikeServer:
    """Local server for agent communication"""
    
    def __init__(self, shared_dir: str, port: int = 8080, host: str = '0.0.0.0'):
        self.shared_dir = Path(shared_dir)
        self.port = port
        self.host = host
        self.server = None
        
        # Ensure shared directory exists
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        log_file = self.shared_dir / "server.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("MorphStrike-Server")
        
        # Initialize directory structure
        self._init_directory_structure()
    
    def _init_directory_structure(self):
        """Initialize the shared directory structure"""
        subdirs = ['messages', 'tasks', 'discoveries', 'plans', 'logs', 'tools']
        for subdir in subdirs:
            (self.shared_dir / subdir).mkdir(exist_ok=True)
        
        # Create server info file
        server_info = {
            'host': self.host,
            'port': self.port,
            'shared_dir': str(self.shared_dir),
            'subdirectories': subdirs,
            'setup_time': str(datetime.now())
        }
        
        with open(self.shared_dir / 'server_info.json', 'w') as f:
            json.dump(server_info, f, indent=2)
    
    def start(self):
        """Start the HTTP server"""
        os.chdir(self.shared_dir)
        
        # Create handler with shared directory
        handler = lambda *args, **kwargs: MorphStrikeHTTPHandler(
            *args, shared_dir=self.shared_dir, **kwargs
        )
        
        self.server = socketserver.TCPServer((self.host, self.port), handler)
        self.server.allow_reuse_address = True
        
        self.logger.info(f"MorphStrike server starting on {self.host}:{self.port}")
        self.logger.info(f"Shared directory: {self.shared_dir}")
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server_thread
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.logger.info("MorphStrike server stopped")
    
    def get_network_interfaces(self) -> List[str]:
        """Get available network interfaces"""
        interfaces = []
        hostname = socket.gethostname()
        
        # Get all IP addresses
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            interfaces.append(local_ip)
        except:
            pass
        
        # Add localhost
        interfaces.append('127.0.0.1')
        
        return interfaces
    
    def print_connection_info(self):
        """Print connection information for agents"""
        interfaces = self.get_network_interfaces()
        
        print("\n" + "="*60)
        print("MorphStrike Server Connection Information")
        print("="*60)
        print(f"Shared Directory: {self.shared_dir}")
        print(f"Port: {self.port}")
        print("\nAgent Connection URLs:")
        
        for interface in interfaces:
            print(f"  http://{interface}:{self.port}/")
        
        print("\nDirectory Structure:")
        for item in self.shared_dir.iterdir():
            if item.is_dir():
                print(f"  📁 {item.name}/")
            else:
                print(f"  📄 {item.name}")
        
        print("\nAgent Setup Commands:")
        print("For Giver Agent:")
        for interface in interfaces:
            print(f"  python morphstrike_framework.py giver_01 giver http://{interface}:{self.port}/ <target_ip>")
        
        print("\nFor Taker Agent:")
        for interface in interfaces:
            print(f"  python morphstrike_framework.py taker_01 taker http://{interface}:{self.port}/")
        
        print("="*60)

def setup_samba_share(shared_dir: str, share_name: str = "morphstrike"):
    """Setup Samba share for Windows/Linux file sharing"""
    samba_config = f"""
[{share_name}]
path = {shared_dir}
browseable = yes
read only = no
guest ok = yes
create mask = 0777
directory mask = 0777
force user = nobody
force group = nogroup
"""
    
    print(f"\nTo setup Samba share, add this to /etc/samba/smb.conf:")
    print(samba_config)
    print("Then restart Samba: sudo systemctl restart smbd")

def setup_nfs_share(shared_dir: str):
    """Setup NFS share for Linux file sharing"""
    exports_entry = f"{shared_dir} *(rw,sync,no_subtree_check,all_squash,anonuid=65534,anongid=65534)"
    
    print(f"\nTo setup NFS share, add this to /etc/exports:")
    print(exports_entry)
    print("Then restart NFS: sudo systemctl restart nfs-kernel-server")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MorphStrike Server Setup")
    parser.add_argument("--shared-dir", default="./morphstrike_shared", 
                       help="Shared directory path")
    parser.add_argument("--port", type=int, default=8080, 
                       help="Server port")
    parser.add_argument("--host", default="0.0.0.0", 
                       help="Server host")
    parser.add_argument("--setup-samba", action="store_true", 
                       help="Show Samba setup instructions")
    parser.add_argument("--setup-nfs", action="store_true", 
                       help="Show NFS setup instructions")
    
    args = parser.parse_args()
    
    # Create and start server
    server = MorphStrikeServer(args.shared_dir, args.port, args.host)
    
    try:
        server_thread = server.start()
        server.print_connection_info()
        
        if args.setup_samba:
            setup_samba_share(str(server.shared_dir))
        
        if args.setup_nfs:
            setup_nfs_share(str(server.shared_dir))
        
        print("\nPress Ctrl+C to stop the server...")
        
        # Keep the main thread alive
        while True:
            try:
                server_thread.join(1)
                if not server_thread.is_alive():
                    break
            except KeyboardInterrupt:
                break
    
    except KeyboardInterrupt:
        print("\nShutting down server...")
    
    finally:
        server.stop()