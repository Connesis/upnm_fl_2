"""
Python client library for interacting with the ICP FL_CVD_Backend canister.
"""
import subprocess
import json
import os
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Client:
    """Represents a federated learning client."""
    id: str
    registered_at: int
    last_active: int
    status: str
    total_rounds_participated: int
    total_samples_contributed: int


@dataclass
class ModelMetadata:
    """Represents model metadata for a training round."""
    round_id: int
    timestamp: int
    num_clients: int
    total_examples: int
    num_trees: int
    accuracy: float
    model_hash: str


@dataclass
class TrainingRound:
    """Represents a training round."""
    id: int
    timestamp: int
    model_file: str
    participants: List[str]
    status: str
    metadata: Optional[ModelMetadata]


@dataclass
class SystemStats:
    """Represents system statistics."""
    total_clients: int
    active_clients: int
    total_rounds: int
    completed_rounds: int
    total_samples_processed: int


class ICPClient:
    """Client for interacting with the ICP FL_CVD_Backend canister."""

    def __init__(self, canister_name: str = "fl_cvd_backend_backend", dfx_path: str = "dfx", icp_project_dir: str = None):
        """
        Initialize the ICP client.

        Args:
            canister_name: Name of the canister to interact with
            dfx_path: Path to the dfx executable
            icp_project_dir: Directory containing the dfx.json file
        """
        self.canister_name = canister_name
        self.dfx_path = dfx_path

        # Set the ICP project directory
        if icp_project_dir is None:
            # Try to find the ICP project directory
            current_dir = os.getcwd()
            if os.path.exists(os.path.join(current_dir, "icp", "fl_cvd_backend", "dfx.json")):
                self.icp_project_dir = os.path.join(current_dir, "icp", "fl_cvd_backend")
            elif os.path.exists(os.path.join(current_dir, "dfx.json")):
                self.icp_project_dir = current_dir
            else:
                self.icp_project_dir = os.path.join(current_dir, "icp", "fl_cvd_backend")
        else:
            self.icp_project_dir = icp_project_dir

        self.canister_id = self._get_canister_id()
    
    def _get_canister_id(self) -> Optional[str]:
        """Get the canister ID from dfx."""
        try:
            result = subprocess.run(
                [self.dfx_path, "canister", "id", self.canister_name],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.icp_project_dir
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _call_canister(self, method: str, args: str = "") -> Dict[str, Any]:
        """
        Call a canister method and return the result.
        
        Args:
            method: The method name to call
            args: Arguments to pass to the method
            
        Returns:
            Parsed result from the canister call
        """
        cmd = [self.dfx_path, "canister", "call", self.canister_name, method]
        if args:
            cmd.append(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=self.icp_project_dir)
            # Parse the Candid output (simplified parsing)
            output = result.stdout.strip()
            return self._parse_candid_output(output)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Canister call failed: {e.stderr}")
    
    def _parse_candid_output(self, output: str) -> Dict[str, Any]:
        """
        Parse Candid output to Python objects (simplified).
        
        Args:
            output: Raw Candid output
            
        Returns:
            Parsed Python object
        """
        # This is a simplified parser - in production, use a proper Candid parser
        try:
            # Remove outer parentheses and parse as JSON-like structure
            cleaned = output.strip("(),\n ")
            if cleaned.startswith("record"):
                # Extract record content
                start = cleaned.find("{")
                end = cleaned.rfind("}")
                if start != -1 and end != -1:
                    record_content = cleaned[start+1:end]
                    # Simple parsing for basic types
                    result = {}
                    for item in record_content.split(";"):
                        if "=" in item:
                            key, value = item.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            # Parse different types
                            if ":" in value and "nat" in value:
                                result[key] = int(value.split(":")[0].strip())
                            elif ":" in value and "text" in value:
                                result[key] = value.split(":")[0].strip().strip('"')
                            elif ":" in value and "float" in value:
                                result[key] = float(value.split(":")[0].strip())
                            else:
                                result[key] = value
                    return result
            return {"raw": output}
        except Exception:
            return {"raw": output}
    
    # Client management methods
    def register_client(self) -> bool:
        """Register the current client with the canister."""
        try:
            result = self._call_canister("register_client_enhanced")
            return "Success" in str(result)
        except Exception:
            return False
    
    def get_client_info(self, client_id: str) -> Optional[Client]:
        """Get information about a specific client."""
        try:
            result = self._call_canister("get_client_info", f'(principal "{client_id}")')
            if result and "raw" not in result:
                return Client(**result)
            return None
        except Exception:
            return None
    
    def get_active_clients(self) -> List[Client]:
        """Get list of all active clients."""
        try:
            result = self._call_canister("get_active_clients")
            # Parse array of clients (simplified)
            return []  # TODO: Implement proper array parsing
        except Exception:
            return []
    
    def is_client_registered(self, client_id: str) -> bool:
        """Check if a client is registered."""
        try:
            result = self._call_canister("is_client_registered", f'(principal "{client_id}")')
            return "true" in str(result).lower()
        except Exception:
            return False
    
    def is_client_active(self, client_id: str) -> bool:
        """Check if a client is active."""
        try:
            result = self._call_canister("is_client_active", f'(principal "{client_id}")')
            return "true" in str(result).lower()
        except Exception:
            return False
    
    # Training round methods
    def start_training_round(self, participants: List[str]) -> Optional[int]:
        """Start a new training round."""
        try:
            # Format participants as Candid array
            participants_str = "vec {" + "; ".join([f'principal "{p}"' for p in participants]) + "}"
            result = self._call_canister("start_training_round", f"({participants_str})")
            # Extract round ID from result
            if "opt" in str(result):
                # Parse optional nat
                return 1  # TODO: Implement proper parsing
            return None
        except Exception:
            return None
    
    def complete_training_round(self, round_id: int, participants: List[str],
                              total_examples: int, num_trees: int,
                              accuracy: float, model_path: str) -> bool:
        """Complete a training round with basic metadata (legacy method)."""
        try:
            # Calculate model hash
            model_hash = self._calculate_file_hash(model_path) if os.path.exists(model_path) else "unknown"

            # Format arguments (using commas for Candid syntax)
            participants_str = "vec {" + "; ".join([f'principal "{p}"' for p in participants]) + "}"
            args = f"({round_id}, {participants_str}, {total_examples}, {num_trees}, {accuracy}, \"{model_hash}\")"

            result = self._call_canister("complete_training_round", args)
            return "true" in str(result).lower()
        except Exception:
            return False

    def start_training_round(self, participants: List[str]) -> Optional[int]:
        """Start a new training round with the given participants."""
        try:
            # Format participant principal IDs
            participants_str = "vec {" + "; ".join([f'principal "{p}"' for p in participants]) + "}"
            args = f"({participants_str})"

            result = self._call_canister("start_training_round", args)
            # Parse the result to get the round ID
            if result and "opt" in str(result):
                # Extract round ID from result like "(opt (1 : nat))"
                result_str = str(result)
                if "opt" in result_str and "nat" in result_str:
                    # Simple parsing - extract number
                    import re
                    match = re.search(r'(\d+)', result_str)
                    if match:
                        return int(match.group(1))
            return None
        except Exception as e:
            print(f"Error starting training round: {e}")
            return None

    def complete_training_round_enhanced(self, round_id: int, participants: List[Dict],
                                       total_examples: int, num_trees: int,
                                       accuracy: float, model_path: str, model_filename: str,
                                       training_start_time: int, training_end_time: int) -> bool:
        """Complete a training round with enhanced metadata."""
        try:
            # Calculate model hash
            model_hash = self._calculate_file_hash(model_path) if os.path.exists(model_path) else "unknown"

            # Format participant data
            participants_str = "vec {" + "; ".join([
                f"record {{ principal_id = principal \"{p['principal_id']}\"; "
                f"client_name = \"{p['client_name']}\"; "
                f"dataset_filename = \"{p['dataset_filename']}\"; "
                f"samples_contributed = {p['samples_contributed']}; "
                f"trees_contributed = {p['trees_contributed']} }}"
                for p in participants
            ]) + "}"

            # Format arguments (using commas for Candid syntax)
            args = (f"({round_id}, {participants_str}, {total_examples}, {num_trees}, "
                   f"{accuracy}, \"{model_hash}\", \"{model_filename}\", "
                   f"{training_start_time}, {training_end_time})")

            result = self._call_canister("complete_training_round_enhanced", args)
            return "true" in str(result).lower()
        except Exception as e:
            print(f"Error completing enhanced training round: {e}")
            return False

    def get_training_round(self, round_id: int) -> Optional[TrainingRound]:
        """Get information about a specific training round."""
        try:
            result = self._call_canister("get_training_round", f"({round_id})")
            # TODO: Implement proper parsing
            return None
        except Exception:
            return None

    def get_training_round_metadata(self, round_id: int) -> Optional[Dict]:
        """Get detailed metadata for a specific training round."""
        try:
            result = self._call_canister("get_training_round_metadata", f"({round_id})")
            # TODO: Implement proper parsing of metadata
            return {"raw_result": str(result)}
        except Exception as e:
            print(f"Error getting training round metadata: {e}")
            return None

    def get_training_history(self) -> Optional[Dict]:
        """Get complete training history with metadata."""
        try:
            result = self._call_canister("get_training_history", "()")
            # TODO: Implement proper parsing of training history
            return {"raw_result": str(result)}
        except Exception as e:
            print(f"Error getting training history: {e}")
            return None

    def get_all_model_metadata(self) -> Optional[Dict]:
        """Get all model metadata from all training rounds."""
        try:
            result = self._call_canister("get_all_model_metadata", "()")
            # TODO: Implement proper parsing of metadata array
            return {"raw_result": str(result)}
        except Exception as e:
            print(f"Error getting all model metadata: {e}")
            return None

    def verify_model_hash(self, round_id: int, model_file_path: str) -> bool:
        """Verify model file hash against stored hash in canister."""
        try:
            # Get stored metadata
            metadata = self.get_training_round_metadata(round_id)
            if not metadata:
                print(f"No metadata found for round {round_id}")
                return False

            # Parse stored hash from metadata
            import re
            metadata_str = metadata["raw_result"]
            hash_pattern = r'model_hash = "([a-f0-9]{64})"'
            match = re.search(hash_pattern, metadata_str)

            if not match:
                print(f"Could not parse stored hash for round {round_id}")
                return False

            stored_hash = match.group(1)

            # Calculate actual file hash
            calculated_hash = self._calculate_file_hash(model_file_path)
            if not calculated_hash:
                print(f"Could not calculate hash for file: {model_file_path}")
                return False

            # Compare hashes
            verified = (stored_hash == calculated_hash)

            if verified:
                print(f"✅ Model hash verified for round {round_id}")
                print(f"   Hash: {stored_hash[:16]}...{stored_hash[-8:]}")
            else:
                print(f"❌ Model hash verification FAILED for round {round_id}")
                print(f"   Stored:    {stored_hash}")
                print(f"   Calculated: {calculated_hash}")

            return verified

        except Exception as e:
            print(f"Error verifying model hash: {e}")
            return False

    def get_system_stats(self) -> Optional[SystemStats]:
        """Get system statistics."""
        try:
            result = self._call_canister("get_system_stats")
            if result and "raw" not in result:
                return SystemStats(
                    total_clients=result.get("total_clients", 0),
                    active_clients=result.get("active_clients", 0),
                    total_rounds=result.get("total_rounds", 0),
                    completed_rounds=result.get("completed_rounds", 0),
                    total_samples_processed=result.get("total_samples_processed", 0)
                )
            return None
        except Exception:
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "unknown"


# Convenience functions
def get_icp_client() -> ICPClient:
    """Get a configured ICP client instance."""
    return ICPClient()


def register_fl_client() -> bool:
    """Register the current federated learning client."""
    client = get_icp_client()
    return client.register_client()


def get_fl_system_stats() -> Optional[SystemStats]:
    """Get federated learning system statistics."""
    client = get_icp_client()
    return client.get_system_stats()
