"""Google Ads Connector — Real Google Ads campaigns.

Alternativa a Meta Ads para campañas en Google Search, Display, etc.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

logger = logging.getLogger(__name__)


class GoogleAdsConnector:
    """Conector real de Google Ads API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        developer_token: str,
        customer_id: str,  # sin guiones (xxxxxxxxxx)
    ):
        """
        Inicializa connector.

        Requiere OAuth2 credentials + Developer Token desde Google Ads.
        """
        self.customer_id = customer_id.replace("-", "")

        self.client = GoogleAdsClient.load_from_dict(
            {
                "use_proto_plus": True,
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "type": "authorized_user",
            },
            version="v14",
        )
        self.client.set_mixed_query_parameter("developer_token", developer_token)

    async def create_search_campaign(
        self,
        campaign_name: str,
        budget_micros: int,  # $100 = 100000000 micros
        keywords: list,  # ["keyword1", "keyword2"]
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea Search campaign.

        budget_micros: presupuesto en micros (millonésimas)
        keywords: lista de keywords para match

        Retorna: (success, campaign_id)
        """
        try:
            service = self.client.get_service("CampaignService")
            budget_service = self.client.get_service("CampaignBudgetService")

            # 1. Crear budget
            budget = self.client.get_type("CampaignBudget")
            budget.name = f"budget_{campaign_name}"
            budget.amount_micros = budget_micros
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget_operation.create = budget

            budget_response = budget_service.mutate_campaign_budgets(
                customer_id=self.customer_id,
                operations=[budget_operation],
            )

            budget_id = budget_response.results[0].resource_name

            # 2. Crear campaign
            campaign = self.client.get_type("Campaign")
            campaign.name = campaign_name
            campaign.campaign_budget = budget_id
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            campaign.advertising_channel_type = (
                self.client.enums.AdvertisingChannelTypeEnum.SEARCH
            )

            campaign_operation = self.client.get_type("CampaignOperation")
            campaign_operation.create = campaign

            campaign_response = service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation],
            )

            campaign_id = campaign_response.results[0].resource_name

            logger.info(f"Google Ads campaign created: {campaign_id}")

            return True, campaign_id

        except GoogleAdsException as e:
            logger.error(f"Google Ads API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return False, None

    async def create_ad_group(
        self,
        campaign_id: str,
        ad_group_name: str,
        cpc_bid_micros: int,  # $1 = 1000000 micros
    ) -> Tuple[bool, Optional[str]]:
        """Crea Ad Group dentro de campaign."""
        try:
            service = self.client.get_service("AdGroupService")

            ad_group = self.client.get_type("AdGroup")
            ad_group.name = ad_group_name
            ad_group.campaign = campaign_id
            ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
            ad_group.cpc_bid_micros = cpc_bid_micros

            operation = self.client.get_type("AdGroupOperation")
            operation.create = ad_group

            response = service.mutate_ad_groups(
                customer_id=self.customer_id,
                operations=[operation],
            )

            ad_group_id = response.results[0].resource_name

            logger.info(f"Ad group created: {ad_group_id}")

            return True, ad_group_id

        except Exception as e:
            logger.error(f"Error creating ad group: {e}")
            return False, None

    async def create_text_ad(
        self,
        ad_group_id: str,
        headline1: str,
        headline2: str,
        description: str,
        final_url: str,
    ) -> Tuple[bool, Optional[str]]:
        """Crea Responsive Search Ad."""
        try:
            service = self.client.get_service("AdService")

            ad = self.client.get_type("Ad")

            # Responsive Search Ad
            responsive_search_ad = self.client.get_type("ResponsiveSearchAdInfo")
            responsive_search_ad.headlines.append(
                self.client.get_type("AdTextAsset", text=headline1)
            )
            responsive_search_ad.headlines.append(
                self.client.get_type("AdTextAsset", text=headline2)
            )
            responsive_search_ad.descriptions.append(
                self.client.get_type("AdTextAsset", text=description)
            )

            ad.responsive_search_ad = responsive_search_ad
            ad.final_urls.append(final_url)

            operation = self.client.get_type("AdOperation")
            operation.create = ad

            response = service.mutate_ads(
                customer_id=self.customer_id,
                operations=[operation],
            )

            ad_id = response.results[0].resource_name

            logger.info(f"Ad created: {ad_id}")

            return True, ad_id

        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return False, None

    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """Obtiene stats de campaign."""
        try:
            service = self.client.get_service("GoogleAdsService")

            query = f"""
                SELECT
                  campaign.id,
                  campaign.name,
                  metrics.impressions,
                  metrics.clicks,
                  metrics.cost_micros,
                  metrics.conversions,
                  metrics.ctr,
                  metrics.average_cpc
                FROM campaign
                WHERE campaign.id = {campaign_id.split('/')[-1]}
            """

            response = service.search_stream(
                customer_id=self.customer_id,
                query=query,
            )

            for batch in response:
                for row in batch.results:
                    return {
                        "id": row.campaign.id,
                        "name": row.campaign.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": row.metrics.cost_micros / 1000000,
                        "conversions": row.metrics.conversions,
                        "ctr": row.metrics.ctr,
                        "avg_cpc": row.metrics.average_cpc / 1000000,
                    }

            return {}

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


def get_google_ads_connector(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    developer_token: str,
    customer_id: str,
) -> GoogleAdsConnector:
    return GoogleAdsConnector(
        client_id,
        client_secret,
        refresh_token,
        developer_token,
        customer_id,
    )
