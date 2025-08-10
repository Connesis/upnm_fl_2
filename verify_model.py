#!/usr/bin/env python3
"""
CLI Model Verification Tool
Command-line interface for verifying model file integrity against blockchain records.
"""

import os
import sys
import argparse
import hashlib
from typing import Optional
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.dirname(__file__))
from icp_auth_client import AuthenticatedICPClient

def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA256 hash of a file."""
    try:
        if not os.path.exists(file_path):
            return None
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    except Exception:
        return None

def verify_model_by_round(round_id: int) -> bool:
    """Verify model integrity for a specific training round."""
    load_dotenv()
    os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    icp_client = AuthenticatedICPClient(identity_type="server")
    icp_client.identity_name = "fl_server"
    
    if not icp_client.canister_id:
        print("❌ Failed to connect to canister")
        return False
    
    try:
        # Get metadata
        result = icp_client._call_canister("get_training_round_metadata", f"({round_id})")
        
        if not result or "null" in str(result):
            print(f"❌ No metadata found for round {round_id}")
            return False
        
        # Parse hash and filename
        import re
        result_str = str(result)
        
        hash_match = re.search(r'model_hash = "([a-f0-9]{64})"', result_str)
        filename_match = re.search(r'model_filename = "([^"]+)"', result_str)
        
        if not hash_match or not filename_match:
            print("❌ Could not parse metadata")
            return False
        
        stored_hash = hash_match.group(1)
        model_filename = filename_match.group(1)
        model_path = os.path.join("models", model_filename)
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
        
        # Calculate and compare hash
        calculated_hash = calculate_file_hash(model_path)
        if not calculated_hash:
            print("❌ Failed to calculate file hash")
            return False
        
        verified = (stored_hash == calculated_hash)
        
        print(f"🔍 Round {round_id} Verification:")
        print(f"   📁 File: {model_filename}")
        print(f"   🔐 Stored:    {stored_hash[:16]}...{stored_hash[-8:]}")
        print(f"   🧮 Calculated: {calculated_hash[:16]}...{calculated_hash[-8:]}")
        print(f"   ✅ Result: {'VERIFIED' if verified else 'FAILED'}")
        
        return verified
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_model_by_file(file_path: str, round_id: int) -> bool:
    """Verify a specific model file against stored hash."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    load_dotenv()
    os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
    icp_client = AuthenticatedICPClient(identity_type="server")
    icp_client.identity_name = "fl_server"
    
    try:
        # Get stored hash
        result = icp_client._call_canister("get_training_round_metadata", f"({round_id})")
        
        if not result or "null" in str(result):
            print(f"❌ No metadata found for round {round_id}")
            return False
        
        import re
        hash_match = re.search(r'model_hash = "([a-f0-9]{64})"', str(result))
        
        if not hash_match:
            print("❌ Could not parse stored hash")
            return False
        
        stored_hash = hash_match.group(1)
        calculated_hash = calculate_file_hash(file_path)
        
        if not calculated_hash:
            print("❌ Failed to calculate file hash")
            return False
        
        verified = (stored_hash == calculated_hash)
        
        print(f"🔍 File Verification:")
        print(f"   📁 File: {os.path.basename(file_path)}")
        print(f"   🔄 Round: {round_id}")
        print(f"   🔐 Stored:    {stored_hash[:16]}...{stored_hash[-8:]}")
        print(f"   🧮 Calculated: {calculated_hash[:16]}...{calculated_hash[-8:]}")
        print(f"   ✅ Result: {'VERIFIED' if verified else 'FAILED'}")
        
        return verified
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_models():
    """List available model files."""
    models_dir = "models"
    if not os.path.exists(models_dir):
        print("❌ Models directory not found")
        return
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.joblib')]
    
    if not model_files:
        print("❌ No model files found")
        return
    
    print("📁 Available Model Files:")
    for i, filename in enumerate(sorted(model_files), 1):
        file_path = os.path.join(models_dir, filename)
        file_size = os.path.getsize(file_path)
        
        # Extract round number
        import re
        round_match = re.search(r'round_(\d+)', filename)
        round_num = round_match.group(1) if round_match else "?"
        
        print(f"   {i:2d}. Round {round_num}: {filename}")
        print(f"       Size: {file_size:,} bytes")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Verify model file integrity against blockchain records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify model for round 1
  python verify_model.py --round 1
  
  # Verify specific file against round 2
  python verify_model.py --file models/my_model.joblib --round 2
  
  # List available models
  python verify_model.py --list
  
  # Verify all available rounds
  python verify_model.py --all
        """
    )
    
    parser.add_argument("--round", "-r", type=int, help="Training round to verify")
    parser.add_argument("--file", "-f", help="Specific model file to verify")
    parser.add_argument("--list", "-l", action="store_true", help="List available model files")
    parser.add_argument("--all", "-a", action="store_true", help="Verify all available rounds")
    
    args = parser.parse_args()
    
    print("🔍 Model Integrity Verification Tool")
    print("=" * 40)
    
    if args.list:
        list_models()
        return 0
    
    if args.all:
        success_count = 0
        total_count = 0
        
        for round_id in [1, 2, 3, 4, 5]:  # Check first 5 rounds
            try:
                total_count += 1
                if verify_model_by_round(round_id):
                    success_count += 1
                print()
            except:
                total_count -= 1  # Don't count rounds that don't exist
                break
        
        if total_count > 0:
            print(f"📊 Summary: {success_count}/{total_count} models verified")
            return 0 if success_count == total_count else 1
        else:
            print("❌ No models found to verify")
            return 1
    
    if args.file and args.round:
        success = verify_model_by_file(args.file, args.round)
        return 0 if success else 1
    
    if args.round:
        success = verify_model_by_round(args.round)
        return 0 if success else 1
    
    # No arguments provided
    parser.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
