#!/usr/bin/env python3
"""
Command-line interface for managing the ICP FL_CVD_Backend canister.
"""
import argparse
import sys
import os
import subprocess
import time
import signal
import threading
from typing import Optional, List, Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from icp_client import ICPClient, SystemStats
from icp_auth_client import AuthenticatedICPClient, get_admin_client, get_server_client


def print_banner():
    """Print the CLI banner."""
    print("\n" + "="*80)
    print("🔗 ICP FEDERATED LEARNING MANAGEMENT CLI")
    print("="*80)


def print_system_stats(stats: Optional[SystemStats]):
    """Print system statistics in a formatted way."""
    if stats:
        print("\n📊 System Statistics:")
        print(f"   • Total clients: {stats.total_clients}")
        print(f"   • Active clients: {stats.active_clients}")
        print(f"   • Total training rounds: {stats.total_rounds}")
        print(f"   • Completed rounds: {stats.completed_rounds}")
        print(f"   • Total samples processed: {stats.total_samples_processed:,}")
    else:
        print("❌ Failed to retrieve system statistics")


def cmd_status(args):
    """Show system status and statistics."""
    print_banner()
    
    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        print("   Make sure the local devnet is running and canister is deployed")
        return 1
    
    print(f"🔗 Connected to canister: {client.canister_id}")
    
    stats = client.get_system_stats()
    print_system_stats(stats)
    
    print("\n" + "="*80)
    return 0


def cmd_register(args):
    """Register a new client."""
    print_banner()
    
    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        return 1
    
    print("🔄 Registering client with ICP blockchain...")
    success = client.register_client()
    
    if success:
        print("✅ Client registered successfully!")
    else:
        print("ℹ️  Client already registered or registration failed")
    
    # Show updated stats
    stats = client.get_system_stats()
    print_system_stats(stats)
    
    print("\n" + "="*80)
    return 0


def cmd_clients(args):
    """List all clients."""
    print_banner()
    
    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        return 1
    
    print("👥 Retrieving client list...")
    
    # Get active clients
    active_clients = client.get_active_clients()
    
    if active_clients:
        print(f"\n📋 Active Clients ({len(active_clients)}):")
        for i, client_info in enumerate(active_clients, 1):
            print(f"   {i}. {client_info.id}")
            print(f"      Status: {client_info.status}")
            print(f"      Rounds participated: {client_info.total_rounds_participated}")
            print(f"      Samples contributed: {client_info.total_samples_contributed:,}")
    else:
        print("📋 No active clients found")
    
    print("\n" + "="*80)
    return 0


def cmd_rounds(args):
    """Show training round history."""
    print_banner()
    
    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        return 1
    
    print("🔄 Retrieving training round history...")
    
    # For now, just show system stats
    # TODO: Implement proper round history retrieval
    stats = client.get_system_stats()
    print_system_stats(stats)
    
    print("\nℹ️  Detailed round history feature coming soon...")
    print("   Use the Candid interface for detailed round information:")
    print(f"   http://127.0.0.1:4943/?canisterId=uzt4z-lp777-77774-qaabq-cai&id={client.canister_id}")
    
    print("\n" + "="*80)
    return 0


def cmd_check(args):
    """Check if a specific client is registered."""
    print_banner()
    
    if not args.client_id:
        print("❌ Error: Client ID is required")
        return 1
    
    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        return 1
    
    print(f"🔍 Checking client: {args.client_id}")
    
    is_registered = client.is_client_registered(args.client_id)
    is_active = client.is_client_active(args.client_id)
    
    print(f"   Registered: {'✅ Yes' if is_registered else '❌ No'}")
    print(f"   Active: {'✅ Yes' if is_active else '❌ No'}")
    
    print("\n" + "="*80)
    return 0


def cmd_candid(args):
    """Open the Candid interface in browser."""
    print_banner()

    client = ICPClient()
    if not client.canister_id:
        print("❌ Error: Could not connect to ICP canister")
        return 1

    candid_url = f"http://127.0.0.1:4943/?canisterId=uzt4z-lp777-77774-qaabq-cai&id={client.canister_id}"

    print("🌐 Candid Interface URL:")
    print(f"   {candid_url}")
    print("\n💡 Copy this URL to your browser to interact with the canister directly")

    # Try to open in browser (optional)
    try:
        import webbrowser
        if args.open:
            webbrowser.open(candid_url)
            print("🚀 Opening in default browser...")
    except ImportError:
        pass

    print("\n" + "="*80)
    return 0


