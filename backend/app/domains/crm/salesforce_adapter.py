"""Salesforce CRM adapter - Production integration."""

from typing import Optional, Dict, Any, List
import logging
import httpx
from app.domains.crm.crm_adapter import CRMAdapter, CRMLead, CRMType

logger = logging.getLogger(__name__)


class SalesforceAdapter(CRMAdapter):
    """Production Salesforce adapter using REST API."""

    crm_type = CRMType.SALESFORCE

    def __init__(
        self,
        instance_url: str,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
    ):
        """
        Initialize Salesforce adapter.

        Args:
            instance_url: Salesforce instance URL (e.g., https://myinstance.salesforce.com)
            client_id: OAuth client ID
            client_secret: OAuth client secret
            username: Salesforce username
            password: Salesforce password
        """
        self.instance_url = instance_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.access_token = None
        self.token_expiry = None

    async def _get_access_token(self) -> str:
        """Authenticate and get OAuth access token."""
        if self.access_token:
            return self.access_token

        auth_url = f"{self.instance_url}/services/oauth2/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(auth_url, data=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]

        logger.info("Salesforce OAuth authentication successful")
        return self.access_token

    async def _api_call(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API call to Salesforce."""
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{self.instance_url}/services/data/v57.0{endpoint}"

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

    async def fetch_lead(self, lead_id: str) -> Optional[CRMLead]:
        """Fetch single lead from Salesforce."""
        try:
            # Query lead by ID
            endpoint = f"/sobjects/Lead/{lead_id}"
            result = await self._api_call("GET", endpoint)

            return CRMLead(
                id=result["Id"],
                company_name=result.get("Company", ""),
                contact_name=f"{result.get('FirstName', '')} {result.get('LastName', '')}".strip(),
                email=result.get("Email", ""),
                phone=result.get("Phone"),
                industry=result.get("Industry"),
                lead_score=result.get("LeadScore__c"),  # Custom field
                source=result.get("LeadSource"),
                stage=result.get("Status"),
                estimated_value=result.get("Amount__c"),
                budget=result.get("Budget__c"),
                custom_fields={k: v for k, v in result.items() if k.endswith("__c")},
            )

        except Exception as e:
            logger.error(f"Salesforce fetch_lead failed: {lead_id} - {e}")
            return None

    async def fetch_leads(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[CRMLead]:
        """Fetch multiple leads from Salesforce with optional filtering."""
        try:
            # Build SOQL query
            where_clauses = []
            if filters:
                if "min_lead_score" in filters:
                    where_clauses.append(f"LeadScore__c >= {filters['min_lead_score']}")
                if "stage" in filters:
                    where_clauses.append(f"Status = '{filters['stage']}'")
                if "industry" in filters:
                    where_clauses.append(f"Industry = '{filters['industry']}'")

            where_clause = " AND ".join(where_clauses) if where_clauses else ""
            query = f"SELECT Id, Company, FirstName, LastName, Email, Phone, Industry, LeadScore__c, LeadSource, Status, Amount__c, Budget__c FROM Lead"
            if where_clause:
                query += f" WHERE {where_clause}"
            query += " LIMIT 500"

            # Execute SOQL
            endpoint = "/query"
            result = await self._api_call("GET", f"{endpoint}?q={query}")

            leads = []
            for record in result.get("records", []):
                leads.append(
                    CRMLead(
                        id=record["Id"],
                        company_name=record.get("Company", ""),
                        contact_name=f"{record.get('FirstName', '')} {record.get('LastName', '')}".strip(),
                        email=record.get("Email", ""),
                        phone=record.get("Phone"),
                        industry=record.get("Industry"),
                        lead_score=record.get("LeadScore__c"),
                        source=record.get("LeadSource"),
                        stage=record.get("Status"),
                        estimated_value=record.get("Amount__c"),
                        budget=record.get("Budget__c"),
                    )
                )

            logger.info(f"Fetched {len(leads)} leads from Salesforce")
            return leads

        except Exception as e:
            logger.error(f"Salesforce fetch_leads failed: {e}")
            return []

    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Update lead in Salesforce."""
        try:
            endpoint = f"/sobjects/Lead/{lead_id}"
            await self._api_call("PATCH", endpoint, data=data)
            logger.info(f"Updated lead {lead_id} in Salesforce")
            return True

        except Exception as e:
            logger.error(f"Salesforce update_lead failed: {lead_id} - {e}")
            return False

    async def create_activity(
        self, lead_id: str, activity_type: str, description: str
    ) -> bool:
        """Log activity (task) in Salesforce."""
        try:
            activity_data = {
                "WhoId": lead_id,
                "Subject": activity_type,
                "Description": description,
                "ActivityDate": None,  # Today
                "ReminderDateTime": None,
                "IsReminderSet": False,
            }

            endpoint = "/sobjects/Task"
            await self._api_call("POST", endpoint, data=activity_data)
            logger.info(f"Logged activity for lead {lead_id}: {activity_type}")
            return True

        except Exception as e:
            logger.error(f"Salesforce create_activity failed: {lead_id} - {e}")
            return False
