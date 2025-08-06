#!/usr/bin/env python3
"""
Script to run the federated learning system with server and 3 clients.
"""

import subprocess
import time
import os

def main():
    """Main function to start the federated learning process."""
    # Start the server
    print("Starting server...")
    server_process = subprocess.Popen(
        ["uv", "run", "python", "server/server.py", "--rounds", "5"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server a moment to start
    time.sleep(5)
    
    # Check if server started successfully
    if server_process.poll() is not None:
        print("Server failed to start.")
        print("STDOUT:", server_process.stdout.read())
        print("STDERR:", server_process.stderr.read())
        return
    
    print("Server started successfully.")
    
    # Start the clients
    client_processes = []
    client_datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv",
        "dataset/clients/client3_data.csv"
    ]
    
    for i, dataset in enumerate(client_datasets, 1):
        print(f"Starting client {i} with dataset {dataset}...")
        client_process = subprocess.Popen(
            ["uv", "run", "python", "client/client.py", "--dataset", dataset],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        client_processes.append(client_process)
        # Small delay between starting clients
        time.sleep(2)
    
    # Wait for all processes to complete
    try:
        # Wait for server to finish (it will run for the specified number of rounds)
        server_stdout, server_stderr = server_process.communicate()
        print("Server output:")
        print(server_stdout)
        if server_stderr:
            print("Server errors:")
            print(server_stderr)
        
        # Wait for clients to finish
        for i, client_process in enumerate(client_processes):
            client_stdout, client_stderr = client_process.communicate()
            print(f"Client {i+1} output:")
            print(client_stdout)
            if client_stderr:
                print(f"Client {i+1} errors:")
                print(client_stderr)
                
    except KeyboardInterrupt:
        print("\nTerminating processes...")
        server_process.terminate()
        for client_process in client_processes:
            client_process.terminate()
        
        # Wait for processes to terminate
        server_process.wait()
        for client_process in client_processes:
            client_process.wait()
        
        print("All processes terminated.")

if __name__ == "__main__":
    main()