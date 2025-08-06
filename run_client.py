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
    
    args = parser.parse_args()
    
    print(f"Starting federated learning client with dataset: {args.dataset}")
    
    if not os.path.exists(args.dataset):
        print(f"Error: Dataset file not found at {args.dataset}")
        return 1
    
    try:
        client_main(args.dataset)
        return 0
    except Exception as e:
        print(f"Error running client: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())