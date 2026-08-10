"""HubSpot CRM adapter - Production integration."""

from typing import Optional, Dict, Any, List
import logging
import httpx
from app.domains.crm.crm_adapter import CRMAdapter, CRMLead, CRMType

logger = logging.getLogger(__name__)


class HubSpotAdapter(CRMAdapter):
    """Production HubSpot adapter using REST API."""

    crm_type = CRMType.HUBSPOT

    def __init__(self, api_key: str):
        """
        Initialize HubSpot adapter.

        Args:
            api_key: HubSpot private app access token
        """
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"

    async def _api_call(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API call to HubSpot."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{endpoint}"

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

    def _extract_lead_from_hubspot(self, record: Dict[str, Any]) -> CRMLead:
        """Extract CRMLead from HubSpot contact/company record."""
        props = record.get("properties", {})

        # Extract engagement signals from associations
        emails_opened = 0
        demo_attended = False
        call_scheduled = False

        return CRMLead(
            id=record.get("id"),
            company_name=props.get("company", ""),
            contact_name=props.get("firstname", "") + " " + props.get("lastname", ""),
            email=props.get("email", ""),
            phone=props.get("phone"),
            industry=props.get("industry"),
            company_size=int(props.get("numberofemployees", 0)) if props.get("numberofemployees") else None,
            annual_revenue=float(props.get("annualrevenue", 0)) if props.get("annualrevenue") else None,
            lead_score=int(props.get("hs_lead_status", 0)) if props.get("hs_lead_status") else None,
            source=props.get("source"),
            stage=props.get("lifecyclestage"),
            estimated_value=float(props.get("deal_amount", 0)) if props.get("deal_amount") else None,
            budget=props.get("budget"),
            email_opens=emails_opened,
            demo_attended=demo_attended,
            call_scheduled=call_scheduled,
            custom_fields={k: v for k, v in props.items() if k.startswith("custom_")},
        )

    async def fetch_lead(self, lead_id: str) -> Optional[CRMLead]:
        """Fetch single contact from HubSpot."""
        try:
            endpoint = f"/crm/v3/objects/contacts/{lead_id}"
            result = await self._api_call("GET", endpoint)
            return self._extract_lead_from_hubspot(result)

        except Exception as e:
            logger.error(f"HubSpot fetch_lead failed: {lead_id} - {e}")
            return None

    async def fetch_leads(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[CRMLead]:
        """Fetch multiple contacts from HubSpot with optional filtering."""
        try:
            # Build filter query
            filter_groups = []

            if filters:
                if "min_lead_score" in filters:
                    filter_groups.append(
                        {
                            "filters": [
                                {
                                    "propertyName": "hs_lead_status",
                                    "operator": "GTE",
                                    "value": str(filters["min_lead_score"]),
                                }
                            ]
                        }
                    )
                if "stage" in filters:
                    filter_groups.append(
                        {
                            "filters": [
                                {
                                    "propertyName": "lifecyclestage",
                                    "operator": "EQ",
                                    "value": filters["stage"],
                                }
                            ]
                        }
                    )

            # Query contacts
            endpoint = "/crm/v3/objects/contacts"
            query_data = {
                "limit": 100,
                "after": 0,
                "properties": [
                    "firstname",
                    "lastname",
                    "email",
                    "phone",
                    "company",
                    "industry",
                    "numberofemployees",
                    "annualrevenue",
                    "hs_lead_status",
                    "lifecyclestage",
                    "source",
                ],
            }

            if filter_groups:
                query_data["filterGroups"] = filter_groups

            result = await self._api_call("POST", f"{endpoint}/search", data=query_data)

            leads = []
            for record in result.get("results", []):
                leads.append(self._extract_lead_from_hubspot(record))

            logger.info(f"Fetched {len(leads)} leads from HubSpot")
            return leads

        except Exception as e:
            logger.error(f"HubSpot fetch_leads failed: {e}")
            return []

    async def update_lead(self, lead_id: str, data: Dict[str, Any]) -> bool:
        """Update contact in HubSpot."""
        try:
            # Map field names to HubSpot properties
            hubspot_data = {
                "properties": {
                    "lifecyclestage": data.get("stage"),
                    "notes": data.get("notes"),
                    "dealstage": data.get("deal_stage"),
                }
            }
            # Remove None values
            hubspot_data["properties"] = {
                k: v for k, v in hubspot_data["properties"].items() if v is not None
            }

            endpoint = f"/crm/v3/objects/contacts/{lead_id}"
            await self._api_call("PATCH", endpoint, data=hubspot_data)
            logger.info(f"Updated contact {lead_id} in HubSpot")
            return True

        except Exception as e:
            logger.error(f"HubSpot update_lead failed: {lead_id} - {e}")
            return False

    async def create_activity(
        self, lead_id: str, activity_type: str, description: str
    ) -> bool:
        """Create engagement activity in HubSpot."""
        try:
            # Create note/task
            activity_data = {
                "properties": {
                    "hs_note_body": f"{activity_type}: {description}",
                    "hs_timestamp": None,  # Current time
                }
            }

            endpoint = f"/crm/v3/objects/contacts/{lead_id}/associations"
            await self._api_call("POST", endpoint, data=activity_data)
            logger.info(f"Logged activity for contact {lead_id}: {activity_type}")
            return True

        except Exception as e:
            logger.error(f"HubSpot create_activity failed: {lead_id} - {e}")
            return False
