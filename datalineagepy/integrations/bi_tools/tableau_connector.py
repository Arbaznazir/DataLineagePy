"""
Tableau connector for DataLineagePy enterprise integrations.
"""

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from urllib.parse import urljoin

from ..core.base_connector import BaseConnector, ConnectorConfig, ConnectorType, ConnectionStatus

logger = logging.getLogger(__name__)


@dataclass
class TableauConfig(ConnectorConfig):
    """Tableau-specific configuration."""
    server_url: str = None
    site_id: str = 'default'  # Site ID or content URL
    api_version: str = '3.19'  # Tableau Server API version
    personal_access_token_name: str = None
    personal_access_token_secret: str = None
    trusted_ticket: str = None
    use_server_version: bool = True
    page_size: int = 100
    request_timeout: int = 30
    
    def __post_init__(self):
        """Validate Tableau configuration."""
        super().__post_init__()
        
        if not self.server_url:
            raise ValueError("Tableau server URL is required")
        
        # Validate authentication method
        has_username_password = self.username and self.password
        has_pat = self.personal_access_token_name and self.personal_access_token_secret
        has_trusted_ticket = self.trusted_ticket
        
        if not (has_username_password or has_pat or has_trusted_ticket):
            raise ValueError("Authentication required: username/password, PAT, or trusted ticket")
        
        # Set connector type
        self.connector_type = ConnectorType.BI_TOOL
        
        # Build base API URL
        if not self.connection_string:
            self.connection_string = self._build_api_url()
    
    def _build_api_url(self) -> str:
        """Build Tableau Server API base URL."""
        base_url = self.server_url.rstrip('/')
        return f"{base_url}/api/{self.api_version}"


