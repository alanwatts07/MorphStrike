#!/usr/bin/env python3
"""
HexStrike MCP Integration for MorphStrike Framework
Integrates HexStrike AI MCP server tools with the agent communication system
"""

import json
import subprocess
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import tempfile
import yaml

@dataclass
class HexStrikeResult:
    tool_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    success: bool

class HexStrikeIntegration:
    """Integration layer for HexStrike MCP server tools"""
    
    def __init__(self, shared_dir: str, agent_id: str):
        self.shared_dir = Path(shared_dir)
        self.agent_id = agent_id
        self.tools_dir = self.shared_dir / "tools"
        self.results_dir = self.shared_dir / "hexstrike_results"
        
        # Create directories
        self.tools_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"HexStrike-{agent_id}")
        
        # Tool categories and their common commands
        self.tool_categories = {
            "reconnaissance": {
                "nmap": ["nmap", "-sS", "-sV", "-O"],
                "masscan": ["masscan", "-p1-65535"],
                "rustscan": ["rustscan", "-a"],
                "nuclei": ["nuclei", "-t", "network/"],
                "subfinder": ["subfinder", "-d"],
                "amass": ["amass", "enum", "-d"]
            },
            "web": {
                "gobuster": ["gobuster", "dir", "-u", "{target}", "-w"],
                "ffuf": ["ffuf", "-u", "{target}/FUZZ", "-w"],
                "nikto": ["nikto", "-h"],
                "whatweb": ["whatweb"],
                "wpscan": ["wpscan", "--url"],
                "sqlmap": ["sqlmap", "-u"],
                "dirb": ["dirb"],
                "feroxbuster": ["feroxbuster", "-u"]
            },
            "exploitation": {
                "metasploit": ["msfconsole", "-x"],
                "searchsploit": ["searchsploit"],
                "exploit-db": ["searchsploit", "--nmap"],
                "nuclei-cves": ["nuclei", "-t", "cves/"],
                "hydra": ["hydra", "-l", "admin", "-P"]
            },
            "post_exploitation": {
                "linpeas": ["./linpeas.sh"],
                "winpeas": ["winPEASx64.exe"],
                "linenum": ["./LinEnum.sh"],
                "pspy": ["./pspy64"],
                "gtfobins": ["echo", "GTFOBins reference"]
            },
            "forensics": {
                "volatility": ["volatility", "-f"],
                "autopsy": ["autopsy"],
                "foremost": ["foremost", "-i"],
                "binwalk": ["binwalk"],
                "strings": ["strings"],
                "file": ["file"],
                "exiftool": ["exiftool"]
            },
            "crypto": {
                "hashcat": ["hashcat", "-m"],
                "john": ["john", "--wordlist="],
                "openssl": ["openssl"],
                "base64": ["base64", "-d"],
                "rot13": ["tr", "A-Za-z", "N-ZA-Mn-za-m"]
            }
        }
    
    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools by category"""
        available = {}
        for category, tools in self.tool_categories.items():
            available[category] = []
            for tool_name in tools.keys():
                if self._check_tool_available(tool_name):
                    available[category].append(tool_name)
        return available
    
    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available on the system"""
        try:
            result = subprocess.run(["which", tool_name], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def execute_tool(self, category: str, tool_name: str, target: str, 
                    additional_args: List[str] = None, wordlist: str = None) -> HexStrikeResult:
        """Execute a specific tool from the HexStrike arsenal"""
        if category not in self.tool_categories:
            raise ValueError(f"Unknown category: {category}")
        
        if tool_name not in self.tool_categories[category]:
            raise ValueError(f"Unknown tool {tool_name} in category {category}")
        
        # Build command
        base_command = self.tool_categories[category][tool_name].copy()
        command = self._build_command(base_command, target, additional_args, wordlist)
        
        self.logger.info(f"Executing: {' '.join(command)}")
        
        # Execute with timeout
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=self.tools_dir
            )
            
            execution_time = time.time() - start_time
            
            hexstrike_result = HexStrikeResult(
                tool_name=tool_name,
                command=' '.join(command),
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                success=result.returncode == 0
            )
            
            # Save result
            self._save_result(hexstrike_result, category, target)
            
            return hexstrike_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return HexStrikeResult(
                tool_name=tool_name,
                command=' '.join(command),
                exit_code=-1,
                stdout="",
                stderr="Command timed out after 5 minutes",
                execution_time=execution_time,
                success=False
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return HexStrikeResult(
                tool_name=tool_name,
                command=' '.join(command),
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                success=False
            )
    
    def _build_command(self, base_command: List[str], target: str, 
                      additional_args: List[str] = None, wordlist: str = None) -> List[str]:
        """Build the complete command with target and arguments"""
        command = []
        
        for part in base_command:
            if "{target}" in part:
                command.append(part.replace("{target}", target))
            else:
                command.append(part)
        
        # Add target if not already included
        if target not in ' '.join(command):
            command.append(target)
        
        # Add wordlist if specified
        if wordlist:
            if any("wordlist" in arg or "-w" in arg for arg in command):
                command.append(wordlist)
            else:
                command.extend(["-w", wordlist])
        
        # Add additional arguments
        if additional_args:
            command.extend(additional_args)
        
        return command
    
    def _save_result(self, result: HexStrikeResult, category: str, target: str):
        """Save tool execution result to shared directory"""
        timestamp = int(time.time())
        filename = f"{self.agent_id}_{category}_{result.tool_name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        result_data = {
            "agent_id": self.agent_id,
            "category": category,
            "target": target,
            "tool_name": result.tool_name,
            "command": result.command,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": result.execution_time,
            "success": result.success,
            "timestamp": timestamp
        }
        
        with open(filepath, 'w') as f:
            json.dump(result_data, f, indent=2)
    
    def run_reconnaissance_suite(self, target: str) -> Dict[str, HexStrikeResult]:
        """Run a comprehensive reconnaissance suite against a target"""
        results = {}
        
        # Port scan
        if self._check_tool_available("nmap"):
            results["nmap_scan"] = self.execute_tool(
                "reconnaissance", "nmap", target, 
                ["-sS", "-sV", "-O", "-A", "--script=vuln"]
            )
        
        # Fast port scan
        if self._check_tool_available("rustscan"):
            results["rustscan"] = self.execute_tool(
                "reconnaissance", "rustscan", target, 
                ["--", "-sV"]
            )
        
        # Vulnerability scan
        if self._check_tool_available("nuclei"):
            results["nuclei_network"] = self.execute_tool(
                "reconnaissance", "nuclei", target,
                ["-t", "network/", "-severity", "high,critical"]
            )
        
        return results
    
    def run_web_analysis_suite(self, target_url: str, wordlist: str = None) -> Dict[str, HexStrikeResult]:
        """Run a comprehensive web analysis suite against a target URL"""
        results = {}
        
        # Default wordlist if none provided
        if not wordlist:
            wordlist = "/usr/share/wordlists/dirb/common.txt"
        
        # Directory enumeration
        if self._check_tool_available("gobuster"):
            results["gobuster"] = self.execute_tool(
                "web", "gobuster", target_url,
                ["dir", "-u", target_url, "-w", wordlist, "-x", "php,html,txt,js"]
            )
        
        # Technology detection
        if self._check_tool_available("whatweb"):
            results["whatweb"] = self.execute_tool(
                "web", "whatweb", target_url,
                ["-v", "-a", "3"]
            )
        
        # Vulnerability scan
        if self._check_tool_available("nikto"):
            results["nikto"] = self.execute_tool(
                "web", "nikto", target_url,
                ["-h", target_url, "-C", "all"]
            )
        
        # Fast fuzzing
        if self._check_tool_available("ffuf"):
            results["ffuf"] = self.execute_tool(
                "web", "ffuf", target_url,
                ["-u", f"{target_url}/FUZZ", "-w", wordlist, "-fc", "404"]
            )
        
        return results
    
    def get_wordlists(self) -> Dict[str, str]:
        """Get available wordlists for various tools"""
        wordlist_paths = {
            "common": "/usr/share/wordlists/dirb/common.txt",
            "big": "/usr/share/wordlists/dirb/big.txt",
            "seclists_dirs": "/usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt",
            "seclists_files": "/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt",
            "rockyou": "/usr/share/wordlists/rockyou.txt"
        }
        
        available_wordlists = {}
        for name, path in wordlist_paths.items():
            if Path(path).exists():
                available_wordlists[name] = path
        
        return available_wordlists
    
    def parse_nmap_results(self, nmap_output: str) -> Dict[str, Any]:
        """Parse Nmap output and extract useful information"""
        results = {
            "open_ports": [],
            "services": {},
            "os_detection": "",
            "vulnerabilities": []
        }
        
        lines = nmap_output.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Extract open ports
            if "/tcp" in line and "open" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split('/')[0]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    results["open_ports"].append(port)
                    results["services"][port] = service
            
            # Extract OS information
            if "OS details:" in line:
                results["os_detection"] = line.replace("OS details:", "").strip()
            
            # Extract vulnerabilities from script results
            if "| " in line and ("CVE-" in line or "VULNERABLE" in line):
                results["vulnerabilities"].append(line.strip())
        
        return results
    
    def create_ctf_toolkit_config(self) -> str:
        """Create a configuration file for CTF-specific tool preferences"""
        config = {
            "ctf_categories": {
                "web": {
                    "primary_tools": ["gobuster", "nikto", "whatweb"],
                    "wordlists": ["common", "seclists_dirs"],
                    "extensions": ["php", "html", "txt", "js", "asp", "aspx"]
                },
                "crypto": {
                    "primary_tools": ["hashcat", "john", "openssl"],
                    "hash_modes": {
                        "md5": 0,
                        "sha1": 100,
                        "sha256": 1400,
                        "bcrypt": 3200
                    }
                },
                "forensics": {
                    "primary_tools": ["binwalk", "strings", "file", "exiftool"],
                    "file_types": ["image", "document", "binary", "memory_dump"]
                },
                "network": {
                    "primary_tools": ["nmap", "rustscan", "nuclei"],
                    "scan_types": ["tcp", "udp", "stealth", "aggressive"]
                }
            },
            "automation_rules": {
                "auto_escalate_on": ["admin_panel", "file_upload", "sql_injection"],
                "follow_up_scans": {
                    "web_found": ["web_analysis_suite"],
                    "ssh_found": ["password_spray", "key_enumeration"],
                    "smb_found": ["enum4linux", "smbclient"]
                }
            }
        }
        
        config_file = self.shared_dir / "ctf_toolkit_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return str(config_file)

