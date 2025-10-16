from typing import Dict, Any, List


class Connector:
    """
    Display-only connector interface for MVP. Each connector should
    implement metadata and a simulated test() method.
    """

    id: str = ""
    name: str = ""
    provider: str = ""
    capabilities: List[str] = []

    def metadata(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "capabilities": self.capabilities,
            "comingSoon": self.id != "csv_upload",
        }

    def test(self) -> Dict[str, Any]:
        status = "ok" if self.id == "csv_upload" else "coming_soon"
        return {"connector": self.id, "status": status}


class CsvUploadConnector(Connector):
    id = "csv_upload"
    name = "CSV Upload"
    provider = "Local Files"
    capabilities = ["one_time_import"]


class ZohoCrmConnector(Connector):
    id = "zoho_crm"
    name = "Zoho CRM"
    provider = "Zoho"
    capabilities = ["schedule", "webhook"]


class SupabaseConnector(Connector):
    id = "supabase"
    name = "Supabase / Postgres"
    provider = "Supabase"
    capabilities = ["query", "schedule"]


class HubSpotConnector(Connector):
    id = "hubspot"
    name = "HubSpot"
    provider = "HubSpot"
    capabilities = ["schedule", "webhook"]


class SalesforceConnector(Connector):
    id = "salesforce"
    name = "Salesforce"
    provider = "Salesforce"
    capabilities = ["schedule", "webhook"]


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: Dict[str, Connector] = {}
        self.register(CsvUploadConnector())
        self.register(ZohoCrmConnector())
        self.register(SupabaseConnector())
        self.register(HubSpotConnector())
        self.register(SalesforceConnector())

    def register(self, connector: Connector) -> None:
        self._connectors[connector.id] = connector

    def list(self) -> List[Dict[str, Any]]:
        return [c.metadata() for c in self._connectors.values()]

    def test(self, connector_id: str) -> Dict[str, Any]:
        connector = self._connectors.get(connector_id)
        if not connector:
            return {"error": "connector_not_found"}
        return connector.test()


