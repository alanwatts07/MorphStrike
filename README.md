# MorphStrike Framework

A multi-agent communication framework for Claude Code controlled agents to collaborate on CTF challenges and penetration testing scenarios.

## Overview

MorphStrike enables multiple Claude Code instances to work together as coordinated agents across different VMs, sharing intelligence and coordinating attacks through a file-based communication system. The framework integrates with the HexStrike MCP server to provide access to 150+ cybersecurity tools.

## Features

- **Multi-Agent Architecture**: Giver and Taker agent roles for task distribution
- **File-Based Communication**: JSON message passing between agents
- **HexStrike Integration**: Access to 150+ cybersecurity tools via MCP server
- **CTF Automation**: Automated challenge analysis and solving
- **Cross-VM Deployment**: Deploy agents across multiple virtual machines
- **Real-Time Coordination**: Live task assignment and progress tracking
- **Intelligence Sharing**: Shared discovery database across all agents

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   VM 1      │    │   VM 2      │    │   VM 3      │
│   Server    │    │   Giver     │    │   Taker     │
│             │    │             │    │             │
│ ┌─────────┐ │    │ ┌─────────┐ │    │ ┌─────────┐ │
│ │ HTTP    │ │    │ │ Agent   │ │    │ │ Agent   │ │
│ │ Server  │◄┼────┼►│ Coord.  │ │    │ │ Exec.   │ │
│ │         │ │    │ │         │ │    │ │         │ │
│ └─────────┘ │    │ └─────────┘ │    │ └─────────┘ │
│             │    │             │    │             │
│ Shared Dir  │    │ HexStrike   │    │ HexStrike   │
│ /messages   │    │ Tools       │    │ Tools       │
│ /tasks      │    │             │    │             │
│ /discoveries│    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Installation

### Automatic Installation

Run the installation script on each VM:

```bash
chmod +x install.sh
sudo ./install.sh
```

### Manual Installation

1. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

2. Install system tools:
```bash
# Ubuntu/Debian
sudo apt-get install nmap gobuster nikto whatweb hydra sqlmap

# Or use the installation script with --skip-tools to skip this step
```

3. Install HexStrike MCP server:
```bash
git clone https://github.com/0x4m4/hexstrike-ai.git
cd hexstrike-ai
pip3 install -r requirements.txt
```

## Quick Start

### 1. Start the Communication Server

On your server VM:
```bash
python3 server_setup.py --shared-dir /opt/morphstrike/shared --port 8080
```

### 2. Deploy to Multiple VMs

Edit `deployment_config.yaml` with your VM details:
```yaml
vms:
  server:
    ip: "192.168.1.100"
    role: "server"
    ssh_user: "morpheus"
  giver:
    ip: "192.168.1.101"
    role: "giver"
    ssh_user: "morpheus"
  taker1:
    ip: "192.168.1.102"
    role: "taker"
    ssh_user: "morpheus"
```

Deploy to all VMs:
```bash
python3 deploy.py --deploy
```

### 3. Start CTF Session

Start a coordinated CTF session:
```bash
python3 deploy.py --start-ctf
```

Or manually start agents:

**Giver Agent (VM 2):**
```bash
python3 morphstrike_framework.py giver_01 giver /opt/morphstrike/shared 10.10.10.1
```

**Taker Agent (VM 3):**
```bash
python3 morphstrike_framework.py taker_01 taker /opt/morphstrike/shared
```

### 4. Monitor Progress

Monitor all agents:
```bash
python3 deploy.py --monitor
```

## Usage Examples

### Basic CTF Box Analysis

The Giver agent automatically creates tasks for target analysis:

```python
# Giver agent creates reconnaissance tasks
giver.analyze_ctf_box("10.10.10.5", "hackthebox_machine")

# Creates tasks:
# 1. Port scanning and service enumeration
# 2. Web application analysis (if HTTP found)
# 3. Vulnerability scanning
# 4. Exploitation attempts
```

### Custom Task Creation

```python
# Create a custom task
task_id = giver.create_task(
    "SQL Injection Testing",
    "Test the login form at http://10.10.10.5/login.php for SQL injection",
    "taker_01",
    "web",
    priority=3
)
```

### Sharing Discoveries

```python
# Taker agent shares a discovery
taker.add_discovery(
    "web",
    "Found admin panel at /admin.php",
    {
        "url": "http://10.10.10.5/admin.php",
        "status_code": 200,
        "requires_auth": True
    },
    confidence=0.9
)
```

### HexStrike Tool Integration

```python
# Use HexStrike tools
from hexstrike_integration import HexStrikeIntegration

hexstrike = HexStrikeIntegration("/opt/morphstrike/shared", "taker_01")

# Run reconnaissance suite
results = hexstrike.run_reconnaissance_suite("10.10.10.5")

# Run web analysis
web_results = hexstrike.run_web_analysis_suite("http://10.10.10.5")
```

