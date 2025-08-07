"""
Script to run a federated learning client with the cardiovascular dataset.
"""
import argparse
import sys
import os

# Add client directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'client'))

from client.client import main as client_main


def main():
    """Main function to run the client."""
    parser = argparse.ArgumentParser(description="Federated Learning Client for CVD Prediction")
    parser.add_argument("--dataset", type=str, default="dataset/cardio_train.csv",
                        help="Path to dataset CSV file")
    parser.add_argument("--max-wait-time", type=int, default=300,
                        help="Maximum time to wait for server in seconds (default: 300)")
    parser.add_argument("--retry-interval", type=int, default=5,
                        help="Initial retry interval in seconds (default: 5)")

    args = parser.parse_args()

    print(f"Starting federated learning client:")
    print(f"  • Dataset: {args.dataset}")
    print(f"  • Max wait time: {args.max_wait_time}s")
    print(f"  • Retry interval: {args.retry_interval}s")

    if not os.path.exists(args.dataset):
        print(f"Error: Dataset file not found at {args.dataset}")
        return 1

    try:
        client_main(args.dataset, args.max_wait_time, args.retry_interval)
        return 0
    except Exception as e:
        print(f"Error running client: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())