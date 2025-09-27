#!/usr/bin/env python3
"""
Simple test script to verify MorphStrike setup
Run this to test if your agents can communicate
"""

import os
import sys
import time
import json
import subprocess
import signal
from pathlib import Path

class MorphStrikeTest:
    def __init__(self):
        self.test_dir = Path("./test_morphstrike")
        self.processes = []
        
    def cleanup(self):
        """Kill all test processes"""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # Clean up test directory
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)
    
    def setup_test_environment(self):
        """Create test directory structure"""
        print("🔧 Setting up test environment...")
        
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ['messages', 'tasks', 'discoveries', 'plans', 'logs']:
            (self.test_dir / subdir).mkdir(exist_ok=True)
        
        print(f"✅ Test directory created: {self.test_dir}")
    
    def test_basic_communication(self):
        """Test basic agent communication without external tools"""
        print("\n🧪 Testing basic agent communication...")
        
        # Start giver agent
        print("Starting Giver agent...")
        giver_proc = subprocess.Popen([
            sys.executable, "morphstrike_framework.py",
            "test_giver", "giver", str(self.test_dir)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(giver_proc)
        
        # Wait a moment for giver to start
        time.sleep(2)
        
        # Start taker agent
        print("Starting Taker agent...")
        taker_proc = subprocess.Popen([
            sys.executable, "morphstrike_framework.py", 
            "test_taker", "taker", str(self.test_dir)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(taker_proc)
        
        # Wait for communication
        print("Waiting for agents to communicate...")
        time.sleep(5)
        
        # Check if communication occurred
        return self.verify_communication()
    
    def verify_communication(self):
        """Verify that agents are communicating"""
        print("\n📊 Checking communication results...")
        
        results = {
            "messages_created": len(list((self.test_dir / "messages").glob("*.json"))),
            "tasks_created": len(list((self.test_dir / "tasks").glob("*.json"))),
            "logs_created": len(list((self.test_dir / "logs").glob("*.log"))),
        }
        
        print(f"Messages: {results['messages_created']}")
        print(f"Tasks: {results['tasks_created']}")
        print(f"Logs: {results['logs_created']}")
        
        # Check log contents
        log_files = list((self.test_dir / "logs").glob("*.log"))
        if log_files:
            print(f"\nLog content sample from {log_files[0].name}:")
            with open(log_files[0]) as f:
                lines = f.readlines()[-5:]  # Last 5 lines
                for line in lines:
                    print(f"  {line.strip()}")
        
        success = results['messages_created'] > 0 or results['tasks_created'] > 0
        
        if success:
            print("✅ Basic communication test PASSED")
        else:
            print("❌ Basic communication test FAILED")
            
        return success
    
    def test_server_mode(self):
        """Test HTTP server mode"""
        print("\n🌐 Testing HTTP server mode...")
        
        # Start server
        print("Starting HTTP server...")
        server_proc = subprocess.Popen([
            sys.executable, "server_setup.py",
            "--shared-dir", str(self.test_dir),
            "--port", "8081"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(server_proc)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test if server is responding
        try:
            import requests
            response = requests.get("http://localhost:8081/", timeout=5)
            print(f"✅ HTTP server responding: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ HTTP server test failed: {e}")
            return False
    
    def create_manual_task(self):
        """Create a manual task to test task processing"""
        print("\n📝 Creating manual test task...")
        
        task_data = {
            "id": "test_task_001",
            "title": "Test Reconnaissance",
            "description": "Test task for verification",
            "assigned_to": "test_taker",
            "created_by": "test_giver",
            "status": "pending",
            "priority": 1,
            "ctf_category": "reconnaissance",
            "dependencies": [],
            "results": {},
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00"
        }
        
        task_file = self.test_dir / "tasks" / "test_task_001.json"
        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        print(f"✅ Test task created: {task_file}")
        
        # Create corresponding message
        message_data = {
            "id": "test_msg_001",
            "sender_id": "test_giver",
            "recipient_id": "test_taker", 
            "message_type": "task_assignment",
            "content": {
                "task_id": "test_task_001",
                "title": "Test Reconnaissance",
                "description": "Test task for verification"
            },
            "timestamp": "2024-01-01T12:00:00",
            "read": False
        }
        
        msg_file = self.test_dir / "messages" / "test_msg_001.json"
        with open(msg_file, 'w') as f:
            json.dump(message_data, f, indent=2)
        
        print(f"✅ Test message created: {msg_file}")
    
    def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting MorphStrike Test Suite")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            self.create_manual_task()
            
            # Test basic communication
            comm_success = self.test_basic_communication()
            
            # Test server mode
            server_success = self.test_server_mode()
            
            print("\n" + "=" * 50)
            print("📋 TEST RESULTS SUMMARY")
            print("=" * 50)
            print(f"Basic Communication: {'✅ PASS' if comm_success else '❌ FAIL'}")
            print(f"HTTP Server Mode:    {'✅ PASS' if server_success else '❌ FAIL'}")
            
            if comm_success or server_success:
                print("\n🎉 MorphStrike framework is working!")
                print("\nNext steps:")
                print("1. Install on your second VM")
                print("2. Use the shared directory or HTTP server for communication")
                print("3. Start with: python3 morphstrike_framework.py <agent_id> <role> <shared_dir>")
            else:
                print("\n⚠️  Some tests failed. Check the error messages above.")
                print("Make sure all Python dependencies are installed:")
                print("pip3 install requests pyyaml")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
        finally:
            print("\n🧹 Cleaning up...")
            self.cleanup()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nTest interrupted...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run tests
    tester = MorphStrikeTest()
    tester.run_full_test()