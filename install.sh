#!/bin/bash

# MorphStrike Framework Installation Script
# Installs dependencies and sets up the multi-agent CTF framework

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/morphstrike"
USER_HOME="$HOME"

echo "==============================================="
echo "   MorphStrike Framework Installation"
echo "==============================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system-wide installation
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_info "Running as root - installing system-wide"
        INSTALL_DIR="/opt/morphstrike"
    else
        log_info "Running as user - installing to home directory"
        INSTALL_DIR="$USER_HOME/.morphstrike"
    fi
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 not found. Please install Python 3 and pip3 first."
        exit 1
    fi
    
    # Create requirements.txt if it doesn't exist
    cat > "$SCRIPT_DIR/requirements.txt" << EOF
requests>=2.25.1
pyyaml>=5.4.1
asyncio>=3.4.3
aiofiles>=0.7.0
websockets>=9.1
pathlib>=1.0.1
dataclasses>=0.6
uuid>=1.30
logging>=0.4.9.6
threading>=1.0
socketserver>=0.4
http.server>=0.6
json>=2.0.9
datetime>=4.3
enum34>=1.1.10
argparse>=1.4.0
tempfile>=1.0
subprocess>=1.0
signal>=1.0
os>=1.0
sys>=1.0
time>=1.0
EOF

    pip3 install --user -r "$SCRIPT_DIR/requirements.txt"
    log_success "Python dependencies installed"
}

# Install system tools commonly used in CTF
install_system_tools() {
    log_info "Installing system tools for CTF..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y \
            nmap \
            masscan \
            nikto \
            dirb \
            gobuster \
            whatweb \
            curl \
            wget \
            netcat \
            socat \
            john \
            hashcat \
            binwalk \
            foremost \
            strings \
            file \
            exiftool \
            steghide \
            stegosuite \
            wireshark \
            tshark \
            aircrack-ng \
            sqlmap \
            wfuzz \
            ffuf \
            hydra \
            metasploit-framework \
            exploitdb \
            searchsploit \
            enum4linux \
            smbclient \
            rpcclient \
            nbtscan \
            onesixtyone \
            snmpwalk \
            dnsrecon \
            fierce \
            theharvester \
            recon-ng \
            maltego \
            volatility \
            autopsy \
            sleuthkit \
            gdb \
            radare2 \
            ghidra \
            burpsuite \
            zaproxy \
            dirbuster \
            wpscan \
            joomscan \
            nuclei \
            subfinder \
            assetfinder \
            amass \
            rustscan \
            feroxbuster
            
    elif command -v yum &> /dev/null; then
        # RedHat/CentOS/Fedora
        sudo yum install -y epel-release
        sudo yum install -y \
            nmap \
            nikto \
            dirb \
            curl \
            wget \
            nc \
            john \
            hashcat \
            binwalk \
            foremost \
            strings \
            file \
            exiftool \
            wireshark \
            aircrack-ng \
            sqlmap \
            hydra \
            enum4linux \
            smbclient
            
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S --noconfirm \
            nmap \
            masscan \
            nikto \
            dirb \
            gobuster \
            curl \
            wget \
            netcat \
            john \
            hashcat \
            binwalk \
            foremost \
            strings \
            file \
            exiftool \
            wireshark-cli \
            aircrack-ng \
            sqlmap \
            hydra \
            enum4linux \
            smbclient
    else
        log_warning "Package manager not detected. Please install CTF tools manually."
    fi
    
    log_success "System tools installation completed"
}

# Install HexStrike MCP server
install_hexstrike() {
    log_info "Installing HexStrike MCP server..."
    
    HEXSTRIKE_DIR="$INSTALL_DIR/hexstrike-ai"
    
    if [ -d "$HEXSTRIKE_DIR" ]; then
        log_info "HexStrike already exists, updating..."
        cd "$HEXSTRIKE_DIR"
        git pull
    else
        log_info "Cloning HexStrike repository..."
        git clone https://github.com/0x4m4/hexstrike-ai.git "$HEXSTRIKE_DIR"
    fi
    
    cd "$HEXSTRIKE_DIR"
    
    # Install HexStrike dependencies
    if [ -f "requirements.txt" ]; then
        pip3 install --user -r requirements.txt
    fi
    
    log_success "HexStrike MCP server installed"
}

