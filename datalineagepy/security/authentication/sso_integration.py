"""
Single Sign-On (SSO) Integration
Supports SAML, OAuth2, and LDAP authentication for enterprise environments.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any, List
import base64
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timedelta
import ldap3
from ldap3 import Server, Connection, ALL
import json


class SAMLProvider:
    """
    SAML 2.0 Service Provider implementation.
    
    Supports enterprise SAML identity providers like:
    - Active Directory Federation Services (ADFS)
    - Okta
    - Azure AD
    - Google Workspace
    """
    
    def __init__(self, config: Dict[str, str]):
        self.entity_id = config["entity_id"]
        self.acs_url = config["acs_url"]  # Assertion Consumer Service URL
        self.sso_url = config["sso_url"]  # Identity Provider SSO URL
        self.x509_cert = config.get("x509_cert")  # IdP certificate for verification
        self.private_key = config.get("private_key")  # SP private key
        self.name_id_format = config.get("name_id_format", "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress")
    
    def generate_auth_request(self, relay_state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate SAML authentication request.
        
        Args:
            relay_state: Optional state to maintain across the authentication flow
            
        Returns:
            Dict containing auth_url and request_id
        """
        request_id = f"_{secrets.token_hex(16)}"
        issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Build SAML AuthnRequest XML
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{issue_instant}"
                    Destination="{self.sso_url}"
                    AssertionConsumerServiceURL="{self.acs_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.entity_id}</saml:Issuer>
    <samlp:NameIDPolicy Format="{self.name_id_format}" AllowCreate="true"/>
