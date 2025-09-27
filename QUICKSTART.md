# MorphStrike Quick Start Guide

## Step-by-Step Setup for Two VMs

### Prerequisites
- Two VMs or machines with network connectivity
- Python 3.6+ installed on both
- SSH access between machines (optional for file sharing)

## Method 1: Simple HTTP File Sharing (Easiest)

### Step 1: Setup VM1 (Server + Giver)

1. **Install MorphStrike on VM1:**
   ```bash
   cd /home/morpheus/MorphStrike
   ./install.sh --skip-tools  # Skip heavy tools for quick setup
   ```

2. **Start the file sharing server:**
   ```bash
   python3 server_setup.py --shared-dir ./morphstrike_shared --port 8080
   ```
   
   This will show you connection URLs like:
   ```
   Agent Connection URLs:
     http://192.168.1.100:8080/
     http://127.0.0.1:8080/
   ```
   Note the IP address (e.g., 192.168.1.100) - you'll need this for VM2.

3. **In a new terminal on VM1, start the Giver agent:**
   ```bash
   python3 morphstrike_framework.py giver_01 giver ./morphstrike_shared
   ```

### Step 2: Setup VM2 (Taker)

1. **Copy MorphStrike files to VM2:**
   ```bash
   # On VM2, download or copy the framework files
   scp user@vm1:/home/morpheus/MorphStrike/*.py ./
   ```

2. **Install basic dependencies:**
   ```bash
   pip3 install requests pyyaml
   ```

3. **Create a local shared directory that syncs with VM1:**
   ```bash
   mkdir ./morphstrike_shared
   ```

4. **Start the Taker agent pointing to VM1's server:**
   ```bash
   # Replace 192.168.1.100 with VM1's actual IP
   python3 morphstrike_framework.py taker_01 taker http://192.168.1.100:8080/
   ```

### Step 3: Test the Connection

1. **On VM1 (Giver), create a test task:**
   ```bash
   # The giver should automatically detect the taker and create tasks
   # Or you can create a manual task by modifying the framework
   ```

2. **Check the shared directory:**
   ```bash
   ls -la ./morphstrike_shared/
   # You should see: messages/ tasks/ discoveries/ plans/ logs/
   ```

3. **Monitor logs:**
   ```bash
   tail -f ./morphstrike_shared/agent_*.log
   ```

## Method 2: Shared Folder (If VMs can share folders)

### Step 1: Create Shared Folder

If your VMs can share a folder (VMware shared folders, VirtualBox shared folders, etc.):

1. **Create shared folder accessible to both VMs:**
   ```bash
   mkdir /shared/morphstrike_shared
   # Or use your hypervisor's shared folder feature
   ```

### Step 2: Start Agents

1. **On VM1 (Giver):**
   ```bash
   python3 morphstrike_framework.py giver_01 giver /shared/morphstrike_shared 10.10.10.5
   ```
   Replace `10.10.10.5` with your CTF target IP.

2. **On VM2 (Taker):**
   ```bash
   python3 morphstrike_framework.py taker_01 taker /shared/morphstrike_shared
   ```

## Step 3: Add a CTF Target

Once both agents are running, start a CTF analysis:

1. **On VM1, modify the giver to analyze a target:**
   ```bash
   # Edit the morphstrike_framework.py file and add at the bottom:
   # agent.analyze_ctf_box("10.10.10.5", "test_target")
   ```

Or create a simple test script:

```python
# test_ctf.py
from morphstrike_framework import CTFGiverAgent
import time

# Create giver agent
giver = CTFGiverAgent("giver_01", "./morphstrike_shared")
giver.start_message_listener()

# Analyze a CTF box
giver.analyze_ctf_box("10.10.10.5", "hackthebox")

print("CTF analysis started. Check logs for progress.")
time.sleep(60)  # Let it run for a minute
```

## Troubleshooting

### Problem: "No such file or directory"
**Solution:** Make sure the shared directory exists and has write permissions:
```bash
mkdir -p ./morphstrike_shared
chmod 755 ./morphstrike_shared
```

### Problem: "Connection refused" 
**Solution:** Check if the server is running and firewall allows port 8080:
```bash
# Check if server is running
netstat -ln | grep 8080

# Allow port through firewall (Ubuntu)
sudo ufw allow 8080
```

### Problem: Agents not communicating
**Solution:** Check the shared directory has the right structure:
```bash
ls -la ./morphstrike_shared/
# Should show: messages/ tasks/ discoveries/ plans/ logs/
```

### Problem: Python import errors
**Solution:** Install missing dependencies:
```bash
pip3 install requests pyyaml pathlib dataclasses
```

## Verify It's Working

You'll know it's working when you see:

1. **Log messages** in `./morphstrike_shared/agent_*.log`
2. **Task files** in `./morphstrike_shared/tasks/`
3. **Message files** in `./morphstrike_shared/messages/`
4. **Discovery files** in `./morphstrike_shared/discoveries/`

Example successful output:
```
[INFO] MorphStrike-giver_01 - Message listener started
[INFO] MorphStrike-giver_01 - Created CTF analysis plan for hackthebox (10.10.10.5)
[INFO] MorphStrike-giver_01 - Created task abc123: Initial Reconnaissance - hackthebox
[INFO] MorphStrike-taker_01 - Received task_assignment from giver_01
[INFO] MorphStrike-taker_01 - Executing recon task abc123
```

## Next Steps

Once basic communication works:

1. **Install CTF tools:**
   ```bash
   ./install.sh  # Full installation with tools
   ```

2. **Add HexStrike integration:**
   ```bash
   git clone https://github.com/0x4m4/hexstrike-ai.git
   cd hexstrike-ai
   pip3 install -r requirements.txt
   ```

3. **Scale to more agents** by repeating the VM2 setup on additional machines

## Manual Testing Commands

Test the framework manually:

```bash
# Start server
python3 server_setup.py --shared-dir ./test_shared --port 8080

# In another terminal - start giver
python3 morphstrike_framework.py test_giver giver ./test_shared

# In another terminal - start taker  
python3 morphstrike_framework.py test_taker taker ./test_shared

# Check communication
ls ./test_shared/messages/
ls ./test_shared/tasks/
```