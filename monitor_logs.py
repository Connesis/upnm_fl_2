#!/usr/bin/env python3
"""
Real-time log monitoring script for federated learning.
Shows logs from server and all clients in a unified view.
"""

import os
import time
import threading
import sys
from datetime import datetime

class LogMonitor:
    def __init__(self):
        self.running = True
        self.log_files = []
        
    def find_log_files(self):
        """Find all available log files."""
        log_files = []
        
        # Server log
        if os.path.exists("logs/server.log"):
            log_files.append(("SERVER", "logs/server.log"))
        
        # Client logs
        for i in range(1, 10):  # Check for up to 10 clients
            client_log = f"logs/client_{i}.log"
            if os.path.exists(client_log):
                log_files.append((f"CLIENT_{i}", client_log))
        
        return log_files
    
    def tail_file(self, name, filepath):
        """Tail a log file and print new lines with prefix."""
        try:
            with open(filepath, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if line:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] {name:8} | {line.rstrip()}")
                    else:
                        time.sleep(0.1)
        except FileNotFoundError:
            print(f"[ERROR] Log file not found: {filepath}")
        except Exception as e:
            print(f"[ERROR] Error reading {filepath}: {e}")
    
    def monitor(self):
        """Start monitoring all log files."""
        print("🔍 Federated Learning Log Monitor")
        print("=" * 80)
        
        # Find log files
        log_files = self.find_log_files()
        
        if not log_files:
            print("❌ No log files found in logs/ directory")
            print("   Make sure to run the federated learning simulation first")
            return
        
        print(f"📝 Monitoring {len(log_files)} log files:")
        for name, filepath in log_files:
            print(f"   • {name}: {filepath}")
        
        print("\n🚀 Starting real-time monitoring (Press Ctrl+C to stop)...")
        print("=" * 80)
        
        # Start a thread for each log file
        threads = []
        for name, filepath in log_files:
            thread = threading.Thread(target=self.tail_file, args=(name, filepath))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping log monitor...")
            self.running = False
            
            # Wait a bit for threads to finish
            time.sleep(0.5)
            print("✅ Log monitor stopped")

def show_log_summary():
    """Show a summary of existing log files."""
    print("📋 Log File Summary")
    print("=" * 50)
    
    log_files = []
    
    # Check for server log
    if os.path.exists("logs/server.log"):
        log_files.append(("Server", "logs/server.log"))
    
    # Check for client logs
    for i in range(1, 10):
        client_log = f"logs/client_{i}.log"
        if os.path.exists(client_log):
            log_files.append((f"Client {i}", client_log))
    
    if not log_files:
        print("❌ No log files found")
        return
    
    for name, filepath in log_files:
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
                print(f"\n📄 {name} ({filepath}):")
                print(f"   Lines: {len(lines)}")
                if lines:
                    print(f"   Last line: {lines[-1].rstrip()}")
                else:
                    print("   (Empty)")
        except Exception as e:
            print(f"   Error reading file: {e}")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_log_summary()
        return
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    monitor = LogMonitor()
    monitor.monitor()

if __name__ == "__main__":
    main()