# Install wordlists
install_wordlists() {
    log_info "Installing common wordlists..."
    
    WORDLISTS_DIR="$INSTALL_DIR/wordlists"
    mkdir -p "$WORDLISTS_DIR"
    
    # SecLists
    if [ ! -d "$WORDLISTS_DIR/SecLists" ]; then
        log_info "Installing SecLists..."
        git clone https://github.com/danielmiessler/SecLists.git "$WORDLISTS_DIR/SecLists"
    fi
    
    # FuzzDB
    if [ ! -d "$WORDLISTS_DIR/fuzzdb" ]; then
        log_info "Installing FuzzDB..."
        git clone https://github.com/fuzzdb-project/fuzzdb.git "$WORDLISTS_DIR/fuzzdb"
    fi
    
    # PayloadsAllTheThings
    if [ ! -d "$WORDLISTS_DIR/PayloadsAllTheThings" ]; then
        log_info "Installing PayloadsAllTheThings..."
        git clone https://github.com/swisskyrepo/PayloadsAllTheThings.git "$WORDLISTS_DIR/PayloadsAllTheThings"
    fi
    
    log_success "Wordlists installed"
}

# Setup MorphStrike framework
setup_framework() {
    log_info "Setting up MorphStrike framework..."
    
    mkdir -p "$INSTALL_DIR"
    
    # Copy framework files
    cp "$SCRIPT_DIR/morphstrike_framework.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/server_setup.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/hexstrike_integration.py" "$INSTALL_DIR/"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/morphstrike_framework.py"
    chmod +x "$INSTALL_DIR/server_setup.py"
    chmod +x "$INSTALL_DIR/hexstrike_integration.py"
    
    # Create shared directory structure
    SHARED_DIR="$INSTALL_DIR/shared"
    mkdir -p "$SHARED_DIR"/{messages,tasks,discoveries,plans,logs,tools,hexstrike_results}
    
    log_success "MorphStrike framework setup completed"
}

# Create system service files
create_services() {
    log_info "Creating systemd service files..."
    
    if [[ $EUID -eq 0 ]]; then
        # Server service
        cat > /etc/systemd/system/morphstrike-server.service << EOF
[Unit]
Description=MorphStrike Communication Server
After=network.target

[Service]
Type=simple
User=morphstrike
Group=morphstrike
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/server_setup.py --shared-dir $INSTALL_DIR/shared --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        # Create morphstrike user
        if ! id "morphstrike" &>/dev/null; then
            useradd -r -s /bin/false morphstrike
            chown -R morphstrike:morphstrike "$INSTALL_DIR"
        fi
        
        systemctl daemon-reload
        log_success "System services created"
    else
        log_warning "Not running as root - skipping system service creation"
    fi
}

# Create CLI shortcuts
create_shortcuts() {
    log_info "Creating CLI shortcuts..."
    
    BIN_DIR="$USER_HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    
    # MorphStrike command
    cat > "$BIN_DIR/morphstrike" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 "$INSTALL_DIR/morphstrike_framework.py" "\$@"
EOF

    # MorphStrike server command
    cat > "$BIN_DIR/morphstrike-server" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 "$INSTALL_DIR/server_setup.py" "\$@"
EOF

    # HexStrike integration command
    cat > "$BIN_DIR/morphstrike-hex" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 "$INSTALL_DIR/hexstrike_integration.py" "\$@"
EOF

    chmod +x "$BIN_DIR/morphstrike"
    chmod +x "$BIN_DIR/morphstrike-server"
    chmod +x "$BIN_DIR/morphstrike-hex"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$USER_HOME/.bashrc"
        log_info "Added $BIN_DIR to PATH in .bashrc"
    fi
    
    log_success "CLI shortcuts created"
}