def cmd_init_admin(args):
    """Initialize admin role (run once after deployment)."""
    print_banner()

    print("🔧 Initializing admin role...")

    try:
        admin_client = get_admin_client()
        if not admin_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            return 1

        success = admin_client.init_admin()
        if success:
            print("✅ Admin role initialized successfully!")
            current_principal = admin_client.get_current_principal()
            if current_principal:
                print(f"   Admin Principal: {current_principal}")
        else:
            print("❌ Failed to initialize admin role")
            print("   This may have already been done, or you're not the deployer")

    except Exception as e:
        print(f"❌ Error initializing admin: {e}")
        return 1

    print("\n" + "="*80)
    return 0


def cmd_pending_clients(args):
    """List clients pending approval."""
    print_banner()

    try:
        admin_client = get_admin_client()
        if not admin_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            return 1

        print("📋 Retrieving pending clients...")
        pending_clients = admin_client.get_pending_clients()

        if pending_clients:
            print(f"\n⏳ Pending Clients ({len(pending_clients)}):")
            for i, client in enumerate(pending_clients, 1):
                print(f"   {i}. {client.id}")
                print(f"      Registered: {client.registered_at}")
                print(f"      Status: Pending Approval")
        else:
            print("📋 No clients pending approval")

    except Exception as e:
        print(f"❌ Error retrieving pending clients: {e}")
        return 1

    print("\n" + "="*80)
    return 0


def cmd_approve_client(args):
    """Approve a pending client."""
    print_banner()

    if not args.client_id:
        print("❌ Error: Client ID is required")
        return 1

    try:
        admin_client = get_admin_client()
        if not admin_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            return 1

        print(f"✅ Approving client: {args.client_id}")
        success = admin_client.admin_approve_client(args.client_id)

        if success:
            print("✅ Client approved successfully!")
            print("   Client can now participate in federated learning")
        else:
            print("❌ Failed to approve client")
            print("   Client may not exist or not be in pending status")

    except Exception as e:
        print(f"❌ Error approving client: {e}")
        return 1

    print("\n" + "="*80)
    return 0


def cmd_reject_client(args):
    """Reject a pending client."""
    print_banner()

    if not args.client_id:
        print("❌ Error: Client ID is required")
        return 1

    try:
        admin_client = get_admin_client()
        if not admin_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            return 1

        print(f"❌ Rejecting client: {args.client_id}")
        success = admin_client.admin_reject_client(args.client_id)

        if success:
            print("✅ Client rejected successfully!")
        else:
            print("❌ Failed to reject client")
            print("   Client may not exist or not be in pending status")

    except Exception as e:
        print(f"❌ Error rejecting client: {e}")
        return 1

    print("\n" + "="*80)
    return 0


def cmd_setup_server(args):
    """Set up server role."""
    print_banner()

    if not args.server_principal:
        print("❌ Error: Server principal ID is required")
        return 1

    try:
        admin_client = get_admin_client()
        if not admin_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            return 1

        print(f"🔧 Setting up server role for: {args.server_principal}")
        success = admin_client.admin_set_server(args.server_principal)

        if success:
            print("✅ Server role configured successfully!")
            print("   Server can now manage training rounds")
        else:
            print("❌ Failed to set up server role")

    except Exception as e:
        print(f"❌ Error setting up server: {e}")
        return 1

    print("\n" + "="*80)
    return 0


