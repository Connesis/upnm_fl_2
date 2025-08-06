#!/usr/bin/env python3
"""
Script to run the federated learning system with server and 3 clients.
Each client uses its specific dfx identity (fl_client_1, fl_client_2, fl_client_3).
"""

import subprocess
import time
import os

def start_server_with_identity():
    """Start the server with fl_server identity."""
    print("🖥️ Starting server with fl_server identity...")

    # Set environment variable for server identity
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"

    # Create server log file
    server_log = open("logs/server.log", "w")

    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", "--rounds", "3"],  # Reduced rounds for faster testing
        stdout=server_log,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        text=True,
        env=env
    )

    # Give the server a moment to start
    print("   ⏳ Waiting for server to initialize...")
    time.sleep(3)

    # Check if server started successfully
    if server_process.poll() is not None:
        server_log.close()
        with open("logs/server.log", "r") as f:
            log_content = f.read()
        print("❌ Server failed to start.")
        print("Server log:")
        print(log_content)
        return None

    print("✅ Server started successfully with fl_server identity.")
    print("   📝 Server logs: logs/server.log")
    return server_process, server_log

def start_client_with_identity(client_num, dataset):
    """Start a client with its specific identity."""
    identity_name = f"fl_client_{client_num}"
    print(f"👤 Starting client {client_num} with {identity_name} identity and dataset {dataset}...")

    # Set environment variable for client identity
    env = os.environ.copy()
    env["ICP_CLIENT_IDENTITY_NAME"] = identity_name

    # Create client log file
    client_log = open(f"logs/client_{client_num}.log", "w")

    client_process = subprocess.Popen(
        ["uv", "run", "python", "client/client.py", "--dataset", dataset],
        stdout=client_log,
        stderr=subprocess.STDOUT,  # Combine stderr with stdout
        text=True,
        env=env
    )

    print(f"✅ Client {client_num} started with {identity_name} identity.")
    print(f"   📝 Client {client_num} logs: logs/client_{client_num}.log")
    return client_process, client_log

def main():
    """Main function to start the federated learning process."""
    print("🚀 Starting Federated Learning with Identity Management")
    print("=" * 60)

    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    # Start the server with fl_server identity
    server_result = start_server_with_identity()
    if not server_result:
        print("❌ Failed to start server. Exiting.")
        return

    server_process, server_log = server_result

    # Start the clients with their specific identities
    client_processes = []
    client_logs = []
    client_configs = [
        (1, "dataset/clients/client1_data.csv"),
        (2, "dataset/clients/client2_data.csv"),
        (3, "dataset/clients/client3_data.csv")
    ]

    for client_num, dataset in client_configs:
        client_result = start_client_with_identity(client_num, dataset)
        if client_result:
            client_process, client_log = client_result
            client_processes.append((client_num, client_process))
            client_logs.append(client_log)
        else:
            print(f"❌ Failed to start client {client_num}")
        # Small delay between starting clients
        time.sleep(2)

    print(f"\n📊 Summary: Server + {len(client_processes)} clients started")
    print("=" * 60)
    print("📝 Log files created:")
    print("   • Server: logs/server.log")
    for i in range(len(client_processes)):
        print(f"   • Client {i+1}: logs/client_{i+1}.log")
    print("\n💡 You can monitor progress by running:")
    print("   tail -f logs/server.log")
    print("   tail -f logs/client_*.log")

    # Monitor processes with periodic status updates
    try:
        print("\n⏳ Monitoring federated learning progress...")
        start_time = time.time()

        while True:
            # Check if server is still running
            if server_process.poll() is not None:
                print("\n🏁 Server process completed!")
                break

            # Check client status
            running_clients = 0
            for client_num, client_process in client_processes:
                if client_process.poll() is None:
                    running_clients += 1

            elapsed = int(time.time() - start_time)
            print(f"\r   ⏱️  Elapsed: {elapsed}s | Server: Running | Clients: {running_clients}/{len(client_processes)} running", end="", flush=True)

            time.sleep(5)  # Update every 5 seconds

        # Close log files
        server_log.close()
        for log in client_logs:
            log.close()

        # Wait for clients to finish
        print("\n👥 Waiting for remaining clients to complete...")
        for client_num, client_process in client_processes:
            if client_process.poll() is None:
                client_process.wait()

        print("\n🎉 Federated learning completed successfully!")
        print("\n📋 Final log summary:")

        # Show last few lines of each log
        for log_file in ["logs/server.log"] + [f"logs/client_{i+1}.log" for i in range(len(client_processes))]:
            if os.path.exists(log_file):
                print(f"\n📄 {log_file} (last 5 lines):")
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        print(f"   {line.rstrip()}")

    except KeyboardInterrupt:
        print("\n🛑 Terminating processes...")
        server_process.terminate()
        for client_num, client_process in client_processes:
            print(f"   Terminating client {client_num} (fl_client_{client_num})")
            client_process.terminate()

        # Close log files
        server_log.close()
        for log in client_logs:
            log.close()

        # Wait for processes to terminate
        server_process.wait()
        for client_num, client_process in client_processes:
            client_process.wait()

        print("✅ All processes terminated.")

    print("=" * 60)

if __name__ == "__main__":
    main()