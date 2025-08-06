"""
Test script for the ICP client library.
"""
import sys
import os

# Add the current directory to the path so we can import icp_client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from icp_client import ICPClient, get_fl_system_stats


def test_icp_client():
    """Test the ICP client functionality."""
    print("Testing ICP Client Library")
    print("=" * 50)
    
    # Initialize client
    client = ICPClient()
    print(f"Canister ID: {client.canister_id}")
    
    # Test system stats
    print("\n1. Testing system stats...")
    stats = client.get_system_stats()
    if stats:
        print(f"   Total clients: {stats.total_clients}")
        print(f"   Active clients: {stats.active_clients}")
        print(f"   Total rounds: {stats.total_rounds}")
        print(f"   Completed rounds: {stats.completed_rounds}")
        print(f"   Total samples processed: {stats.total_samples_processed}")
    else:
        print("   Failed to get system stats")
    
    # Test client registration
    print("\n2. Testing client registration...")
    success = client.register_client()
    print(f"   Registration result: {success}")
    
    # Test system stats again
    print("\n3. Testing system stats after registration...")
    stats = client.get_system_stats()
    if stats:
        print(f"   Total clients: {stats.total_clients}")
        print(f"   Active clients: {stats.active_clients}")
    else:
        print("   Failed to get system stats")
    
    print("\n" + "=" * 50)
    print("ICP client test completed!")


if __name__ == "__main__":
    test_icp_client()