class FederatedLearningOrchestrator:
    """Orchestrates the complete federated learning process."""

    def __init__(self):
        self.server_process = None
        self.client_processes = []
        self.icp_client = ICPClient()
        self.shutdown_requested = False

    def start_server(self, rounds: int, port: int = 8080) -> bool:
        """Start the federated learning server with fl_server identity."""
        try:
            print(f"🚀 Starting Flower server with fl_server identity (rounds: {rounds}, port: {port})...")

            # Set environment variable for server identity
            env = os.environ.copy()
            env["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"

            cmd = [
                "uv", "run", "python", "server/server.py",
                "--rounds", str(rounds)
            ]

            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            # Wait a moment for server to start
            time.sleep(3)

            # Check if server started successfully
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Server failed to start:")
                print(f"   STDOUT: {stdout}")
                print(f"   STDERR: {stderr}")
                return False

            print("✅ Server started successfully with fl_server identity")
            return True

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def wait_for_clients(self, expected_clients: int, timeout: int = 60) -> bool:
        """Wait for the expected number of clients to connect."""
        print(f"⏳ Waiting for {expected_clients} clients to connect (timeout: {timeout}s)...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.shutdown_requested:
                return False

            try:
                stats = self.icp_client.get_system_stats()
                if stats and stats.active_clients >= expected_clients:
                    print(f"✅ {stats.active_clients} clients connected!")
                    return True

                # Show progress
                current_clients = stats.active_clients if stats else 0
                print(f"   📊 Current clients: {current_clients}/{expected_clients}")
                time.sleep(2)

            except Exception as e:
                print(f"   ⚠️  Error checking client status: {e}")
                time.sleep(2)

        print(f"⏰ Timeout waiting for clients")
        return False

    def start_clients(self, client_datasets: List[str], delay: float = 1.0) -> bool:
        """Start federated learning clients with proper identity management."""
        print(f"👥 Starting {len(client_datasets)} clients with identity management...")

        for i, dataset in enumerate(client_datasets, 1):
            if self.shutdown_requested:
                return False

            try:
                identity_name = f"fl_client_{i}"
                print(f"   🔄 Starting client {i} with identity {identity_name} and dataset: {dataset}")

                # Set environment variable for client identity
                env = os.environ.copy()
                env["ICP_CLIENT_IDENTITY_NAME"] = identity_name

                cmd = [
                    "uv", "run", "python", "client/client.py",
                    "--dataset", dataset
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                self.client_processes.append(process)
                print(f"   ✅ Client {i} started with identity: {identity_name}")

                # Small delay between starting clients
                if delay > 0:
                    time.sleep(delay)

            except Exception as e:
                print(f"   ❌ Failed to start client {i}: {e}")
                return False

        print(f"✅ All {len(client_datasets)} clients started with their respective identities")
        return True

    def monitor_training(self) -> bool:
        """Monitor the training process."""
        print("📊 Monitoring federated learning progress...")

        initial_stats = self.icp_client.get_system_stats()
        initial_rounds = initial_stats.completed_rounds if initial_stats else 0

        while not self.shutdown_requested:
            try:
                # Check if server is still running
                if self.server_process and self.server_process.poll() is not None:
                    print("🏁 Server process completed")
                    break

                # Get current stats
                stats = self.icp_client.get_system_stats()
                if stats:
                    current_rounds = stats.completed_rounds
                    if current_rounds > initial_rounds:
                        print(f"   ✅ Round {current_rounds} completed!")
                        print(f"   📈 Total samples processed: {stats.total_samples_processed:,}")

                time.sleep(5)

            except Exception as e:
                print(f"   ⚠️  Error monitoring training: {e}")
                time.sleep(5)

        return True

    def cleanup(self):
        """Clean up all processes."""
        print("\n🧹 Cleaning up processes...")

        # Terminate server
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                print("   ✅ Server terminated")
            except Exception as e:
                print(f"   ⚠️  Error terminating server: {e}")
                try:
                    self.server_process.kill()
                except:
                    pass

        # Terminate clients
        for i, process in enumerate(self.client_processes, 1):
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ Client {i} terminated")
            except Exception as e:
                print(f"   ⚠️  Error terminating client {i}: {e}")
                try:
                    process.kill()
                except:
                    pass

        print("✅ Cleanup completed")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.shutdown_requested = True


def cmd_train(args):
    """Orchestrate a complete federated learning training session."""
    print_banner()

    # Validate arguments
    if not args.datasets:
        print("❌ Error: At least one dataset must be specified")
        return 1

    # Check if datasets exist
    missing_datasets = []
    for dataset in args.datasets:
        if not os.path.exists(dataset):
            missing_datasets.append(dataset)

    if missing_datasets:
        print("❌ Error: The following datasets do not exist:")
        for dataset in missing_datasets:
            print(f"   • {dataset}")
        return 1

    # Initialize orchestrator
    orchestrator = FederatedLearningOrchestrator()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, orchestrator.signal_handler)
    signal.signal(signal.SIGTERM, orchestrator.signal_handler)

    try:
        print(f"🎯 Starting federated learning session:")
        print(f"   • Rounds: {args.rounds}")
        print(f"   • Clients: {len(args.datasets)}")
        print(f"   • Datasets: {', '.join(args.datasets)}")
        print(f"   • Wait timeout: {args.wait_timeout}s")

        # Check ICP connection
        if not orchestrator.icp_client.canister_id:
            print("❌ Error: Could not connect to ICP canister")
            print("   Make sure the local devnet is running and canister is deployed")
            return 1

        print(f"🔗 Connected to ICP canister: {orchestrator.icp_client.canister_id}")

        # Step 1: Start the server
        if not orchestrator.start_server(args.rounds):
            return 1

        # Step 2: Start clients if auto-start is enabled
        if args.auto_start_clients:
            if not orchestrator.start_clients(args.datasets, args.client_delay):
                orchestrator.cleanup()
                return 1
        else:
            print("\n📋 Manual client startup mode:")
            print("   Start your clients manually using:")
            for i, dataset in enumerate(args.datasets, 1):
                print(f"   {i}. uv run python client/client.py --dataset {dataset}")

        # Step 3: Wait for clients to connect
        if not orchestrator.wait_for_clients(len(args.datasets), args.wait_timeout):
            print("❌ Training aborted: Not enough clients connected")
            orchestrator.cleanup()
            return 1

        print("\n🚀 All clients connected! Training will begin automatically...")

        # Step 4: Monitor training progress
        orchestrator.monitor_training()

        # Step 5: Show final results
        print("\n📊 Training completed! Final statistics:")
        final_stats = orchestrator.icp_client.get_system_stats()
        print_system_stats(final_stats)

        print("\n🎉 Federated learning session completed successfully!")

    except KeyboardInterrupt:
        print("\n🛑 Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        return 1
    finally:
        orchestrator.cleanup()

    print("\n" + "="*80)
    return 0


def cmd_quick_train(args):
    """Quick training with default client datasets."""
    print_banner()

    # Default client datasets
    default_datasets = [
        "dataset/clients/client1_data.csv",
        "dataset/clients/client2_data.csv",
        "dataset/clients/client3_data.csv"
    ]

    # Check which datasets exist
    available_datasets = [d for d in default_datasets if os.path.exists(d)]

    if not available_datasets:
        print("❌ Error: No default client datasets found")
        print("   Expected datasets:")
        for dataset in default_datasets:
            print(f"   • {dataset}")
        return 1

    print(f"🚀 Quick training mode with {len(available_datasets)} clients")

    # Set up args for training
    class QuickArgs:
        def __init__(self):
            self.datasets = available_datasets
            self.rounds = args.rounds
            self.auto_start_clients = True
            self.wait_timeout = 60
            self.client_delay = 2.0

    quick_args = QuickArgs()
    return cmd_train(quick_args)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ICP Federated Learning Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                                    # Show system status
  %(prog)s register                                  # Register current client
  %(prog)s clients                                   # List all clients
  %(prog)s rounds                                    # Show training history
  %(prog)s check <client-id>                         # Check client status
  %(prog)s candid                                    # Get Candid interface URL

  # Admin commands (require admin role):
  %(prog)s init-admin                                # Initialize admin role (run once)
  %(prog)s pending                                   # List clients pending approval
  %(prog)s approve <client-principal-id>             # Approve a pending client
  %(prog)s reject <client-principal-id>              # Reject a pending client
  %(prog)s setup-server <server-principal-id>       # Set up server role

  # Training orchestration:
  %(prog)s train --rounds 3 dataset/clients/*.csv   # Full training orchestration
  %(prog)s quick-train --rounds 2                   # Quick training with defaults
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show system status and statistics')
    
    # Register command
    subparsers.add_parser('register', help='Register a new client')
    
    # Clients command
    subparsers.add_parser('clients', help='List all registered clients')
    
    # Rounds command
    subparsers.add_parser('rounds', help='Show training round history')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if a client is registered')
    check_parser.add_argument('client_id', help='Client ID to check')
    
    # Candid command
    candid_parser = subparsers.add_parser('candid', help='Get Candid interface URL')
    candid_parser.add_argument('--open', action='store_true', help='Open in browser')

    # Admin commands
    init_admin_parser = subparsers.add_parser('init-admin', help='Initialize admin role (run once after deployment)')

    pending_parser = subparsers.add_parser('pending', help='List clients pending approval')

    approve_parser = subparsers.add_parser('approve', help='Approve a pending client')
    approve_parser.add_argument('client_id', help='Principal ID of client to approve')

    reject_parser = subparsers.add_parser('reject', help='Reject a pending client')
    reject_parser.add_argument('client_id', help='Principal ID of client to reject')

    setup_server_parser = subparsers.add_parser('setup-server', help='Set up server role')
    setup_server_parser.add_argument('server_principal', help='Principal ID of the server')

    # Train command (full orchestration)
    train_parser = subparsers.add_parser('train', help='Orchestrate complete federated learning session')
    train_parser.add_argument('datasets', nargs='+', help='Client dataset files')
    train_parser.add_argument('--rounds', type=int, default=3, help='Number of training rounds (default: 3)')
    train_parser.add_argument('--wait-timeout', type=int, default=120, help='Timeout waiting for clients (default: 120s)')
    train_parser.add_argument('--no-auto-start', dest='auto_start_clients', action='store_false',
                             help='Do not automatically start clients')
    train_parser.add_argument('--client-delay', type=float, default=2.0,
                             help='Delay between starting clients (default: 2.0s)')

    # Quick train command
    quick_train_parser = subparsers.add_parser('quick-train', help='Quick training with default datasets')
    quick_train_parser.add_argument('--rounds', type=int, default=2, help='Number of training rounds (default: 2)')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    commands = {
        'status': cmd_status,
        'register': cmd_register,
        'clients': cmd_clients,
        'rounds': cmd_rounds,
        'check': cmd_check,
        'candid': cmd_candid,
        'init-admin': cmd_init_admin,
        'pending': cmd_pending_clients,
        'approve': cmd_approve_client,
        'reject': cmd_reject_client,
        'setup-server': cmd_setup_server,
        'train': cmd_train,
        'quick-train': cmd_quick_train,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
