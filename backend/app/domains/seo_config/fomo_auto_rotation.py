"""Smart auto-rotation: regenerate FOMO when decay detected, auto-test winner."""

from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domains.seo_config.fomo_decay_service import FOMADecayService
from app.domains.seo_config.fomo_service import FOMAConversionService
from app.domains.seo_config.fomo_abtest_service import FOMABTestService
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator


class FOMAAutoRotator:
  """Automatic FOMO copy rotation on decay detection."""

  def __init__(self, db: AsyncSession):
    self.db = db
    self.decay_service = FOMADecayService(db)
    self.conversion_service = FOMAConversionService(db)
    self.abtest_service = FOMABTestService(db)
    self.fomo_gen = PublicationFOMOGenerator(db)

  async def auto_rotate_on_decay(self, business_id: UUID) -> dict[str, object]:
    """
    1. Detect links with decay >30%
    2. Generate new FOMO copy variants
    3. Auto-start A/B test
    4. Return summary.
    """
    # Detect decay
    decayed_links = await self.decay_service.get_links_with_decay(
      business_id=business_id,
      decay_threshold=30,
    )

    if not decayed_links:
      return {
        'rotated': 0,
        'links': [],
      }

    rotated = []

    for link in decayed_links:
      link_obj = link.get('link')
      if not link_obj:
        continue

      # Generate new variants (A, B, C)
      try:
        variant_a = await self.fomo_gen.generate_fomo_copy(
          business_id=business_id,
          link_id=link_obj.id,
          platform=link_obj.platform,
          force_urgency='scarcity',
        )

        variant_b = await self.fomo_gen.generate_fomo_copy(
          business_id=business_id,
          link_id=link_obj.id,
          platform=link_obj.platform,
          force_urgency='social_proof',
        )

        variant_c = await self.fomo_gen.generate_fomo_copy(
          business_id=business_id,
          link_id=link_obj.id,
          platform=link_obj.platform,
          force_urgency='time_pressure',
        )

        if not (variant_a and variant_b and variant_c):
          continue

        # Create A/B test
        test_result = await self.abtest_service.create_ab_test(
          business_id=business_id,
          link_id=link_obj.id,
          variant_a_id=variant_a.id,
          variant_b_id=variant_b.id,
          variant_c_id=variant_c.id,
        )

        if test_result:
          rotated.append({
            'link_id': str(link_obj.id),
            'link_title': link_obj.title,
            'baseline_ctr': link.get('baseline_ctr'),
            'current_ctr': link.get('current_ctr'),
            'decay': link.get('decay_percentage'),
            'new_test_id': str(test_result.id),
            'rotated_at': datetime.utcnow().isoformat(),
          })
      except Exception as e:
        print(f'Auto-rotation failed for link {link_obj.id}: {e}')
        continue

    return {
      'rotated': len(rotated),
      'links': rotated,
    }

  async def get_rotation_history(
    self,
    business_id: UUID,
    days: int = 7,
  ) -> list[dict[str, object]]:
    """Get recent auto-rotations (query A/B tests that started due to decay)."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Query A/B tests created after decay was detected
    # (in real implementation, would add auto_rotation flag to FOMABTest)
    result = await self.db.execute(
      select(PublicationLinkFOMO).where(
        PublicationLinkFOMO.business_id == business_id,
      )
      .order_by(PublicationLinkFOMO.created_at.desc())
    )

    fomos = result.scalars().all()
    history = []

    for fomo in fomos:
      if fomo.created_at > cutoff:
        history.append({
          'link_id': str(fomo.link_id),
          'copy': fomo.fomo_copy,
          'urgency_trigger': fomo.urgency_trigger,
          'created_at': fomo.created_at.isoformat(),
        })

    return history
