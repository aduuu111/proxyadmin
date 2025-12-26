"""
Core Service Adapter - Wrapper for the underlying proxy engine API.
Implements asynchronous communication with the Core Service using httpx.
Based on the OpenAPI specification provided in 默认模块.openapi.json
"""
import httpx
from typing import Optional, List, Dict, Any
from app.config_loader import load_core_config


class CoreConnectionError(Exception):
    """
    Custom exception for Core Service connection failures.
    """
    pass


class CoreAdapter:
    """
    Adapter class for communicating with the Core Service.
    All methods are async and handle errors gracefully.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0
    ):
        """
        Initialize the Core Adapter.

        Args:
            base_url: Base URL of the Core Service (e.g., http://127.0.0.1:8080)
            api_key: Authentication key for the Core Service
            timeout: Request timeout in seconds
        """
        # Load config from file if not provided
        if base_url is None or api_key is None:
            config = load_core_config()
            base_url = base_url or config["api_url"]
            api_key = api_key or config["api_key"]
            timeout = timeout if timeout != 10.0 else config["timeout"]

        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Auth": self.api_key}
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Internal method for making HTTP requests with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body for POST requests
            params: Query parameters for GET requests

        Returns:
            Response JSON data

        Raises:
            CoreConnectionError: If connection fails or response is invalid
        """
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=json,
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.ConnectError as e:
            raise CoreConnectionError(f"Failed to connect to Core Service at {self.base_url}: {str(e)}")
        except httpx.TimeoutException as e:
            raise CoreConnectionError(f"Core Service request timed out: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise CoreConnectionError(f"Core Service returned error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise CoreConnectionError(f"Unexpected error communicating with Core Service: {str(e)}")

    # ===========================
    # System Information Methods
    # ===========================

    async def get_interfaces(self) -> List[Dict[str, str]]:
        """
        Get list of network interfaces from the server.

        Returns:
            List of interfaces with format:
            [{"ehName": "eth0", "eh": "192.168.1.1", "ip": "1.2.3.4"}, ...]

        API: GET /api/system/getInterFaces
        """
        result = await self._request("GET", "/api/system/getInterFaces")
        return result.get("data", [])

    async def get_system_base_info(self, io_option: str = "all", net_option: str = "all") -> Dict[str, Any]:
        """
        Get basic system information.

        Args:
            io_option: IO statistics option
            net_option: Network statistics option

        API: GET /api/system/base/{ioOption}/{netOption}
        """
        return await self._request("GET", f"/api/system/base/{io_option}/{net_option}")

    async def get_system_current_info(self, io_option: str = "all", net_option: str = "all") -> Dict[str, Any]:
        """
        Get real-time system information.

        Args:
            io_option: IO statistics option
            net_option: Network statistics option

        API: GET /api/system/current/{ioOption}/{netOption}
        """
        return await self._request("GET", f"/api/system/current/{io_option}/{net_option}")

    async def restart_service(self, operation: str = "GreenServer") -> Dict[str, Any]:
        """
        Restart the proxy service or system.

        Args:
            operation: "GreenServer" to restart proxy, "system" to restart OS

        API: POST /api/system/restart/{operation}
        """
        return await self._request("POST", f"/api/system/restart/{operation}")

    # ===========================
    # Outbound Management Methods
    # ===========================

    async def create_outbound(self, name: str, eh: str, proxy_url: str = "") -> Dict[str, Any]:
        """
        Create a single outbound proxy configuration.

        Args:
            name: Unique outbound name
            eh: Local interface IP (e.g., "192.168.1.1")
            proxy_url: Optional proxy chain URL (e.g., "socks5://user:pass@ip:port")

        API: POST /api/out/createOutBound
        """
        data = {
            "name": name,
            "eh": eh,
            "proxyUrl": proxy_url
        }
        return await self._request("POST", "/api/out/createOutBound", json=data)

    async def create_outbounds(self, outbounds: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create multiple outbounds in batch.

        Args:
            outbounds: List of outbound configurations
                [{"name": "out1", "eh": "192.168.1.1", "proxyUrl": ""}, ...]

        API: POST /api/out/createOutBounds
        """
        return await self._request("POST", "/api/out/createOutBounds", json=outbounds)

    async def get_all_outbounds(self) -> List[Dict[str, Any]]:
        """
        Get all outbound configurations.

        API: GET /api/out/getOutBoundsAll
        """
        result = await self._request("GET", "/api/out/getOutBoundsAll")
        return result.get("data", [])

    async def edit_outbound(self, name: str, eh: str, proxy_url: str = "") -> Dict[str, Any]:
        """
        Edit an existing outbound configuration.

        Args:
            name: Outbound name to edit
            eh: New local interface IP
            proxy_url: New proxy URL

        API: POST /api/out/editOutBound
        """
        data = {
            "name": name,
            "eh": eh,
            "proxyUrl": proxy_url
        }
        return await self._request("POST", "/api/out/editOutBound", json=data)

    async def delete_outbound(self, name: str) -> Dict[str, Any]:
        """
        Delete an outbound configuration.

        API: GET /api/out/deleteOutBound?name={name}
        """
        return await self._request("GET", "/api/out/deleteOutBound", params={"name": name})

    async def get_outbound_info(self, name: str) -> Dict[str, Any]:
        """
        Get current connection data for an outbound.

        API: GET /api/out/getOutBoundInfo?name={name}
        """
        return await self._request("GET", "/api/out/getOutBoundInfo", params={"name": name})

    # ===========================
    # User Management Methods
    # ===========================

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new proxy user.

        Args:
            user_data: User configuration matching the OpenAPI spec
                Required fields:
                - enable: bool
                - listenAddr: str (e.g., "0.0.0.0:1080")
                - protocol: str (socks5/ss)
                - deleteTime: str (e.g., "2026-01-02 15:04:05")
                - maxSendByte, maxReceiveByte, sendByte, receiveByte: int
                - maxConnCount, sendLimit, receiveLimit: int
                - rule: list[str] (rule names)
                - out: str (outbound name)
                - conf: dict ({"username": "user", "password": "pass"})
                - info: str (additional data)

        API: POST /api/user/createUser
        """
        return await self._request("POST", "/api/user/createUser", json=user_data)

    async def create_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple users in batch.

        API: POST /api/user/createUsers
        """
        return await self._request("POST", "/api/user/createUsers", json=users_data)

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all proxy users.

        API: GET /api/user/getUserAll
        """
        result = await self._request("GET", "/api/user/getUserAll")
        return result.get("data", [])

    async def edit_user(self, listen_addr: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit an existing user.

        Args:
            listen_addr: Current listen address (e.g., "0.0.0.0:1080")
            user_data: New user configuration

        API: POST /api/user/editUser?lAddr={listen_addr}
        """
        return await self._request(
            "POST",
            "/api/user/editUser",
            json=user_data,
            params={"lAddr": listen_addr}
        )

    async def delete_user(self, listen_addr: str) -> Dict[str, Any]:
        """
        Delete a user.

        Args:
            listen_addr: Listen address of user to delete (e.g., "0.0.0.0:1080")

        API: GET /api/user/deleteUser?lAddr={listen_addr}
        """
        return await self._request("GET", "/api/user/deleteUser", params={"lAddr": listen_addr})

    async def get_user_connections(self, listen_addr: str) -> List[Dict[str, Any]]:
        """
        Get connection list for a user.

        API: GET /api/user/getUserConnList?lAddr={listen_addr}
        """
        result = await self._request("GET", "/api/user/getUserConnList", params={"lAddr": listen_addr})
        return result.get("data", [])

    async def edit_user_delete_time(self, listen_addr: str, delete_time: str) -> Dict[str, Any]:
        """
        Modify user expiration time.

        Args:
            listen_addr: User's listen address
            delete_time: New expiration time (e.g., "2026-01-02 15:04:05")

        API: GET /api/user/EditUserDeleteTime?lAddr={listen_addr}&deleteTime={delete_time}
        """
        return await self._request(
            "GET",
            "/api/user/EditUserDeleteTime",
            params={"lAddr": listen_addr, "deleteTime": delete_time}
        )

    # ===========================
    # Rule Management Methods
    # ===========================

    async def add_rule(self, name: str, data: str) -> Dict[str, Any]:
        """
        Add a traffic rule.

        Args:
            name: Rule name
            data: Rule content (e.g., "* = allow")

        API: POST /api/rule/addRule
        """
        return await self._request("POST", "/api/rule/addRule", json={"name": name, "data": data})

    async def add_rules(self, rules: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Add multiple rules in batch.

        Args:
            rules: List of rules [{"name": "rule1", "data": "* = allow"}, ...]

        API: POST /api/rule/addRules
        """
        return await self._request("POST", "/api/rule/addRules", json=rules)

    async def get_all_rules(self) -> List[Dict[str, Any]]:
        """
        Get all rules.

        API: GET /api/rule/getRuleAll
        """
        result = await self._request("GET", "/api/rule/getRuleAll")
        return result.get("data", [])

    async def edit_rule(self, name: str, data: str) -> Dict[str, Any]:
        """
        Edit a rule.

        API: POST /api/rule/editRule
        """
        return await self._request("POST", "/api/rule/editRule", json={"name": name, "data": data})

    async def delete_rule(self, name: str) -> Dict[str, Any]:
        """
        Delete a rule.

        API: GET /api/rule/delRule?name={name}
        """
        return await self._request("GET", "/api/rule/delRule", params={"name": name})

    async def delete_all_rules(self) -> Dict[str, Any]:
        """
        Delete all rules.

        API: GET /api/rule/deleteRuleAll
        """
        return await self._request("GET", "/api/rule/deleteRuleAll")

    # ===========================
    # High-Level Sync Methods
    # ===========================

    async def sync_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart sync: Determine if user exists in Core and call create or edit accordingly.

        This is a high-level method that checks if a user exists by listening address,
        then calls create_user or edit_user appropriately.

        Args:
            user_data: Complete user configuration

        Returns:
            Result from create_user or edit_user
        """
        listen_addr = user_data.get("listenAddr")

        try:
            # Check if user exists by getting all users and searching
            existing_users = await self.get_all_users()
            if existing_users is None:
                existing_users = []
            user_exists = any(u.get("listenAddr") == listen_addr for u in existing_users)

            if user_exists:
                # User exists - update it
                return await self.edit_user(listen_addr, user_data)
            else:
                # User doesn't exist - create it
                return await self.create_user(user_data)

        except CoreConnectionError as e:
            # If we can't determine, try to create (will fail if exists)
            raise e