class CTFAutomation:
    """Automated CTF challenge solving using HexStrike tools"""
    
    def __init__(self, hexstrike_integration: HexStrikeIntegration):
        self.hexstrike = hexstrike_integration
        self.logger = logging.getLogger(f"CTF-Automation-{hexstrike_integration.agent_id}")
    
    def analyze_challenge_type(self, challenge_description: str, files: List[str] = None) -> str:
        """Analyze challenge type based on description and files"""
        description_lower = challenge_description.lower()
        
        # Web challenges
        if any(keyword in description_lower for keyword in ["website", "web", "http", "url", "server"]):
            return "web"
        
        # Crypto challenges
        elif any(keyword in description_lower for keyword in ["crypto", "cipher", "encrypt", "decode", "hash"]):
            return "crypto"
        
        # Forensics challenges
        elif any(keyword in description_lower for keyword in ["forensics", "image", "memory", "disk", "pcap"]):
            return "forensics"
        
        # Network challenges
        elif any(keyword in description_lower for keyword in ["network", "port", "scan", "service"]):
            return "network"
        
        # Binary exploitation
        elif any(keyword in description_lower for keyword in ["binary", "exploit", "buffer", "overflow", "reverse"]):
            return "binary"
        
        # Default to reconnaissance
        else:
            return "reconnaissance"
    
    def solve_challenge(self, challenge_type: str, target: str, 
                       challenge_description: str = "") -> Dict[str, Any]:
        """Automatically attempt to solve a CTF challenge"""
        solution_results = {
            "challenge_type": challenge_type,
            "target": target,
            "tools_used": [],
            "findings": {},
            "potential_flags": [],
            "next_steps": []
        }
        
        if challenge_type == "web":
            results = self.hexstrike.run_web_analysis_suite(target)
            solution_results["tools_used"].extend(results.keys())
            
            # Look for common flag patterns in web results
            for tool_name, result in results.items():
                if result.success:
                    flags = self._extract_flags(result.stdout)
                    solution_results["potential_flags"].extend(flags)
        
        elif challenge_type == "network" or challenge_type == "reconnaissance":
            results = self.hexstrike.run_reconnaissance_suite(target)
            solution_results["tools_used"].extend(results.keys())
            
            # Parse results for next steps
            if "nmap_scan" in results and results["nmap_scan"].success:
                parsed = self.hexstrike.parse_nmap_results(results["nmap_scan"].stdout)
                solution_results["findings"]["nmap"] = parsed
                
                # Suggest next steps based on findings
                if "80" in parsed["open_ports"] or "443" in parsed["open_ports"]:
                    solution_results["next_steps"].append("web_analysis")
                if "22" in parsed["open_ports"]:
                    solution_results["next_steps"].append("ssh_enumeration")
        
        return solution_results
    
    def _extract_flags(self, text: str) -> List[str]:
        """Extract potential CTF flags from text"""
        import re
        
        # Common CTF flag patterns
        patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[a-zA-Z0-9_]+\{[^}]+\}',
            r'[A-Fa-f0-9]{32}',  # MD5
            r'[A-Fa-f0-9]{64}',  # SHA256
        ]
        
        flags = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            flags.extend(matches)
        
        return list(set(flags))  # Remove duplicates

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python hexstrike_integration.py <shared_dir> <agent_id> [test_target]")
        sys.exit(1)
    
    shared_dir = sys.argv[1]
    agent_id = sys.argv[2]
    
    # Initialize integration
    hexstrike = HexStrikeIntegration(shared_dir, agent_id)
    
    # Show available tools
    available = hexstrike.get_available_tools()
    print("Available HexStrike tools:")
    for category, tools in available.items():
        print(f"  {category}: {', '.join(tools)}")
    
    # Create CTF config
    config_file = hexstrike.create_ctf_toolkit_config()
    print(f"CTF toolkit config created: {config_file}")
    
    # Test with target if provided
    if len(sys.argv) > 3:
        test_target = sys.argv[3]
        print(f"\nTesting reconnaissance on {test_target}...")
        
        automation = CTFAutomation(hexstrike)
        challenge_type = automation.analyze_challenge_type(f"Network challenge: {test_target}")
        results = automation.solve_challenge(challenge_type, test_target)
        
        print(f"Challenge type detected: {challenge_type}")
        print(f"Tools used: {results['tools_used']}")
        print(f"Potential flags: {results['potential_flags']}")
        print(f"Next steps: {results['next_steps']}")