</samlp:AuthnRequest>"""
        
        # Encode the request
        encoded_request = base64.b64encode(authn_request.encode()).decode()
        
        # Build authentication URL
        params = {
            "SAMLRequest": encoded_request
        }
        
        if relay_state:
            params["RelayState"] = relay_state
        
        auth_url = f"{self.sso_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "request_id": request_id
        }
    
    def process_saml_response(self, saml_response: str, relay_state: Optional[str] = None) -> Dict[str, Any]:
        """
        Process SAML response from Identity Provider.
        
        Args:
            saml_response: Base64 encoded SAML response
            relay_state: Optional relay state
            
        Returns:
            User information extracted from SAML assertion
        """
        try:
            # Decode SAML response
            decoded_response = base64.b64decode(saml_response).decode()
            
            # Parse XML
            root = ET.fromstring(decoded_response)
            
            # Extract user attributes
            user_info = self._extract_user_attributes(root)
            
            # Validate assertion (in production, verify signature)
            if self._validate_assertion(root):
                return {
                    "success": True,
                    "user": user_info,
                    "relay_state": relay_state
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid SAML assertion"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"SAML processing error: {str(e)}"
            }
    
    def _extract_user_attributes(self, root: ET.Element) -> Dict[str, Any]:
        """Extract user attributes from SAML assertion."""
        user_info = {}
        
        # Define namespace mappings
        namespaces = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol'
        }
        
        # Extract NameID (usually email)
        name_id = root.find('.//saml:NameID', namespaces)
        if name_id is not None:
            user_info['email'] = name_id.text
            user_info['name_id'] = name_id.text
        
        # Extract attributes
        attributes = root.findall('.//saml:Attribute', namespaces)
        for attr in attributes:
            attr_name = attr.get('Name')
            attr_values = [val.text for val in attr.findall('saml:AttributeValue', namespaces)]
            
            # Map common SAML attributes
            if 'email' in attr_name.lower():
                user_info['email'] = attr_values[0] if attr_values else None
            elif 'firstname' in attr_name.lower() or 'givenname' in attr_name.lower():
                user_info['first_name'] = attr_values[0] if attr_values else None
            elif 'lastname' in attr_name.lower() or 'surname' in attr_name.lower():
                user_info['last_name'] = attr_values[0] if attr_values else None
            elif 'displayname' in attr_name.lower():
                user_info['display_name'] = attr_values[0] if attr_values else None
            elif 'role' in attr_name.lower() or 'group' in attr_name.lower():
                user_info['roles'] = attr_values
        
        return user_info
    
    def _validate_assertion(self, root: ET.Element) -> bool:
        """Validate SAML assertion (simplified version)."""
        # In production, verify:
        # 1. Digital signature
        # 2. Assertion expiration
        # 3. Audience restriction
        # 4. Issuer validation
        return True  # Simplified for demo


class OAuth2Provider:
    """
    OAuth2 authentication provider.
    
    Supports providers like:
    - Google
    - Microsoft Azure AD
    - GitHub
    - Custom OAuth2 providers
    """
    
    def __init__(self, config: Dict[str, str]):
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.auth_url = config["auth_url"]
        self.token_url = config["token_url"]
        self.user_info_url = config["user_info_url"]
        self.redirect_uri = config["redirect_uri"]
        self.scope = config.get("scope", "openid email profile")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth2 authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scope
        }
        
        if state:
            params["state"] = state
        
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"
    
    def exchange_code_for_token(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth2 provider
            state: State parameter for validation
            
        Returns:
            Token response or error
        """
        try:
            token_data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            response = requests.post(self.token_url, data=token_data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            return {"error": f"Token exchange failed: {str(e)}"}
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            access_token: OAuth2 access token
            
        Returns:
            User information or error
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(self.user_info_url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            return {"error": f"User info request failed: {str(e)}"}


class LDAPProvider:
    """
    LDAP/Active Directory authentication provider.
    
    Supports:
    - Active Directory
    - OpenLDAP
    - Other LDAP-compatible directories
    """
    
    def __init__(self, config: Dict[str, str]):
        self.server_uri = config["server_uri"]
        self.bind_dn = config.get("bind_dn")
        self.bind_password = config.get("bind_password")
        self.user_search_base = config["user_search_base"]
        self.user_search_filter = config.get("user_search_filter", "(sAMAccountName={username})")
        self.group_search_base = config.get("group_search_base")
        self.use_ssl = config.get("use_ssl", True)
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user against LDAP directory.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication result with user information
        """
        try:
            # Create server connection
            server = Server(self.server_uri, use_ssl=self.use_ssl, get_info=ALL)
            
            # First, bind with service account to search for user
            if self.bind_dn:
                conn = Connection(server, self.bind_dn, self.bind_password, auto_bind=True)
            else:
                conn = Connection(server, auto_bind=True)
            
            # Search for user
            search_filter = self.user_search_filter.format(username=username)
            conn.search(self.user_search_base, search_filter, attributes=['*'])
            
            if not conn.entries:
                return {"success": False, "error": "User not found"}
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # Close service account connection
            conn.unbind()
            
            # Authenticate with user credentials
            user_conn = Connection(server, user_dn, password)
            if not user_conn.bind():
                return {"success": False, "error": "Invalid credentials"}
            
            # Extract user attributes
            user_info = self._extract_ldap_attributes(user_entry)
            
            # Get user groups
            user_info['groups'] = self._get_user_groups(server, user_dn)
            
            user_conn.unbind()
            
            return {
                "success": True,
                "user": user_info
            }
            
        except Exception as e:
            return {"success": False, "error": f"LDAP authentication failed: {str(e)}"}
    
    def _extract_ldap_attributes(self, user_entry) -> Dict[str, Any]:
        """Extract user attributes from LDAP entry."""
        user_info = {}
        
        # Common LDAP attribute mappings
        attr_mapping = {
            'sAMAccountName': 'username',
            'userPrincipalName': 'email',
            'mail': 'email',
            'givenName': 'first_name',
            'sn': 'last_name',
            'displayName': 'display_name',
            'title': 'job_title',
            'department': 'department',
            'company': 'company'
        }
        
        for ldap_attr, user_attr in attr_mapping.items():
            if hasattr(user_entry, ldap_attr):
                value = getattr(user_entry, ldap_attr).value
                if value:
                    user_info[user_attr] = value
        
        return user_info
    
    def _get_user_groups(self, server, user_dn: str) -> List[str]:
        """Get groups for user."""
        if not self.group_search_base:
            return []
        
        try:
            conn = Connection(server, self.bind_dn, self.bind_password, auto_bind=True)
            
            # Search for groups containing the user
            search_filter = f"(member={user_dn})"
            conn.search(self.group_search_base, search_filter, attributes=['cn'])
            
            groups = [entry.cn.value for entry in conn.entries if hasattr(entry, 'cn')]
            conn.unbind()
            
            return groups
            
        except Exception:
            return []


class SSOManager:
    """
    Unified SSO manager that coordinates different authentication providers.
    """
    
    def __init__(self):
        self.providers = {}
    
    def register_saml_provider(self, name: str, config: Dict[str, str]):
        """Register SAML provider."""
        self.providers[name] = SAMLProvider(config)
    
    def register_oauth2_provider(self, name: str, config: Dict[str, str]):
        """Register OAuth2 provider."""
        self.providers[name] = OAuth2Provider(config)
    
    def register_ldap_provider(self, name: str, config: Dict[str, str]):
        """Register LDAP provider."""
        self.providers[name] = LDAPProvider(config)
    
    def get_provider(self, name: str):
        """Get authentication provider by name."""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List available authentication providers."""
        return list(self.providers.keys())


# Example usage
if __name__ == "__main__":
    # Initialize SSO manager
    sso_manager = SSOManager()
    
    # Register SAML provider (e.g., Azure AD)
    saml_config = {
        "entity_id": "https://your-app.com/saml/metadata",
        "acs_url": "https://your-app.com/saml/acs",
        "sso_url": "https://login.microsoftonline.com/tenant-id/saml2",
        "x509_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
    }
    sso_manager.register_saml_provider("azure_ad", saml_config)
    
    # Register OAuth2 provider (e.g., Google)
    oauth2_config = {
        "client_id": "your-google-client-id",
        "client_secret": "your-google-client-secret",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "redirect_uri": "https://your-app.com/oauth2/callback"
    }
    sso_manager.register_oauth2_provider("google", oauth2_config)
    
    # Register LDAP provider
    ldap_config = {
        "server_uri": "ldaps://your-domain-controller.com:636",
        "bind_dn": "CN=service-account,OU=Service Accounts,DC=company,DC=com",
        "bind_password": "service-account-password",
        "user_search_base": "OU=Users,DC=company,DC=com",
        "user_search_filter": "(sAMAccountName={username})",
        "group_search_base": "OU=Groups,DC=company,DC=com"
    }
    sso_manager.register_ldap_provider("company_ad", ldap_config)
    
    print("Available SSO providers:", sso_manager.list_providers())