class TableauConnector(BaseConnector):
    """Tableau connector for BI lineage extraction."""
    
    def __init__(self, config: TableauConfig):
        """Initialize Tableau connector."""
        super().__init__(config)
        self.tableau_config = config
        self._session = None
        self._auth_token = None
        self._site_id = None
        self._user_id = None
        
        # Tableau-specific attributes
        self.server_info = None
        self.site_info = None
        
        self.logger.info(f"Initialized Tableau connector for server: {config.server_url}")
    
    async def connect(self) -> bool:
        """Connect to Tableau Server."""
        try:
            self._update_status(ConnectionStatus.CONNECTING)
            
            # Import required libraries
            try:
                import requests
                import aiohttp
            except ImportError:
                raise ImportError("requests and aiohttp are required for Tableau integration")
            
            # Create HTTP session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.tableau_config.request_timeout)
            )
            
            # Authenticate
            if await self._authenticate():
                # Get server info
                await self._get_server_info()
                
                # Get site info
                await self._get_site_info()
                
                self._update_status(ConnectionStatus.CONNECTED)
                self.logger.info(f"Connected to Tableau Server: {self.tableau_config.server_url}")
                return True
            else:
                self._update_status(ConnectionStatus.ERROR)
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Tableau Server: {e}")
            self._update_status(ConnectionStatus.ERROR)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Tableau Server."""
        try:
            # Sign out if authenticated
            if self._auth_token:
                await self._sign_out()
            
            # Close HTTP session
            if self._session:
                await self._session.close()
                self._session = None
            
            self._auth_token = None
            self._site_id = None
            self._user_id = None
            
            self._update_status(ConnectionStatus.DISCONNECTED)
            self.logger.info("Disconnected from Tableau Server")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Tableau Server: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Tableau Server connection."""
        try:
            if not self._auth_token:
                return False
            
            # Test with a simple API call
            url = f"{self.tableau_config.connection_string}/sites/{self._site_id}/serverinfo"
            headers = {'X-Tableau-Auth': self._auth_token}
            
            async with self._session.get(url, headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute API request against Tableau Server."""
        if not self._auth_token:
            raise RuntimeError("Not authenticated to Tableau Server")
        
        start_time = time.time()
        
        try:
            # Build URL
            if query.startswith('http'):
                url = query
            else:
                url = f"{self.tableau_config.connection_string}{query}"
            
            # Add site context if needed
            if '/sites/' not in url and self._site_id:
                url = url.replace('/api/', f'/api/{self.tableau_config.api_version}/sites/{self._site_id}/')
            
            # Prepare headers
            headers = {'X-Tableau-Auth': self._auth_token}
            if parameters and 'headers' in parameters:
                headers.update(parameters['headers'])
            
            # Make request
            method = parameters.get('method', 'GET') if parameters else 'GET'
            data = parameters.get('data') if parameters else None
            
            async with self._session.request(method, url, headers=headers, data=data) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/xml' in content_type:
                        text = await response.text()
                        result = ET.fromstring(text)
                    elif 'application/json' in content_type:
                        result = await response.json()
                    else:
                        result = await response.text()
                    
                    self._log_query(query, True, response_time)
                    return result
                else:
                    error_text = await response.text()
                    self._log_query(query, False, response_time, f"HTTP {response.status}: {error_text}")
                    raise Exception(f"API request failed: HTTP {response.status}")
            
        except Exception as e:
            response_time = time.time() - start_time
            self._log_query(query, False, response_time, str(e))
            raise
    
    async def get_metadata(self) -> Dict[str, Any]:
        """Extract metadata from Tableau Server."""
        try:
            metadata = {
                'server_info': self.server_info,
                'site_info': self.site_info,
                'workbooks': await self._get_workbooks(),
                'datasources': await self._get_datasources(),
                'projects': await self._get_projects(),
                'users': await self._get_users(),
                'groups': await self._get_groups(),
                'schedules': await self._get_schedules(),
                'flows': await self._get_flows(),
                'metrics': await self._get_metrics()
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}
    
    async def get_lineage(self, entity_id: str) -> Dict[str, Any]:
        """Extract lineage information for a Tableau entity."""
        try:
            # Parse entity ID (format: type:id or just id)
            if ':' in entity_id:
                entity_type, entity_id = entity_id.split(':', 1)
            else:
                entity_type = 'workbook'  # Default to workbook
            
            lineage = {
                'entity_id': entity_id,
                'entity_type': entity_type,
                'upstream_dependencies': [],
                'downstream_dependencies': [],
                'field_lineage': [],
                'usage_statistics': {}
            }
            
            if entity_type == 'workbook':
                lineage.update(await self._get_workbook_lineage(entity_id))
            elif entity_type == 'datasource':
                lineage.update(await self._get_datasource_lineage(entity_id))
            elif entity_type == 'flow':
                lineage.update(await self._get_flow_lineage(entity_id))
            
            return lineage
            
        except Exception as e:
            self.logger.error(f"Failed to extract lineage for {entity_id}: {e}")
            return {}
    
    async def _authenticate(self) -> bool:
        """Authenticate with Tableau Server."""
        try:
            auth_url = f"{self.tableau_config.connection_string}/auth/signin"
            
            # Build authentication request
            if self.tableau_config.personal_access_token_name:
                # Personal Access Token authentication
                credentials = ET.Element('credentials')
                credentials.set('personalAccessTokenName', self.tableau_config.personal_access_token_name)
                credentials.set('personalAccessTokenSecret', self.tableau_config.personal_access_token_secret)
                
                site = ET.SubElement(credentials, 'site')
                site.set('contentUrl', self.tableau_config.site_id)
                
            elif self.tableau_config.trusted_ticket:
                # Trusted ticket authentication
                credentials = ET.Element('credentials')
                credentials.set('token', self.tableau_config.trusted_ticket)
                
                site = ET.SubElement(credentials, 'site')
                site.set('contentUrl', self.tableau_config.site_id)
                
            else:
                # Username/password authentication
                credentials = ET.Element('credentials')
                credentials.set('name', self.tableau_config.username)
                credentials.set('password', self.tableau_config.password)
                
                site = ET.SubElement(credentials, 'site')
                site.set('contentUrl', self.tableau_config.site_id)
            
            # Create request XML
            tsRequest = ET.Element('tsRequest')
            tsRequest.append(credentials)
            
            xml_request = ET.tostring(tsRequest, encoding='unicode')
            
            # Make authentication request
            headers = {'Content-Type': 'application/xml'}
            
            async with self._session.post(auth_url, data=xml_request, headers=headers) as response:
                if response.status == 200:
                    response_xml = ET.fromstring(await response.text())
                    
                    # Extract authentication token
                    credentials_elem = response_xml.find('.//credentials')
                    if credentials_elem is not None:
                        self._auth_token = credentials_elem.get('token')
                        
                        # Extract site ID
                        site_elem = credentials_elem.find('site')
                        if site_elem is not None:
                            self._site_id = site_elem.get('id')
                        
                        # Extract user ID
                        user_elem = credentials_elem.find('user')
                        if user_elem is not None:
                            self._user_id = user_elem.get('id')
                        
                        return True
                
                error_text = await response.text()
                self.logger.error(f"Authentication failed: {error_text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    async def _sign_out(self):
        """Sign out from Tableau Server."""
        try:
            if self._auth_token:
                signout_url = f"{self.tableau_config.connection_string}/auth/signout"
                headers = {'X-Tableau-Auth': self._auth_token}
                
                async with self._session.post(signout_url, headers=headers) as response:
                    if response.status == 200:
                        self.logger.debug("Successfully signed out from Tableau Server")
                    
        except Exception as e:
            self.logger.warning(f"Error during sign out: {e}")
    
    async def _get_server_info(self):
        """Get Tableau Server information."""
        try:
            result = await self.execute_query('/serverinfo')
            if hasattr(result, 'find'):
                server_info_elem = result.find('.//serverInfo')
                if server_info_elem is not None:
                    self.server_info = {
                        'product_version': server_info_elem.get('productVersion'),
                        'build_number': server_info_elem.get('buildNumber'),
                        'schema_version': server_info_elem.get('schemaVersion')
                    }
        except Exception as e:
            self.logger.warning(f"Failed to get server info: {e}")
    
    async def _get_site_info(self):
        """Get current site information."""
        try:
            result = await self.execute_query(f'/sites/{self._site_id}')
            if hasattr(result, 'find'):
                site_elem = result.find('.//site')
                if site_elem is not None:
                    self.site_info = {
                        'id': site_elem.get('id'),
                        'name': site_elem.get('name'),
                        'content_url': site_elem.get('contentUrl'),
                        'admin_mode': site_elem.get('adminMode'),
                        'state': site_elem.get('state')
                    }
        except Exception as e:
            self.logger.warning(f"Failed to get site info: {e}")
    
    async def _get_workbooks(self) -> List[Dict[str, Any]]:
        """Get list of workbooks."""
        try:
            result = await self.execute_query('/workbooks')
            workbooks = []
            
            if hasattr(result, 'findall'):
                for workbook_elem in result.findall('.//workbook'):
                    workbook = {
                        'id': workbook_elem.get('id'),
                        'name': workbook_elem.get('name'),
                        'content_url': workbook_elem.get('contentUrl'),
                        'show_tabs': workbook_elem.get('showTabs'),
                        'size': workbook_elem.get('size'),
                        'created_at': workbook_elem.get('createdAt'),
                        'updated_at': workbook_elem.get('updatedAt')
                    }
                    
                    # Get project info
                    project_elem = workbook_elem.find('project')
                    if project_elem is not None:
                        workbook['project'] = {
                            'id': project_elem.get('id'),
                            'name': project_elem.get('name')
                        }
                    
                    # Get owner info
                    owner_elem = workbook_elem.find('owner')
                    if owner_elem is not None:
                        workbook['owner'] = {
                            'id': owner_elem.get('id'),
                            'name': owner_elem.get('name')
                        }
                    
                    workbooks.append(workbook)
            
            return workbooks
            
        except Exception as e:
            self.logger.error(f"Failed to get workbooks: {e}")
            return []
    
    async def _get_datasources(self) -> List[Dict[str, Any]]:
        """Get list of datasources."""
        try:
            result = await self.execute_query('/datasources')
            datasources = []
            
            if hasattr(result, 'findall'):
                for datasource_elem in result.findall('.//datasource'):
                    datasource = {
                        'id': datasource_elem.get('id'),
                        'name': datasource_elem.get('name'),
                        'content_url': datasource_elem.get('contentUrl'),
                        'type': datasource_elem.get('type'),
                        'created_at': datasource_elem.get('createdAt'),
                        'updated_at': datasource_elem.get('updatedAt')
                    }
                    
                    # Get project info
                    project_elem = datasource_elem.find('project')
                    if project_elem is not None:
                        datasource['project'] = {
                            'id': project_elem.get('id'),
                            'name': project_elem.get('name')
                        }
                    
                    # Get owner info
                    owner_elem = datasource_elem.find('owner')
                    if owner_elem is not None:
                        datasource['owner'] = {
                            'id': owner_elem.get('id'),
                            'name': owner_elem.get('name')
                        }
                    
                    datasources.append(datasource)
            
            return datasources
            
        except Exception as e:
            self.logger.error(f"Failed to get datasources: {e}")
            return []
    
    async def _get_projects(self) -> List[Dict[str, Any]]:
        """Get list of projects."""
        try:
            result = await self.execute_query('/projects')
            projects = []
            
            if hasattr(result, 'findall'):
                for project_elem in result.findall('.//project'):
                    project = {
                        'id': project_elem.get('id'),
                        'name': project_elem.get('name'),
                        'description': project_elem.get('description'),
                        'content_permissions': project_elem.get('contentPermissions'),
                        'parent_project_id': project_elem.get('parentProjectId')
                    }
                    projects.append(project)
            
            return projects
            
        except Exception as e:
            self.logger.error(f"Failed to get projects: {e}")
            return []
    
    async def _get_users(self) -> List[Dict[str, Any]]:
        """Get list of users."""
        try:
            result = await self.execute_query('/users')
            users = []
            
            if hasattr(result, 'findall'):
                for user_elem in result.findall('.//user'):
                    user = {
                        'id': user_elem.get('id'),
                        'name': user_elem.get('name'),
                        'site_role': user_elem.get('siteRole'),
                        'locale': user_elem.get('locale'),
                        'language': user_elem.get('language')
                    }
                    users.append(user)
            
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to get users: {e}")
            return []
    
    async def _get_groups(self) -> List[Dict[str, Any]]:
        """Get list of groups."""
        try:
            result = await self.execute_query('/groups')
            groups = []
            
            if hasattr(result, 'findall'):
                for group_elem in result.findall('.//group'):
                    group = {
                        'id': group_elem.get('id'),
                        'name': group_elem.get('name'),
                        'domain_name': group_elem.get('domainName'),
                        'minimum_site_role': group_elem.get('minimumSiteRole')
                    }
                    groups.append(group)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Failed to get groups: {e}")
            return []
    
    async def _get_schedules(self) -> List[Dict[str, Any]]:
        """Get list of schedules."""
        try:
            result = await self.execute_query('/schedules')
            schedules = []
            
            if hasattr(result, 'findall'):
                for schedule_elem in result.findall('.//schedule'):
                    schedule = {
                        'id': schedule_elem.get('id'),
                        'name': schedule_elem.get('name'),
                        'state': schedule_elem.get('state'),
                        'priority': schedule_elem.get('priority'),
                        'created_at': schedule_elem.get('createdAt'),
                        'updated_at': schedule_elem.get('updatedAt'),
                        'type': schedule_elem.get('type'),
                        'frequency': schedule_elem.get('frequency')
                    }
                    schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            self.logger.error(f"Failed to get schedules: {e}")
            return []
    
    async def _get_flows(self) -> List[Dict[str, Any]]:
        """Get list of flows (Tableau Prep)."""
        try:
            result = await self.execute_query('/flows')
            flows = []
            
            if hasattr(result, 'findall'):
                for flow_elem in result.findall('.//flow'):
                    flow = {
                        'id': flow_elem.get('id'),
                        'name': flow_elem.get('name'),
                        'description': flow_elem.get('description'),
                        'created_at': flow_elem.get('createdAt'),
                        'updated_at': flow_elem.get('updatedAt')
                    }
                    
                    # Get project info
                    project_elem = flow_elem.find('project')
                    if project_elem is not None:
                        flow['project'] = {
                            'id': project_elem.get('id'),
                            'name': project_elem.get('name')
                        }
                    
                    flows.append(flow)
            
            return flows
            
        except Exception as e:
            self.logger.error(f"Failed to get flows: {e}")
            return []
    
    async def _get_metrics(self) -> List[Dict[str, Any]]:
        """Get list of metrics."""
        try:
            result = await self.execute_query('/metrics')
            metrics = []
            
            if hasattr(result, 'findall'):
                for metric_elem in result.findall('.//metric'):
                    metric = {
                        'id': metric_elem.get('id'),
                        'name': metric_elem.get('name'),
                        'description': metric_elem.get('description'),
                        'created_at': metric_elem.get('createdAt'),
                        'updated_at': metric_elem.get('updatedAt')
                    }
                    
                    # Get project info
                    project_elem = metric_elem.find('project')
                    if project_elem is not None:
                        metric['project'] = {
                            'id': project_elem.get('id'),
                            'name': project_elem.get('name')
                        }
                    
                    metrics.append(metric)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get metrics: {e}")
            return []
    
    async def _get_workbook_lineage(self, workbook_id: str) -> Dict[str, Any]:
        """Get lineage for a specific workbook."""
        try:
            # Get workbook connections
            connections_result = await self.execute_query(f'/workbooks/{workbook_id}/connections')
            
            upstream_dependencies = []
            if hasattr(connections_result, 'findall'):
                for connection_elem in connections_result.findall('.//connection'):
                    connection = {
                        'id': connection_elem.get('id'),
                        'type': connection_elem.get('type'),
                        'server_address': connection_elem.get('serverAddress'),
                        'server_port': connection_elem.get('serverPort'),
                        'username': connection_elem.get('userName'),
                        'embed_password': connection_elem.get('embedPassword')
                    }
                    upstream_dependencies.append(connection)
            
            # Get workbook views for downstream analysis
            views_result = await self.execute_query(f'/workbooks/{workbook_id}/views')
            
            downstream_dependencies = []
            if hasattr(views_result, 'findall'):
                for view_elem in views_result.findall('.//view'):
                    view = {
                        'id': view_elem.get('id'),
                        'name': view_elem.get('name'),
                        'content_url': view_elem.get('contentUrl'),
                        'created_at': view_elem.get('createdAt'),
                        'updated_at': view_elem.get('updatedAt')
                    }
                    downstream_dependencies.append(view)
            
            return {
                'upstream_dependencies': upstream_dependencies,
                'downstream_dependencies': downstream_dependencies
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get workbook lineage: {e}")
            return {'upstream_dependencies': [], 'downstream_dependencies': []}
    
    async def _get_datasource_lineage(self, datasource_id: str) -> Dict[str, Any]:
        """Get lineage for a specific datasource."""
        try:
            # Get datasource connections
            connections_result = await self.execute_query(f'/datasources/{datasource_id}/connections')
            
            upstream_dependencies = []
            if hasattr(connections_result, 'findall'):
                for connection_elem in connections_result.findall('.//connection'):
                    connection = {
                        'id': connection_elem.get('id'),
                        'type': connection_elem.get('type'),
                        'server_address': connection_elem.get('serverAddress'),
                        'server_port': connection_elem.get('serverPort'),
                        'username': connection_elem.get('userName')
                    }
                    upstream_dependencies.append(connection)
            
            return {
                'upstream_dependencies': upstream_dependencies,
                'downstream_dependencies': []  # Would need to query workbooks using this datasource
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get datasource lineage: {e}")
            return {'upstream_dependencies': [], 'downstream_dependencies': []}
    
    async def _get_flow_lineage(self, flow_id: str) -> Dict[str, Any]:
        """Get lineage for a specific flow."""
        try:
            # Get flow connections
            connections_result = await self.execute_query(f'/flows/{flow_id}/connections')
            
            upstream_dependencies = []
            if hasattr(connections_result, 'findall'):
                for connection_elem in connections_result.findall('.//connection'):
                    connection = {
                        'id': connection_elem.get('id'),
                        'type': connection_elem.get('type'),
                        'server_address': connection_elem.get('serverAddress'),
                        'server_port': connection_elem.get('serverPort')
                    }
                    upstream_dependencies.append(connection)
            
            return {
                'upstream_dependencies': upstream_dependencies,
                'downstream_dependencies': []
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get flow lineage: {e}")
            return {'upstream_dependencies': [], 'downstream_dependencies': []}