## Configuration

### Agent Configuration

Edit `/opt/morphstrike/config.yaml`:

```yaml
agents:
  default_timeout: 300  # 5 minutes
  heartbeat_interval: 30  # seconds
  max_concurrent_tasks: 5

ctf:
  auto_escalation: true
  flag_patterns:
    - "flag{.*}"
    - "FLAG{.*}"
    - "CTF{.*}"
```

### Tool Configuration

Configure CTF-specific tool preferences:

```yaml
tools:
  wordlists:
    common: "/opt/morphstrike/wordlists/SecLists/Discovery/Web-Content/common.txt"
    directories: "/opt/morphstrike/wordlists/SecLists/Discovery/Web-Content/directory-list-2.3-medium.txt"
  
  timeouts:
    nmap: 600
    gobuster: 300
    nikto: 900
```

## File Structure

```
/opt/morphstrike/
├── morphstrike_framework.py     # Main agent framework
├── server_setup.py              # Communication server
├── hexstrike_integration.py     # HexStrike MCP integration
├── deploy.py                    # Deployment automation
├── config.yaml                  # Configuration file
├── shared/                      # Shared communication directory
│   ├── messages/               # Agent messages
│   ├── tasks/                  # Task definitions
│   ├── discoveries/            # Shared intelligence
│   ├── plans/                  # Coordination plans
│   ├── logs/                   # Agent logs
│   └── hexstrike_results/      # Tool execution results
├── hexstrike-ai/               # HexStrike MCP server
├── wordlists/                  # Security wordlists
│   ├── SecLists/
│   ├── fuzzdb/
│   └── PayloadsAllTheThings/
└── logs/                       # System logs
```

## Network Setup Options

### Option 1: NFS (Recommended for Linux)

Server VM:
```bash
sudo apt-get install nfs-kernel-server
echo "/opt/morphstrike/shared *(rw,sync,no_subtree_check)" >> /etc/exports
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
```

Client VMs:
```bash
sudo apt-get install nfs-common
sudo mount -t nfs server_ip:/opt/morphstrike/shared /opt/morphstrike/shared
```

### Option 2: Samba (Cross-platform)

Server VM:
```bash
sudo apt-get install samba
# Add share configuration to /etc/samba/smb.conf
sudo systemctl restart smbd
```

Client VMs:
```bash
sudo apt-get install cifs-utils
sudo mount -t cifs //server_ip/morphstrike /opt/morphstrike/shared
```

### Option 3: HTTP Server (Firewall-friendly)

Use the built-in HTTP server for communication:
```bash
python3 server_setup.py --shared-dir /opt/morphstrike/shared --port 8080
```

## Security Considerations

1. **Network Isolation**: Run in isolated lab environments only
2. **Access Control**: Limit SSH and file sharing to lab networks
3. **Tool Validation**: All HexStrike tools are sandboxed and logged
4. **Audit Trail**: Complete logging of all agent activities
5. **CTF Only**: Framework designed for defensive security training

## Advanced Features

### Automated CTF Solving

```python
from hexstrike_integration import CTFAutomation

automation = CTFAutomation(hexstrike_integration)
challenge_type = automation.analyze_challenge_type("Web application challenge")
results = automation.solve_challenge(challenge_type, "http://10.10.10.5")
```

### Custom Agent Roles

Create specialized agents by extending the base classes:

```python
class ForensicsAgent(CTFTakerAgent):
    def execute_forensics_task(self, task_id, evidence_file):
        # Custom forensics analysis
        pass

class WebExploitAgent(CTFTakerAgent):
    def execute_web_exploit(self, task_id, target_url):
        # Specialized web exploitation
        pass
```

### Distributed Coordination

Agents automatically coordinate based on discoveries:

```python
# When a web service is discovered, automatically trigger web analysis
if "80" in discovered_ports:
    giver.create_task("Web Analysis", f"Analyze web app on {target}", "web_specialist")
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Check SSH keys and network connectivity
   - Verify firewall rules allow SSH (port 22)

2. **Shared Directory Not Accessible**
   - Check NFS/Samba server status
   - Verify mount permissions and network connectivity

3. **Agents Not Communicating**
   - Check shared directory permissions
   - Verify file system is mounted read-write

4. **HexStrike Tools Not Found**
   - Install missing tools using package manager
   - Check PATH environment variable

### Debug Mode

Enable debug logging:
```bash
export MORPHSTRIKE_DEBUG=1
python3 morphstrike_framework.py debug giver /opt/morphstrike/shared
```

### Log Analysis

Check agent logs:
```bash
tail -f /opt/morphstrike/shared/logs/agent_*.log
```

Check server logs:
```bash
tail -f /opt/morphstrike/shared/server.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Disclaimer

This framework is designed for educational purposes and authorized penetration testing only. Users are responsible for ensuring compliance with applicable laws and regulations.