# Create configuration file
create_config() {
    log_info "Creating configuration file..."
    
    cat > "$INSTALL_DIR/config.yaml" << EOF
# MorphStrike Framework Configuration

installation:
  install_dir: "$INSTALL_DIR"
  shared_dir: "$INSTALL_DIR/shared"
  wordlists_dir: "$INSTALL_DIR/wordlists"
  hexstrike_dir: "$INSTALL_DIR/hexstrike-ai"

server:
  default_port: 8080
  default_host: "0.0.0.0"
  max_agents: 10
  message_retention_hours: 168  # 1 week
  log_level: "INFO"

agents:
  default_timeout: 300  # 5 minutes
  heartbeat_interval: 30  # seconds
  max_concurrent_tasks: 5

ctf:
  categories:
    - reconnaissance
    - web
    - exploitation
    - post_exploitation
    - forensics
    - crypto
    - reverse_engineering
    - steganography
  
  auto_escalation: true
  flag_patterns:
    - "flag{.*}"
    - "FLAG{.*}"
    - "CTF{.*}"
    - "[a-f0-9]{32}"  # MD5
    - "[a-f0-9]{64}"  # SHA256

tools:
  wordlists:
    common: "$INSTALL_DIR/wordlists/SecLists/Discovery/Web-Content/common.txt"
    directories: "$INSTALL_DIR/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt"
    files: "$INSTALL_DIR/wordlists/SecLists/Discovery/Web-Content/raft-medium-files.txt"
    passwords: "$INSTALL_DIR/wordlists/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000.txt"
  
  timeouts:
    nmap: 600
    gobuster: 300
    nikto: 900
    sqlmap: 1200
EOF

    log_success "Configuration file created"
}

# Print usage instructions
print_usage() {
    echo ""
    echo "==============================================="
    echo "   MorphStrike Installation Complete!"
    echo "==============================================="
    echo ""
    echo "Installation Directory: $INSTALL_DIR"
    echo ""
    echo "Quick Start Commands:"
    echo ""
    echo "1. Start the communication server:"
    echo "   morphstrike-server --shared-dir $INSTALL_DIR/shared"
    echo ""
    echo "2. Start a Giver agent (on VM 1):"
    echo "   morphstrike giver_01 giver $INSTALL_DIR/shared <target_ip>"
    echo ""
    echo "3. Start a Taker agent (on VM 2):"
    echo "   morphstrike taker_01 taker $INSTALL_DIR/shared"
    echo ""
    echo "4. Test HexStrike integration:"
    echo "   morphstrike-hex $INSTALL_DIR/shared test_agent <target_ip>"
    echo ""
    echo "Configuration file: $INSTALL_DIR/config.yaml"
    echo "Logs directory: $INSTALL_DIR/shared/logs/"
    echo ""
    echo "For multi-VM setup:"
    echo "1. Install on each VM using this script"
    echo "2. Setup network file sharing (NFS/Samba) for $INSTALL_DIR/shared"
    echo "3. Or use the built-in HTTP server for communication"
    echo ""
    echo "Documentation and examples: $INSTALL_DIR/README.md"
    echo ""
}

# Main installation function
main() {
    log_info "Starting MorphStrike installation..."
    
    check_permissions
    install_python_deps
    install_system_tools
    setup_framework
    install_hexstrike
    install_wordlists
    create_services
    create_shortcuts
    create_config
    
    log_success "Installation completed successfully!"
    print_usage
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tools)
            SKIP_TOOLS=true
            shift
            ;;
        --skip-hexstrike)
            SKIP_HEXSTRIKE=true
            shift
            ;;
        --skip-wordlists)
            SKIP_WORDLISTS=true
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "MorphStrike Installation Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-tools       Skip system tools installation"
            echo "  --skip-hexstrike   Skip HexStrike MCP server installation"
            echo "  --skip-wordlists   Skip wordlists installation"
            echo "  --install-dir DIR  Custom installation directory"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main installation
main