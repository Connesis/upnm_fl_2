#!/usr/bin/env python3
"""
Model Verification System
Verifies model file integrity by comparing stored hashes with actual file hashes.
"""

import os
import sys
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
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

class ModelVerificationSystem:
    """System for verifying model file integrity against blockchain records."""
    
    def __init__(self):
        """Initialize the verification system."""
        load_dotenv()
        self.models_dir = "models"
        
        # Initialize ICP client
        os.environ["ICP_CLIENT_IDENTITY_NAME"] = "fl_server"
        self.icp_client = AuthenticatedICPClient(identity_type="server")
        self.icp_client.identity_name = "fl_server"
        
        logger.info("🔍 Model Verification System Initialized")
        logger.info(f"   Models Directory: {self.models_dir}")
        logger.info(f"   Canister ID: {self.icp_client.canister_id}")
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of a file."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return None
            
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            file_hash = sha256_hash.hexdigest()
            logger.info(f"📊 Calculated hash for {os.path.basename(file_path)}: {file_hash[:16]}...")
            return file_hash
            
        except Exception as e:
            logger.error(f"❌ Error calculating hash for {file_path}: {e}")
            return None
    
    def get_stored_metadata(self, round_id: int) -> Optional[Dict]:
        """Get stored metadata for a specific training round."""
        try:
            result = self.icp_client._call_canister("get_training_round_metadata", f"({round_id})")
            if result and "opt" in str(result):
                logger.info(f"✅ Retrieved metadata for round {round_id}")
                return {"raw_result": str(result)}
            else:
                logger.warning(f"⚠️  No metadata found for round {round_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error retrieving metadata for round {round_id}: {e}")
            return None
    
    def parse_metadata_hash(self, metadata_result: str) -> Optional[str]:
        """Parse model hash from metadata result."""
        try:
            # Extract model_hash from the Candid result
            import re
            hash_pattern = r'model_hash = "([a-f0-9]{64})"'
            match = re.search(hash_pattern, metadata_result)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing metadata hash: {e}")
            return None
    
    def parse_metadata_filename(self, metadata_result: str) -> Optional[str]:
        """Parse model filename from metadata result."""
        try:
            # Extract model_filename from the Candid result
            import re
            filename_pattern = r'model_filename = "([^"]+)"'
            match = re.search(filename_pattern, metadata_result)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing metadata filename: {e}")
            return None
    
    def verify_model_integrity(self, round_id: int) -> Dict[str, any]:
        """Verify model integrity for a specific training round."""
        logger.info(f"🔍 Verifying model integrity for round {round_id}")
        
        result = {
            "round_id": round_id,
            "verified": False,
            "stored_hash": None,
            "calculated_hash": None,
            "model_filename": None,
            "file_exists": False,
            "error": None
        }
        
        try:
            # Get stored metadata
            metadata = self.get_stored_metadata(round_id)
            if not metadata:
                result["error"] = "No metadata found for this round"
                return result
            
            # Parse stored hash and filename
            metadata_str = metadata["raw_result"]
            stored_hash = self.parse_metadata_hash(metadata_str)
            model_filename = self.parse_metadata_filename(metadata_str)
            
            if not stored_hash:
                result["error"] = "Could not parse stored hash from metadata"
                return result
            
            if not model_filename:
                result["error"] = "Could not parse model filename from metadata"
                return result
            
            result["stored_hash"] = stored_hash
            result["model_filename"] = model_filename
            
            # Find model file
            model_path = os.path.join(self.models_dir, model_filename)
            result["file_exists"] = os.path.exists(model_path)
            
            if not result["file_exists"]:
                result["error"] = f"Model file not found: {model_path}"
                return result
            
            # Calculate actual file hash
            calculated_hash = self.calculate_file_hash(model_path)
            if not calculated_hash:
                result["error"] = "Could not calculate file hash"
                return result
            
            result["calculated_hash"] = calculated_hash
            
            # Verify integrity
            result["verified"] = (stored_hash == calculated_hash)
            
            if result["verified"]:
                logger.info(f"✅ Model integrity verified for round {round_id}")
            else:
                logger.error(f"❌ Model integrity verification FAILED for round {round_id}")
                logger.error(f"   Stored hash:    {stored_hash}")
                logger.error(f"   Calculated hash: {calculated_hash}")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error during verification: {e}")
            return result
    
    def verify_all_models(self) -> List[Dict[str, any]]:
        """Verify integrity of all stored models."""
        logger.info("🔍 Verifying integrity of all stored models")
        
        results = []
        
        try:
            # Get all training rounds
            all_rounds_result = self.icp_client._call_canister("get_all_training_rounds", "()")
            
            if not all_rounds_result:
                logger.warning("⚠️  No training rounds found")
                return results
            
            # Parse round IDs from result
            import re
            round_pattern = r'record \{\s*(\d+) : nat;'
            round_matches = re.findall(round_pattern, str(all_rounds_result))
            
            if not round_matches:
                logger.warning("⚠️  Could not parse round IDs from result")
                return results
            
            round_ids = [int(match) for match in round_matches]
            logger.info(f"📋 Found {len(round_ids)} training rounds: {round_ids}")
            
            # Verify each round
            for round_id in round_ids:
                result = self.verify_model_integrity(round_id)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error verifying all models: {e}")
            return results
    
    def generate_verification_report(self, results: List[Dict[str, any]]) -> None:
        """Generate a comprehensive verification report."""
        logger.info("📋 Generating Model Verification Report")
        print("\n" + "=" * 80)
        print("🔍 MODEL INTEGRITY VERIFICATION REPORT")
        print("=" * 80)
        
        total_models = len(results)
        verified_models = sum(1 for r in results if r["verified"])
        failed_models = total_models - verified_models
        
        print(f"📊 SUMMARY:")
        print(f"   • Total Models: {total_models}")
        print(f"   • ✅ Verified: {verified_models}")
        print(f"   • ❌ Failed: {failed_models}")
        print(f"   • Success Rate: {(verified_models/total_models*100):.1f}%" if total_models > 0 else "   • Success Rate: N/A")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in results:
            round_id = result["round_id"]
            status = "✅ VERIFIED" if result["verified"] else "❌ FAILED"
            
            print(f"\n🔄 Round {round_id}: {status}")
            print(f"   📁 Model File: {result['model_filename'] or 'Unknown'}")
            print(f"   📂 File Exists: {'✅ Yes' if result['file_exists'] else '❌ No'}")
            
            if result["stored_hash"]:
                print(f"   🔐 Stored Hash:    {result['stored_hash'][:16]}...{result['stored_hash'][-8:]}")
            
            if result["calculated_hash"]:
                print(f"   🧮 Calculated Hash: {result['calculated_hash'][:16]}...{result['calculated_hash'][-8:]}")
            
            if result["error"]:
                print(f"   ⚠️  Error: {result['error']}")
        
        print("\n" + "=" * 80)
        
        if verified_models == total_models and total_models > 0:
            print("🎉 ALL MODELS VERIFIED SUCCESSFULLY!")
            print("✅ Model integrity is maintained across all training rounds")
        elif failed_models > 0:
            print("⚠️  SOME MODELS FAILED VERIFICATION!")
            print("❌ Please investigate failed models for potential tampering")
        
        print("=" * 80)


def main():
    """Main function to run model verification."""
    print("🔍 Model Integrity Verification System")
    print("=" * 50)
    
    verifier = ModelVerificationSystem()
    
    if not verifier.icp_client.canister_id:
        print("❌ Failed to connect to ICP canister")
        return 1
    
    # Verify all models
    results = verifier.verify_all_models()
    
    if not results:
        print("⚠️  No models found to verify")
        return 1
    
    # Generate report
    verifier.generate_verification_report(results)
    
    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r["verified"])
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
