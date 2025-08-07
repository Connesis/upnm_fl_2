"""
Script to run the federated learning server.
"""
import argparse
import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.server import main as server_main


def main():
    """Main function to run the server."""
    parser = argparse.ArgumentParser(description="Federated Learning Server for CVD Prediction")
    parser.add_argument("--rounds", type=int, default=5,
                        help="Number of federated learning rounds")
    parser.add_argument("--min-clients", type=int, default=1,
                        help="Minimum number of clients required to start training")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port for the server to listen on")

    args = parser.parse_args()

    print(f"Starting federated learning server:")
    print(f"  • Rounds: {args.rounds}")
    print(f"  • Minimum clients: {args.min_clients}")
    print(f"  • Port: {args.port}")

    try:
        server_main(args.rounds, args.min_clients, args.port)
        return 0
    except Exception as e:
        print(f"Error running server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())