#!/usr/bin/env python3
"""
Quick federated learning simulation with enhanced logging.
"""

import subprocess
import time
import os
import sys
import threading

def monitor_log_file(name, filepath, max_lines=50):
    """Monitor a log file and show the last few lines."""
    try:
        if not os.path.exists(filepath):
            print(f"⏳ Waiting for {name} log file...")
            # Wait for file to be created
            for _ in range(30):  # Wait up to 30 seconds
                if os.path.exists(filepath):
                    break
                time.sleep(1)
            else:
                print(f"❌ {name} log file not created")
                return
        
        print(f"📝 Monitoring {name} log: {filepath}")
        
        # Show last few lines periodically
        last_size = 0
        while True:
            try:
                current_size = os.path.getsize(filepath)
                if current_size > last_size:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        # Show last few lines
                        recent_lines = lines[-5:] if len(lines) > 5 else lines
                        for line in recent_lines:
                            print(f"[{name}] {line.rstrip()}")
                    last_size = current_size
                
                time.sleep(3)  # Check every 3 seconds
            except (FileNotFoundError, PermissionError):
                time.sleep(1)
                continue
            except KeyboardInterrupt:
                break
    except Exception as e:
        print(f"Error monitoring {name}: {e}")

def run_quick_simulation():
    """Run a quick federated learning simulation."""
    print("🚀 Quick Federated Learning Simulation")
    print("=" * 60)
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Clean old logs
    for log_file in ["logs/server.log", "logs/client_1.log", "logs/client_2.log", "logs/client_3.log"]:
        if os.path.exists(log_file):
            os.remove(log_file)
    
    print("🔧 Starting simulation with enhanced logging...")
    print("📝 Log files will be created in logs/ directory")
    print("💡 You can also run: python monitor_logs.py")
    print()
    
    # Start the federated learning process
    try:
        process = subprocess.Popen(
            ["uv", "run", "python", "run_federated_learning.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Start monitoring threads for log files
        monitor_threads = []
        log_files = [
            ("SERVER", "logs/server.log"),
            ("CLIENT1", "logs/client_1.log"),
            ("CLIENT2", "logs/client_2.log"),
            ("CLIENT3", "logs/client_3.log")
        ]
        
        for name, filepath in log_files:
            thread = threading.Thread(target=monitor_log_file, args=(name, filepath))
            thread.daemon = True
            thread.start()
            monitor_threads.append(thread)
        
        print("🔍 Monitoring federated learning process...")
        print("   Press Ctrl+C to stop")
        print("-" * 60)
        
        # Monitor main process output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[MAIN] {output.rstrip()}")
        
        # Wait for process to complete
        return_code = process.wait()
        
        print("-" * 60)
        if return_code == 0:
            print("✅ Simulation completed successfully!")
        else:
            print(f"❌ Simulation failed with return code: {return_code}")
        
        # Show final log summary
        print("\n📋 Final Log Summary:")
        for name, filepath in log_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    print(f"\n{name} ({len(lines)} lines):")
                    # Show last 3 lines
                    for line in lines[-3:]:
                        print(f"   {line.rstrip()}")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping simulation...")
        process.terminate()
        process.wait()
        print("✅ Simulation stopped")
    except Exception as e:
        print(f"❌ Error running simulation: {e}")

def show_help():
    """Show help information."""
    print("🔍 Federated Learning Simulation Tools")
    print("=" * 50)
    print()
    print("Available commands:")
    print("  python run_simulation.py          - Run quick simulation with monitoring")
    print("  python run_federated_learning.py  - Run full simulation")
    print("  python monitor_logs.py            - Monitor logs in real-time")
    print("  python monitor_logs.py summary    - Show log file summary")
    print("  python icp_cli.py status          - Check ICP canister status")
    print()
    print("Log files:")
    print("  logs/server.log     - Server logs")
    print("  logs/client_1.log   - Client 1 logs")
    print("  logs/client_2.log   - Client 2 logs") 
    print("  logs/client_3.log   - Client 3 logs")

def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["help", "-h", "--help"]:
        show_help()
        return
    
    run_quick_simulation()

if __name__ == "__main__":
    main()
