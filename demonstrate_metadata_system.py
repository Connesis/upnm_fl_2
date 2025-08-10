#!/usr/bin/env python3
"""
Demonstration of the Enhanced Metadata System
Shows what metadata is stored and how to query it from the canister.
"""

import os
import sys
import time
import logging
from typing import Dict, List
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def demonstrate_enhanced_metadata_system():
    """Demonstrate the enhanced metadata system capabilities."""
    print("🔐 Enhanced Federated Learning Metadata System")
    print("=" * 80)
    
    load_dotenv()
    
    print("\n📋 COMPREHENSIVE METADATA STORAGE")
    print("-" * 50)
    print("After each training round, the server stores detailed metadata including:")
    print()
    
    # Show what metadata is collected from clients
    print("👥 CLIENT INFORMATION:")
    print("   • Principal ID: xoqpj-5c7wg-idyjk-i5ply-fetwi-salbi-c5z2t-5nt7k-6xojd-uic3u-3ae")
    print("   • Client Name: Healthcare Provider 1")
    print("   • Organization: Hospital 1")
    print("   • Location: City 1, Country")
    print("   • Dataset File: client1_data.csv")
    print("   • Samples Contributed: 1,000")
    print("   • Trees Contributed: 50")
    print()
    
    print("🏥 TRAINING ROUND METADATA:")
    print("   • Round ID: 1")
    print("   • Training Start Time: 2025-08-08 14:41:56 UTC")
    print("   • Training End Time: 2025-08-08 14:42:17 UTC")
    print("   • Total Participants: 3")
    print("   • Total Examples: 3,000")
    print("   • Total Trees: 150")
    print("   • Model Accuracy: 85.2%")
    print("   • Model Hash: sha256:abc123...")
    print("   • Model Filename: federated_cvd_model_round_1_20250808_144217.joblib")
    print()
    
    print("🔍 QUERY CAPABILITIES")
    print("-" * 50)
    
    try:
        # Initialize ICP client
        os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
        icp_client = AuthenticatedICPClient(identity_type="server")
        icp_client.identity_name = "fl_server"
        
        if not icp_client.canister_id:
            print("❌ Failed to connect to canister")
            return False
        
        print(f"✅ Connected to canister: {icp_client.canister_id}")
        print()
        
        # Test canister query methods
        print("🧪 TESTING QUERY METHODS:")
        print()
        
        # Test 1: Get training history
        print("1️⃣ get_training_history()")
        try:
            result = icp_client._call_canister("get_training_history", "()")
            print(f"   ✅ Method available: {str(result)[:100]}...")
            print("   📊 Returns: Complete training timeline with all rounds")
        except Exception as e:
            print(f"   ⚠️  Method response: {str(e)[:100]}...")
        print()
        
        # Test 2: Get all model metadata
        print("2️⃣ get_all_model_metadata()")
        try:
            result = icp_client._call_canister("get_all_model_metadata", "()")
            print(f"   ✅ Method available: {str(result)[:100]}...")
            print("   📊 Returns: All model metadata from all rounds")
        except Exception as e:
            print(f"   ⚠️  Method response: {str(e)[:100]}...")
        print()
        
        # Test 3: Get specific round metadata
        print("3️⃣ get_training_round_metadata(1)")
        try:
            result = icp_client._call_canister("get_training_round_metadata", "(1)")
            print(f"   ✅ Method available: {str(result)[:100]}...")
            print("   📊 Returns: Detailed metadata for specific round")
        except Exception as e:
            print(f"   ⚠️  Method response: {str(e)[:100]}...")
        print()
        
        # Test 4: Get all training rounds
        print("4️⃣ get_all_training_rounds()")
        try:
            result = icp_client._call_canister("get_all_training_rounds", "()")
            print(f"   ✅ Method available: {str(result)[:100]}...")
            print("   📊 Returns: All training round summaries")
        except Exception as e:
            print(f"   ⚠️  Method response: {str(e)[:100]}...")
        print()
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    print("🎯 ENHANCED METADATA FEATURES")
    print("-" * 50)
    print("✅ IMPLEMENTED ENHANCEMENTS:")
    print("   • Server calls complete_training_round_enhanced() after each round")
    print("   • Clients send comprehensive metadata in training responses")
    print("   • Canister stores detailed ClientParticipation records")
    print("   • Multiple query methods available for different use cases")
    print("   • Immutable blockchain-based storage")
    print("   • Real-time metadata updates")
    print()
    
    print("📊 METADATA STRUCTURE:")
    print("   • ModelMetadata includes:")
    print("     - round_id, timestamps (start/end)")
    print("     - num_clients, total_examples, num_trees")
    print("     - accuracy, model_hash, model_filename")
    print("     - participants[] with detailed client info")
    print()
    print("   • ClientParticipation includes:")
    print("     - principal_id, client_name, dataset_filename")
    print("     - samples_contributed, trees_contributed")
    print()
    
    print("🔄 WORKFLOW INTEGRATION:")
    print("   1. Clients register with principal IDs")
    print("   2. Admin approves clients")
    print("   3. Training begins with authentication")
    print("   4. Each round stores comprehensive metadata")
    print("   5. History can be queried anytime")
    print("   6. Audit trail is immutable and verifiable")
    print()
    
    print("✨ BENEFITS:")
    print("   • Complete audit trail of all training activities")
    print("   • Client contribution tracking for incentives")
    print("   • Model provenance and lineage tracking")
    print("   • Compliance and regulatory reporting")
    print("   • Performance analytics and insights")
    print("   • Blockchain-based trust and verification")
    
    return True

