#!/usr/bin/env python3
"""
MorphStrike Deployment Script
Automated deployment and configuration for multi-VM CTF environments
"""

import os
import sys
import json
import yaml
import subprocess
import argparse
import socket
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

class MorphStrikeDeployer:
    """Automated deployment manager for MorphStrike framework"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "deployment_config.yaml"
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self) -> Dict:
        """Load deployment configuration"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default config
            default_config = {
                "deployment": {
                    "install_dir": "/opt/morphstrike",
                    "shared_dir": "/opt/morphstrike/shared",
                    "server_port": 8080,
                    "agent_check_interval": 30
                },
                "vms": {
                    "server": {
                        "ip": "192.168.1.100",
                        "role": "server",
                        "ssh_user": "morpheus",
                        "ssh_key": "~/.ssh/id_rsa"
                    },
                    "giver": {
                        "ip": "192.168.1.101", 
                        "role": "giver",
                        "ssh_user": "morpheus",
                        "ssh_key": "~/.ssh/id_rsa"
                    },
                    "taker1": {
                        "ip": "192.168.1.102",
                        "role": "taker",
                        "ssh_user": "morpheus", 
                        "ssh_key": "~/.ssh/id_rsa"
                    }
                },
                "network": {
                    "share_type": "nfs",  # nfs, samba, http
                    "nfs_export": "/opt/morphstrike/shared",
                    "samba_share": "morphstrike"
                },
                "ctf": {
                    "target_networks": ["10.10.10.0/24", "192.168.100.0/24"],
                    "auto_start": True,
                    "coordination_mode": "automated"
                }
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            print(f"Created default config: {self.config_file}")
            print("Please edit the configuration and run again.")
            sys.exit(1)
            
        return {}
    
    def setup_logging(self):
        """Setup logging for deployment"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('morphstrike_deployment.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("MorphStrike-Deploy")
    
    def check_ssh_connectivity(self, vm_config: Dict) -> bool:
        """Check SSH connectivity to a VM"""
        try:
            cmd = [
                "ssh", 
                "-o", "ConnectTimeout=10",
                "-o", "StrictHostKeyChecking=no",
                f"{vm_config['ssh_user']}@{vm_config['ip']}",
                "echo 'SSH OK'"
            ]
            
            if 'ssh_key' in vm_config:
                cmd.extend(["-i", os.path.expanduser(vm_config['ssh_key'])])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"SSH check failed for {vm_config['ip']}: {e}")
            return False
    
    def deploy_to_vm(self, vm_name: str, vm_config: Dict) -> bool:
        """Deploy MorphStrike to a specific VM"""
        self.logger.info(f"Deploying to {vm_name} ({vm_config['ip']})...")
        
        if not self.check_ssh_connectivity(vm_config):
            self.logger.error(f"Cannot connect to {vm_name}")
            return False
        
        try:
            # Create remote directory
            self._run_ssh_command(vm_config, f"sudo mkdir -p {self.config['deployment']['install_dir']}")
            
            # Copy installation files
            self._copy_files_to_vm(vm_config)
            
            # Run installation script
            install_cmd = f"cd {self.config['deployment']['install_dir']} && sudo bash install.sh"
            self._run_ssh_command(vm_config, install_cmd)
            
            # Configure based on role
            if vm_config['role'] == 'server':
                self._configure_server(vm_config)
            elif vm_config['role'] == 'giver':
                self._configure_giver(vm_config)
            elif vm_config['role'] == 'taker':
                self._configure_taker(vm_config)
            
            self.logger.info(f"Successfully deployed to {vm_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment failed for {vm_name}: {e}")
            return False
    
    def _run_ssh_command(self, vm_config: Dict, command: str) -> str:
        """Run a command via SSH"""
        ssh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            f"{vm_config['ssh_user']}@{vm_config['ip']}"
        ]
        
        if 'ssh_key' in vm_config:
            ssh_cmd.extend(["-i", os.path.expanduser(vm_config['ssh_key'])])
        
        ssh_cmd.append(command)
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise Exception(f"SSH command failed: {result.stderr}")
        
        return result.stdout
    
    def _copy_files_to_vm(self, vm_config: Dict):
        """Copy MorphStrike files to VM"""
        files_to_copy = [
            "morphstrike_framework.py",
            "server_setup.py", 
            "hexstrike_integration.py",
            "install.sh",
            "requirements.txt"
        ]
        
        for filename in files_to_copy:
            if Path(filename).exists():
                scp_cmd = [
                    "scp",
                    "-o", "StrictHostKeyChecking=no"
                ]
                
                if 'ssh_key' in vm_config:
                    scp_cmd.extend(["-i", os.path.expanduser(vm_config['ssh_key'])])
                
                scp_cmd.extend([
                    filename,
                    f"{vm_config['ssh_user']}@{vm_config['ip']}:{self.config['deployment']['install_dir']}/"
                ])
                
                subprocess.run(scp_cmd, check=True)
    
    def _configure_server(self, vm_config: Dict):
        """Configure the communication server VM"""
        self.logger.info("Configuring server VM...")
        
        # Setup network sharing
        share_type = self.config['network']['share_type']
        
        if share_type == 'nfs':
            self._setup_nfs_server(vm_config)
        elif share_type == 'samba':
            self._setup_samba_server(vm_config)
        
        # Start MorphStrike server
        server_cmd = f"""
        cd {self.config['deployment']['install_dir']} && \
        nohup python3 server_setup.py \
        --shared-dir {self.config['deployment']['shared_dir']} \
        --port {self.config['deployment']['server_port']} \
        > server.log 2>&1 &
        """
        
        self._run_ssh_command(vm_config, server_cmd)
        
        # Create systemd service
        service_cmd = f"""
        sudo tee /etc/systemd/system/morphstrike-server.service > /dev/null << 'EOF'
[Unit]
Description=MorphStrike Communication Server
After=network.target

[Service]
Type=simple
User=morphstrike
Group=morphstrike
WorkingDirectory={self.config['deployment']['install_dir']}
ExecStart=/usr/bin/python3 {self.config['deployment']['install_dir']}/server_setup.py --shared-dir {self.config['deployment']['shared_dir']} --port {self.config['deployment']['server_port']}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable morphstrike-server
sudo systemctl start morphstrike-server
        """
        
        self._run_ssh_command(vm_config, service_cmd)
    
    def _configure_giver(self, vm_config: Dict):
        """Configure a giver agent VM"""
        self.logger.info("Configuring giver VM...")
        
        # Mount shared directory
        self._mount_shared_directory(vm_config)
        
        # Create giver startup script
        startup_script = f"""#!/bin/bash
cd {self.config['deployment']['install_dir']}
python3 morphstrike_framework.py giver_${{HOSTNAME}} giver {self.config['deployment']['shared_dir']} $1
"""
        
        script_cmd = f"""
        tee {self.config['deployment']['install_dir']}/start_giver.sh > /dev/null << 'EOF'
{startup_script}
EOF
        chmod +x {self.config['deployment']['install_dir']}/start_giver.sh
        """
        
        self._run_ssh_command(vm_config, script_cmd)
    
    def _configure_taker(self, vm_config: Dict):
        """Configure a taker agent VM"""
        self.logger.info("Configuring taker VM...")
        
        # Mount shared directory
        self._mount_shared_directory(vm_config)
        
        # Create taker startup script
        startup_script = f"""#!/bin/bash
cd {self.config['deployment']['install_dir']}
python3 morphstrike_framework.py taker_${{HOSTNAME}} taker {self.config['deployment']['shared_dir']}
"""
        
        script_cmd = f"""
        tee {self.config['deployment']['install_dir']}/start_taker.sh > /dev/null << 'EOF'
{startup_script}
EOF
        chmod +x {self.config['deployment']['install_dir']}/start_taker.sh
        """
        
        self._run_ssh_command(vm_config, script_cmd)
    
    def _setup_nfs_server(self, vm_config: Dict):
        """Setup NFS server for file sharing"""
        nfs_setup = f"""
        sudo apt-get update
        sudo apt-get install -y nfs-kernel-server
        
        sudo mkdir -p {self.config['deployment']['shared_dir']}
        sudo chown nobody:nogroup {self.config['deployment']['shared_dir']}
        sudo chmod 755 {self.config['deployment']['shared_dir']}
        
        echo "{self.config['deployment']['shared_dir']} *(rw,sync,no_subtree_check,all_squash,anonuid=65534,anongid=65534)" | sudo tee -a /etc/exports
        
        sudo exportfs -a
        sudo systemctl restart nfs-kernel-server
        sudo systemctl enable nfs-kernel-server
        """
        
        self._run_ssh_command(vm_config, nfs_setup)
    
    def _setup_samba_server(self, vm_config: Dict):
        """Setup Samba server for file sharing"""
        samba_setup = f"""
        sudo apt-get update
        sudo apt-get install -y samba
        
        sudo mkdir -p {self.config['deployment']['shared_dir']}
        sudo chmod 777 {self.config['deployment']['shared_dir']}
        
        sudo tee -a /etc/samba/smb.conf > /dev/null << 'EOF'

[{self.config['network']['samba_share']}]
path = {self.config['deployment']['shared_dir']}
browseable = yes
read only = no
guest ok = yes
create mask = 0777
directory mask = 0777
force user = nobody
force group = nogroup
EOF

        sudo systemctl restart smbd
        sudo systemctl enable smbd
        """
        
        self._run_ssh_command(vm_config, samba_setup)
    
    def _mount_shared_directory(self, vm_config: Dict):
        """Mount shared directory on client VMs"""
        server_ip = None
        for vm_name, vm_cfg in self.config['vms'].items():
            if vm_cfg['role'] == 'server':
                server_ip = vm_cfg['ip']
                break
        
        if not server_ip:
            self.logger.error("No server VM found in configuration")
            return
        
        share_type = self.config['network']['share_type']
        
        if share_type == 'nfs':
            mount_cmd = f"""
            sudo apt-get update
            sudo apt-get install -y nfs-common
            sudo mkdir -p {self.config['deployment']['shared_dir']}
            
            # Add to fstab for persistent mounting
            if ! grep -q "{server_ip}:{self.config['deployment']['shared_dir']}" /etc/fstab; then
                echo "{server_ip}:{self.config['deployment']['shared_dir']} {self.config['deployment']['shared_dir']} nfs defaults 0 0" | sudo tee -a /etc/fstab
            fi
            
            sudo mount -a
            """
            
        elif share_type == 'samba':
            mount_cmd = f"""
            sudo apt-get update
            sudo apt-get install -y cifs-utils
            sudo mkdir -p {self.config['deployment']['shared_dir']}
            
            # Add to fstab for persistent mounting
            if ! grep -q "//{server_ip}/{self.config['network']['samba_share']}" /etc/fstab; then
                echo "//{server_ip}/{self.config['network']['samba_share']} {self.config['deployment']['shared_dir']} cifs guest,uid=1000,gid=1000,iocharset=utf8 0 0" | sudo tee -a /etc/fstab
            fi
            
            sudo mount -a
            """
        
        self._run_ssh_command(vm_config, mount_cmd)
    
    def start_ctf_session(self, target_networks: List[str]):
        """Start an automated CTF session"""
        self.logger.info("Starting CTF session...")
        
        # Start giver agents with targets
        for vm_name, vm_config in self.config['vms'].items():
            if vm_config['role'] == 'giver':
                for target in target_networks:
                    start_cmd = f"{self.config['deployment']['install_dir']}/start_giver.sh {target}"
                    self._run_ssh_command(vm_config, f"nohup {start_cmd} > giver_{target.replace('/', '_')}.log 2>&1 &")
        
        # Start taker agents
        for vm_name, vm_config in self.config['vms'].items():
            if vm_config['role'] == 'taker':
                start_cmd = f"{self.config['deployment']['install_dir']}/start_taker.sh"
                self._run_ssh_command(vm_config, f"nohup {start_cmd} > taker.log 2>&1 &")
        
        self.logger.info("CTF session started")
    
    def monitor_agents(self):
        """Monitor agent status across all VMs"""
        self.logger.info("Starting agent monitoring...")
        
        while True:
            agent_status = {}
            
            for vm_name, vm_config in self.config['vms'].items():
                try:
                    # Check if agents are running
                    ps_output = self._run_ssh_command(vm_config, "ps aux | grep morphstrike_framework.py | grep -v grep")
                    agent_count = len(ps_output.strip().split('\n')) if ps_output.strip() else 0
                    
                    agent_status[vm_name] = {
                        'ip': vm_config['ip'],
                        'role': vm_config['role'],
                        'agent_count': agent_count,
                        'status': 'online' if agent_count > 0 else 'offline'
                    }
                    
                except Exception as e:
                    agent_status[vm_name] = {
                        'ip': vm_config['ip'],
                        'role': vm_config['role'],
                        'agent_count': 0,
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Print status
            print("\n" + "="*60)
            print("MorphStrike Agent Status")
            print("="*60)
            for vm_name, status in agent_status.items():
                print(f"{vm_name:12} | {status['ip']:15} | {status['role']:8} | {status['status']:8} | Agents: {status['agent_count']}")
            print("="*60)
            
            time.sleep(self.config['deployment']['agent_check_interval'])
    
    def generate_deployment_report(self):
        """Generate a deployment status report"""
        report = {
            'deployment_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'configuration': self.config,
            'vm_status': {}
        }
        
        for vm_name, vm_config in self.config['vms'].items():
            status = {
                'ssh_connectivity': self.check_ssh_connectivity(vm_config),
                'ip': vm_config['ip'],
                'role': vm_config['role']
            }
            
            if status['ssh_connectivity']:
                try:
                    # Check if MorphStrike is installed
                    install_check = self._run_ssh_command(vm_config, f"ls {self.config['deployment']['install_dir']}/morphstrike_framework.py")
                    status['morphstrike_installed'] = True
                except:
                    status['morphstrike_installed'] = False
                
                try:
                    # Check shared directory access
                    shared_check = self._run_ssh_command(vm_config, f"ls {self.config['deployment']['shared_dir']}")
                    status['shared_directory_accessible'] = True
                except:
                    status['shared_directory_accessible'] = False
            
            report['vm_status'][vm_name] = status
        
        report_file = f"morphstrike_deployment_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Deployment report saved: {report_file}")
        return report

def main():
    parser = argparse.ArgumentParser(description="MorphStrike Deployment Manager")
    parser.add_argument("--config", default="deployment_config.yaml", help="Deployment configuration file")
    parser.add_argument("--deploy", action="store_true", help="Deploy to all VMs")
    parser.add_argument("--start-ctf", action="store_true", help="Start CTF session")
    parser.add_argument("--monitor", action="store_true", help="Monitor agent status")
    parser.add_argument("--report", action="store_true", help="Generate deployment report")
    parser.add_argument("--vm", help="Deploy to specific VM only")
    
    args = parser.parse_args()
    
    deployer = MorphStrikeDeployer(args.config)
    
    if args.deploy:
        if args.vm:
            # Deploy to specific VM
            if args.vm in deployer.config['vms']:
                deployer.deploy_to_vm(args.vm, deployer.config['vms'][args.vm])
            else:
                print(f"VM '{args.vm}' not found in configuration")
        else:
            # Deploy to all VMs
            for vm_name, vm_config in deployer.config['vms'].items():
                deployer.deploy_to_vm(vm_name, vm_config)
    
    elif args.start_ctf:
        target_networks = deployer.config['ctf']['target_networks']
        deployer.start_ctf_session(target_networks)
    
    elif args.monitor:
        try:
            deployer.monitor_agents()
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    
    elif args.report:
        deployer.generate_deployment_report()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()