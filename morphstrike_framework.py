#!/usr/bin/env python3
"""
MorphStrike: Multi-Agent Communication Framework for CTF Collaboration
A framework for Claude Code controlled agents to communicate over shared files
"""

import json
import os
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading
import logging

class AgentRole(Enum):
    GIVER = "giver"
    TAKER = "taker"
    COORDINATOR = "coordinator"

class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_UPDATE = "task_update"
    TASK_COMPLETION = "task_completion"
    DISCOVERY = "discovery"
    PLAN_UPDATE = "plan_update"
    COORDINATION = "coordination"
    HEXSTRIKE_RESULT = "hexstrike_result"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class Message:
    id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    read: bool = False

@dataclass
class Task:
    id: str
    title: str
    description: str
    assigned_to: str
    created_by: str
    status: TaskStatus
    priority: int
    ctf_category: str
    dependencies: List[str]
    results: Dict[str, Any]
    created_at: str
    updated_at: str

@dataclass
class Discovery:
    id: str
    agent_id: str
    category: str
    description: str
    data: Dict[str, Any]
    confidence: float
    timestamp: str

class MorphStrikeAgent:
    def __init__(self, agent_id: str, role: AgentRole, shared_dir: str):
        self.agent_id = agent_id
        self.role = role
        self.shared_dir = Path(shared_dir)
        self.message_dir = self.shared_dir / "messages"
        self.task_dir = self.shared_dir / "tasks"
        self.discovery_dir = self.shared_dir / "discoveries"
        self.plan_dir = self.shared_dir / "plans"
        
        self._setup_directories()
        self.logger = self._setup_logging()
        
    def _setup_directories(self):
        """Create necessary directories for communication"""
        for dir_path in [self.message_dir, self.task_dir, self.discovery_dir, self.plan_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup logging for the agent"""
        log_file = self.shared_dir / f"agent_{self.agent_id}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(f"MorphStrike-{self.agent_id}")
    
    def send_message(self, recipient_id: str, message_type: MessageType, content: Dict[str, Any]):
        """Send a message to another agent"""
        message = Message(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            read=False
        )
        
        message_file = self.message_dir / f"{message.id}.json"
        with open(message_file, 'w') as f:
            json.dump(asdict(message), f, indent=2)
        
        self.logger.info(f"Sent {message_type.value} message to {recipient_id}")
        return message.id
    
    def get_messages(self, unread_only: bool = True) -> List[Message]:
        """Retrieve messages for this agent"""
        messages = []
        for message_file in self.message_dir.glob("*.json"):
            try:
                with open(message_file, 'r') as f:
                    data = json.load(f)
                
                if data['recipient_id'] == self.agent_id:
                    if not unread_only or not data['read']:
                        message = Message(**data)
                        messages.append(message)
            except Exception as e:
                self.logger.error(f"Error reading message {message_file}: {e}")
        
        return sorted(messages, key=lambda m: m.timestamp)
    
    def mark_message_read(self, message_id: str):
        """Mark a message as read"""
        message_file = self.message_dir / f"{message_id}.json"
        if message_file.exists():
            with open(message_file, 'r') as f:
                data = json.load(f)
            data['read'] = True
            with open(message_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def create_task(self, title: str, description: str, assigned_to: str, 
                   ctf_category: str = "", priority: int = 1, dependencies: List[str] = None):
        """Create a new task"""
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            assigned_to=assigned_to,
            created_by=self.agent_id,
            status=TaskStatus.PENDING,
            priority=priority,
            ctf_category=ctf_category,
            dependencies=dependencies or [],
            results={},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        task_file = self.task_dir / f"{task.id}.json"
        with open(task_file, 'w') as f:
            json.dump(asdict(task), f, indent=2)
        
        # Send task assignment message
        self.send_message(
            assigned_to,
            MessageType.TASK_ASSIGNMENT,
            {"task_id": task.id, "title": title, "description": description}
        )
        
        self.logger.info(f"Created task {task.id}: {title}")
        return task.id
    
    def update_task(self, task_id: str, status: TaskStatus = None, results: Dict[str, Any] = None):
        """Update an existing task"""
        task_file = self.task_dir / f"{task_id}.json"
        if not task_file.exists():
            self.logger.error(f"Task {task_id} not found")
            return False
        
        with open(task_file, 'r') as f:
            data = json.load(f)
        
        if status:
            data['status'] = status.value
        if results:
            data['results'].update(results)
        data['updated_at'] = datetime.now().isoformat()
        
        with open(task_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Send update message to task creator
        self.send_message(
            data['created_by'],
            MessageType.TASK_UPDATE,
            {"task_id": task_id, "status": status.value if status else data['status'], "results": results}
        )
        
        self.logger.info(f"Updated task {task_id}")
        return True
    
    def get_tasks(self, assigned_to_me: bool = True, status_filter: TaskStatus = None) -> List[Task]:
        """Get tasks for this agent"""
        tasks = []
        for task_file in self.task_dir.glob("*.json"):
            try:
                with open(task_file, 'r') as f:
                    data = json.load(f)
                
                include_task = True
                if assigned_to_me and data['assigned_to'] != self.agent_id:
                    include_task = False
                if status_filter and data['status'] != status_filter.value:
                    include_task = False
                
                if include_task:
                    task = Task(**data)
                    tasks.append(task)
            except Exception as e:
                self.logger.error(f"Error reading task {task_file}: {e}")
        
        return sorted(tasks, key=lambda t: t.priority, reverse=True)
    
    def add_discovery(self, category: str, description: str, data: Dict[str, Any], confidence: float = 0.8):
        """Add a discovery to the shared knowledge base"""
        discovery = Discovery(
            id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            category=category,
            description=description,
            data=data,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
        
        discovery_file = self.discovery_dir / f"{discovery.id}.json"
        with open(discovery_file, 'w') as f:
            json.dump(asdict(discovery), f, indent=2)
        
        self.logger.info(f"Added discovery: {description}")
        return discovery.id
    
    def get_discoveries(self, category: str = None) -> List[Discovery]:
        """Get discoveries from the knowledge base"""
        discoveries = []
        for discovery_file in self.discovery_dir.glob("*.json"):
            try:
                with open(discovery_file, 'r') as f:
                    data = json.load(f)
                
                if not category or data['category'] == category:
                    discovery = Discovery(**data)
                    discoveries.append(discovery)
            except Exception as e:
                self.logger.error(f"Error reading discovery {discovery_file}: {e}")
        
        return sorted(discoveries, key=lambda d: d.timestamp, reverse=True)
    
    def update_plan(self, plan_name: str, plan_data: Dict[str, Any]):
        """Update a shared plan"""
        plan_file = self.plan_dir / f"{plan_name}.json"
        plan_data['updated_by'] = self.agent_id
        plan_data['updated_at'] = datetime.now().isoformat()
        
        with open(plan_file, 'w') as f:
            json.dump(plan_data, f, indent=2)
        
        self.logger.info(f"Updated plan: {plan_name}")
    
    def get_plan(self, plan_name: str) -> Optional[Dict[str, Any]]:
        """Get a shared plan"""
        plan_file = self.plan_dir / f"{plan_name}.json"
        if plan_file.exists():
            with open(plan_file, 'r') as f:
                return json.load(f)
        return None
    
    def start_message_listener(self):
        """Start a background thread to listen for new messages"""
        def listen():
            while True:
                messages = self.get_messages(unread_only=True)
                for message in messages:
                    self.handle_message(message)
                    self.mark_message_read(message.id)
                time.sleep(5)  # Check every 5 seconds
        
        listener_thread = threading.Thread(target=listen, daemon=True)
        listener_thread.start()
        self.logger.info("Message listener started")
    
    def handle_message(self, message: Message):
        """Handle incoming messages - override in subclass"""
        self.logger.info(f"Received {message.message_type.value} from {message.sender_id}")
        
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            self.logger.info(f"New task assigned: {message.content.get('title')}")
        elif message.message_type == MessageType.DISCOVERY:
            self.logger.info(f"New discovery shared: {message.content.get('description')}")
        # Add more message type handlers as needed

class CTFGiverAgent(MorphStrikeAgent):
    """Specialized agent for giving tasks and coordinating CTF activities"""
    
    def __init__(self, agent_id: str, shared_dir: str):
        super().__init__(agent_id, AgentRole.GIVER, shared_dir)
    
    def analyze_ctf_box(self, target_ip: str, box_name: str = "target"):
        """Analyze a CTF box and create tasks for taker agents"""
        # Create initial reconnaissance tasks
        recon_task_id = self.create_task(
            f"Initial Reconnaissance - {box_name}",
            f"Perform initial reconnaissance on {target_ip}. Include port scanning, service enumeration, and OS detection.",
            "taker",  # Will be assigned to any taker agent
            "reconnaissance",
            priority=5
        )
        
        # Create web analysis task if HTTP services are found
        web_task_id = self.create_task(
            f"Web Application Analysis - {box_name}",
            f"Analyze web applications on {target_ip}. Include directory enumeration, vulnerability scanning, and technology detection.",
            "taker",
            "web",
            priority=4,
            dependencies=[recon_task_id]
        )
        
        # Update master plan
        self.update_plan(f"ctf_plan_{box_name}", {
            "target": target_ip,
            "box_name": box_name,
            "status": "started",
            "tasks": [recon_task_id, web_task_id],
            "objectives": ["initial_access", "privilege_escalation", "flag_capture"]
        })
        
        self.logger.info(f"Created CTF analysis plan for {box_name} ({target_ip})")

class CTFTakerAgent(MorphStrikeAgent):
    """Specialized agent for taking and executing CTF tasks"""
    
    def __init__(self, agent_id: str, shared_dir: str):
        super().__init__(agent_id, AgentRole.TAKER, shared_dir)
        self.hexstrike_available = False
        self._check_hexstrike()
    
    def _check_hexstrike(self):
        """Check if hexstrike MCP server is available"""
        # This would be implemented to check for hexstrike tools
        self.hexstrike_available = True  # Placeholder
    
    def handle_message(self, message: Message):
        """Override message handling for taker-specific logic"""
        super().handle_message(message)
        
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            task_id = message.content.get('task_id')
            self.execute_task(task_id)
    
    def execute_task(self, task_id: str):
        """Execute a CTF task using available tools"""
        task_file = self.task_dir / f"{task_id}.json"
        if not task_file.exists():
            self.logger.error(f"Task {task_id} not found")
            return
        
        with open(task_file, 'r') as f:
            task_data = json.load(f)
        
        self.update_task(task_id, TaskStatus.IN_PROGRESS)
        
        # Execute based on CTF category
        category = task_data.get('ctf_category', '')
        if category == 'reconnaissance':
            self._execute_recon_task(task_id, task_data)
        elif category == 'web':
            self._execute_web_task(task_id, task_data)
        # Add more categories as needed
        
    def _execute_recon_task(self, task_id: str, task_data: Dict[str, Any]):
        """Execute reconnaissance task"""
        self.logger.info(f"Executing recon task {task_id}")
        
        # Placeholder for actual reconnaissance using hexstrike tools
        results = {
            "status": "completed",
            "findings": {
                "ports": ["22", "80", "443"],
                "services": ["ssh", "http", "https"],
                "os": "Linux"
            },
            "tools_used": ["nmap", "service_detection"],
            "execution_time": "5 minutes"
        }
        
        self.update_task(task_id, TaskStatus.COMPLETED, results)
        
        # Add discovery
        self.add_discovery(
            "reconnaissance",
            f"Port scan results for {task_data.get('description', 'target')}",
            results["findings"],
            0.9
        )
    
    def _execute_web_task(self, task_id: str, task_data: Dict[str, Any]):
        """Execute web analysis task"""
        self.logger.info(f"Executing web task {task_id}")
        
        # Placeholder for actual web analysis using hexstrike tools
        results = {
            "status": "completed",
            "findings": {
                "directories": ["/admin", "/backup", "/uploads"],
                "vulnerabilities": ["directory_traversal", "file_upload"],
                "technologies": ["PHP", "Apache", "MySQL"]
            },
            "tools_used": ["gobuster", "nikto", "whatweb"],
            "execution_time": "10 minutes"
        }
        
        self.update_task(task_id, TaskStatus.COMPLETED, results)
        
        # Add discovery
        self.add_discovery(
            "web",
            f"Web analysis results for {task_data.get('description', 'target')}",
            results["findings"],
            0.85
        )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python morphstrike_framework.py <agent_id> <role> <shared_dir> [target_ip]")
        print("Roles: giver, taker")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    role = sys.argv[2]
    shared_dir = sys.argv[3]
    
    if role == "giver":
        agent = CTFGiverAgent(agent_id, shared_dir)
        agent.start_message_listener()
        
        if len(sys.argv) > 4:
            target_ip = sys.argv[4]
            agent.analyze_ctf_box(target_ip)
        
        print(f"Giver agent {agent_id} started. Shared directory: {shared_dir}")
        
    elif role == "taker":
        agent = CTFTakerAgent(agent_id, shared_dir)
        agent.start_message_listener()
        
        print(f"Taker agent {agent_id} started. Shared directory: {shared_dir}")
        
        # Keep the agent running
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print(f"\nAgent {agent_id} shutting down...")
    
    else:
        print(f"Unknown role: {role}")
        sys.exit(1)