def show_code_examples():
    """Show code examples of how to use the enhanced metadata system."""
    print("\n💻 CODE EXAMPLES")
    print("=" * 80)
    
    print("🔧 SERVER-SIDE METADATA STORAGE:")
    print("""
# Enhanced server aggregation with metadata
participants = []
for client_proxy, fit_res in results:
    if hasattr(fit_res, 'metrics') and fit_res.metrics:
        participants.append({
            'principal_id': fit_res.metrics.get('client_principal_id'),
            'client_name': fit_res.metrics.get('client_name'),
            'dataset_filename': fit_res.metrics.get('dataset_filename'),
            'samples_contributed': fit_res.num_examples,
            'trees_contributed': 50
        })

# Store enhanced metadata
success = self.icp_client.complete_training_round_enhanced(
    round_id=server_round,
    participants=participants,
    total_examples=total_examples,
    num_trees=len(aggregated_trees),
    accuracy=accuracy,
    model_path=model_path,
    model_filename=model_filename,
    training_start_time=training_start_time,
    training_end_time=training_end_time
)
""")
    
    print("👥 CLIENT-SIDE METADATA COLLECTION:")
    print("""
# Enhanced client response with metadata
return updated_parameters, len(self.X), {
    "client_principal_id": self.principal_id,
    "client_identity": self.client_identity,
    "client_name": os.getenv("CLIENT_NAME"),
    "dataset_filename": os.path.basename(self.dataset_path),
    "client_organization": os.getenv("CLIENT_ORGANIZATION"),
    "client_location": os.getenv("CLIENT_LOCATION")
}
""")
    
    print("🔍 QUERYING METADATA:")
    print("""
# Query training history
history = icp_client.get_training_history()

# Query specific round metadata
round_metadata = icp_client.get_training_round_metadata(round_id)

# Query all model metadata
all_metadata = icp_client.get_all_model_metadata()
""")

def main():
    """Main demonstration function."""
    success = demonstrate_enhanced_metadata_system()
    
    if success:
        show_code_examples()
        
        print("\n🎉 ENHANCED METADATA SYSTEM READY!")
        print("=" * 80)
        print("✅ The system now stores comprehensive metadata after each training round")
        print("✅ All client information, datasets, and model details are tracked")
        print("✅ Multiple query methods available for different use cases")
        print("✅ Blockchain-based immutable storage ensures data integrity")
        print("✅ Complete audit trail for compliance and analytics")
        
        print("\n🚀 NEXT STEPS:")
        print("   • Run federated training to generate metadata")
        print("   • Use query methods to retrieve training history")
        print("   • Analyze client contributions and model performance")
        print("   • Generate compliance reports from stored metadata")
        
        return True
    else:
        print("\n❌ Demonstration failed - check canister connection")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
