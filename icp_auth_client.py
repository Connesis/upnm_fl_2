"""
Enhanced ICP client with role-based authentication and identity management.
"""
import subprocess
import json
import os
import hashlib
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Import base ICP client
from icp_client import ICPClient, Client, ModelMetadata, TrainingRound, SystemStats


@dataclass
class PendingClient:
    """Represents a client pending approval."""
    id: str
    registered_at: int
    client_name: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None


class AuthenticatedICPClient(ICPClient):
    """ICP client with role-based authentication using environment credentials."""

    def __init__(self, identity_type: str = "client", canister_name: str = "fl_cvd_backend_backend", 
                 dfx_path: str = "dfx", icp_project_dir: str = None):
        """
        Initialize authenticated ICP client.
        
        Args:
            identity_type: Type of identity ("admin", "server", "client")
            canister_name: Name of the canister
            dfx_path: Path to dfx executable
            icp_project_dir: ICP project directory
        """
        # Load environment variables
        load_dotenv()
        
        self.identity_type = identity_type
        self.principal_id = None
        self.seed_phrase = None
        self.identity_name = None
        
        # Load credentials based on identity type
        self._load_credentials()
        
        # Set up dfx identity if credentials are available
        if self.principal_id and self.identity_name:
            self._setup_dfx_identity()
        
        # Initialize base client
        super().__init__(canister_name, dfx_path, icp_project_dir)

    def _load_credentials(self):
        """Load credentials from environment variables based on identity type."""
        if self.identity_type == "admin":
            self.principal_id = os.getenv("ICP_ADMIN_PRINCIPAL_ID")
            self.seed_phrase = os.getenv("ICP_ADMIN_SEED_PHRASE")
            self.identity_name = "admin"
        elif self.identity_type == "server":
            self.principal_id = os.getenv("ICP_SERVER_PRINCIPAL_ID")
            self.seed_phrase = os.getenv("ICP_SERVER_SEED_PHRASE")
            self.identity_name = "server"
        else:  # client
            self.principal_id = os.getenv("ICP_CLIENT_PRINCIPAL_ID")
            self.seed_phrase = os.getenv("ICP_CLIENT_SEED_PHRASE")
            self.identity_name = os.getenv("ICP_CLIENT_IDENTITY_NAME", "client")

    def _setup_dfx_identity(self):
        """Set up dfx identity for authenticated calls."""
        try:
            # Check if identity already exists
            result = subprocess.run(
                [self.dfx_path, "identity", "list"],
                capture_output=True,
                text=True,
                cwd=self.icp_project_dir
            )
            
            if self.identity_name not in result.stdout:
                print(f"⚠️  Identity '{self.identity_name}' not found. Please create it manually:")
                print(f"   dfx identity new {self.identity_name} --storage-mode password-protected")
                print(f"   dfx identity use {self.identity_name}")
                return False
            
            # Use the specified identity
            subprocess.run(
                [self.dfx_path, "identity", "use", self.identity_name],
                capture_output=True,
                text=True,
                cwd=self.icp_project_dir
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to set up dfx identity: {e}")
            return False

    def get_current_principal(self) -> Optional[str]:
        """Get the current principal ID from dfx."""
        try:
            result = subprocess.run(
                [self.dfx_path, "identity", "get-principal"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.icp_project_dir
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    # Admin-specific functions
    def init_admin(self) -> bool:
        """Initialize admin role (can only be called once by deployer)."""
        if self.identity_type != "admin":
            return False
        
        try:
            result = self._call_canister("init_admin")
            return "true" in str(result).lower()
        except Exception:
            return False

    def admin_set_server(self, server_principal: str) -> bool:
        """Set server principal (admin only)."""
        if self.identity_type != "admin":
            return False
        
        try:
            result = self._call_canister("admin_set_server", f'(principal "{server_principal}")')
            return "true" in str(result).lower()
        except Exception:
            return False

    def admin_approve_client(self, client_principal: str) -> bool:
        """Approve a pending client (admin only)."""
        if self.identity_type != "admin":
            return False
        
        try:
            result = self._call_canister("admin_approve_client", f'(principal "{client_principal}")')
            return "true" in str(result).lower()
        except Exception:
            return False

    def admin_reject_client(self, client_principal: str) -> bool:
        """Reject a pending client (admin only)."""
        if self.identity_type != "admin":
            return False
        
        try:
            result = self._call_canister("admin_reject_client", f'(principal "{client_principal}")')
            return "true" in str(result).lower()
        except Exception:
            return False

    def admin_remove_client(self, client_principal: str) -> bool:
        """Remove a client (admin only)."""
        if self.identity_type != "admin":
            return False
        
        try:
            result = self._call_canister("admin_remove_client", f'(principal "{client_principal}")')
            return "true" in str(result).lower()
        except Exception:
            return False

    def get_pending_clients(self) -> List[Client]:
        """Get list of clients pending approval."""
        try:
            result = self._call_canister("get_pending_clients")
            # TODO: Implement proper parsing of client array
            return []  # Simplified for now
        except Exception:
            return []

    def get_admin_principal(self) -> Optional[str]:
        """Get the admin principal ID."""
        try:
            result = self._call_canister("get_admin_principal")
            if result and "principal" in str(result):
                # Extract principal from result
                return str(result).strip()
            return None
        except Exception:
            return None

    # Enhanced registration with pending status
    def register_client_with_metadata(self, client_name: str = None, 
                                    organization: str = None, 
                                    location: str = None, 
                                    contact_email: str = None) -> str:
        """
        Register client with additional metadata.
        
        Returns:
            Status string: "success", "pending", "already_registered", or "error"
        """
        try:
            result = self._call_canister("register_client_enhanced")
            result_str = str(result)
            
            if "Success" in result_str:
                return "success"
            elif "PendingApproval" in result_str:
                return "pending"
            elif "AlreadyRegistered" in result_str:
                return "already_registered"
            else:
                return "error"
        except Exception:
            return "error"


# Convenience functions for different roles
def get_admin_client() -> AuthenticatedICPClient:
    """Get an authenticated admin client."""
    return AuthenticatedICPClient(identity_type="admin")


def get_server_client() -> AuthenticatedICPClient:
    """Get an authenticated server client."""
    return AuthenticatedICPClient(identity_type="server")


def get_client() -> AuthenticatedICPClient:
    """Get an authenticated client."""
    return AuthenticatedICPClient(identity_type="client")


def setup_admin_role() -> bool:
    """Set up the admin role (run once after deployment)."""
    admin_client = get_admin_client()
    return admin_client.init_admin()


def setup_server_role(server_principal: str) -> bool:
    """Set up the server role (admin function)."""
    admin_client = get_admin_client()
    return admin_client.admin_set_server(server_principal)
