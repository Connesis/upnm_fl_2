#!/usr/bin/env python3
"""
Simple Model Verification Script
Verifies specific model files against stored hashes in the canister.
"""

import os
import sys
import hashlib
import logging
from typing import Optional
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA256 hash of a file."""
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"❌ Error calculating hash: {e}")
        return None

def verify_model_round(round_id: int):
    """Verify a specific training round model."""
    print(f"\n🔍 Verifying Model for Round {round_id}")
    print("-" * 50)
    
    # Initialize ICP client
    load_dotenv()
    os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    icp_client = AuthenticatedICPClient(identity_type="server")
    icp_client.identity_name = "fl_server"
    
    if not icp_client.canister_id:
        print("❌ Failed to connect to canister")
        return False
    
    try:
        # Get metadata for the round
        print(f"📋 Retrieving metadata for round {round_id}...")
        result = icp_client._call_canister("get_training_round_metadata", f"({round_id})")
        
        if not result or "null" in str(result):
            print(f"❌ No metadata found for round {round_id}")
            return False
        
        result_str = str(result)
        print(f"✅ Metadata retrieved successfully")
        
        # Parse model hash
        import re
        hash_pattern = r'model_hash = "([a-f0-9]{64})"'
        hash_match = re.search(hash_pattern, result_str)
        
        if not hash_match:
            print("❌ Could not parse model hash from metadata")
            return False
        
        stored_hash = hash_match.group(1)
        print(f"🔐 Stored Hash: {stored_hash[:16]}...{stored_hash[-8:]}")
        
        # Parse model filename
        filename_pattern = r'model_filename = "([^"]+)"'
        filename_match = re.search(filename_pattern, result_str)
        
        if not filename_match:
            print("❌ Could not parse model filename from metadata")
            return False
        
        model_filename = filename_match.group(1)
        print(f"📁 Model File: {model_filename}")
        
        # Find model file
        model_path = os.path.join("models", model_filename)
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
        
        print(f"📂 File exists: {model_path}")
        
        # Calculate actual hash
        print("🧮 Calculating file hash...")
        calculated_hash = calculate_file_hash(model_path)
        
        if not calculated_hash:
            print("❌ Failed to calculate file hash")
            return False
        
        print(f"🧮 Calculated Hash: {calculated_hash[:16]}...{calculated_hash[-8:]}")
        
        # Verify integrity
        if stored_hash == calculated_hash:
            print("✅ MODEL INTEGRITY VERIFIED!")
            print("🎉 Hash matches - model file is authentic and unmodified")
            return True
        else:
            print("❌ MODEL INTEGRITY VERIFICATION FAILED!")
            print("⚠️  Hash mismatch - model file may have been modified or corrupted")
            print(f"   Expected: {stored_hash}")
            print(f"   Actual:   {calculated_hash}")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def list_available_models():
    """List available model files and their corresponding rounds."""
    print("\n📁 Available Model Files:")
    print("-" * 30)
    
    models_dir = "models"
    if not os.path.exists(models_dir):
        print("❌ Models directory not found")
        return
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.joblib') and 'federated_cvd_model' in f]
    
    if not model_files:
        print("❌ No model files found")
        return
    
    for i, filename in enumerate(sorted(model_files), 1):
        file_path = os.path.join(models_dir, filename)
        file_size = os.path.getsize(file_path)
        
        # Extract round number from filename
        import re
        round_match = re.search(r'round_(\d+)', filename)
        round_num = round_match.group(1) if round_match else "Unknown"
        
        print(f"   {i}. Round {round_num}: {filename}")
        print(f"      Size: {file_size:,} bytes")
        print(f"      Path: {file_path}")

def main():
    """Main verification function."""
    print("🔍 Model Hash Verification System")
    print("=" * 50)
    
    # List available models
    list_available_models()
    
    # Test verification for rounds 1 and 2
    print("\n🧪 Testing Model Verification:")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    for round_id in [1, 2]:
        total_count += 1
        if verify_model_round(round_id):
            success_count += 1
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 30)
    print(f"Total Models Tested: {total_count}")
    print(f"Successfully Verified: {success_count}")
    print(f"Failed Verification: {total_count - success_count}")
    print(f"Success Rate: {(success_count/total_count*100):.1f}%" if total_count > 0 else "N/A")
    
    if success_count == total_count and total_count > 0:
        print("\n🎉 ALL MODELS VERIFIED SUCCESSFULLY!")
        print("✅ Model integrity is maintained - no tampering detected")
    elif success_count < total_count:
        print("\n⚠️  SOME MODELS FAILED VERIFICATION!")
        print("❌ Please investigate failed models for potential issues")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
