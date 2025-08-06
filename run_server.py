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
    
    args = parser.parse_args()
    
    print(f"Starting federated learning server for {args.rounds} rounds")
    
    try:
        server_main(args.rounds)
        return 0
    except Exception as e:
        print(f"Error running server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())