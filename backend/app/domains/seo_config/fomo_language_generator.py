"""Multi-language FOMO copy generation (ES, EN, PT)."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.seo_config.fomo_generator import PublicationFOMOGenerator


class FOMALanguageGenerator:
  """Generate FOMO copy in multiple languages."""

  SUPPORTED_LANGUAGES = ['es', 'en', 'pt']
  LANGUAGE_NAMES = {
    'es': 'Español',
    'en': 'English',
    'pt': 'Português',
  }

  def __init__(self, db: AsyncSession):
    self.db = db
    self.fomo_gen = PublicationFOMOGenerator(db)

  async def generate_multilingual(
    self,
    business_id: UUID,
    link_id: UUID,
    platform: str,
    base_urgency: str | None = None,
  ) -> dict[str, object]:
    """Generate FOMO copy in all supported languages."""

    results = {}

    for lang in self.SUPPORTED_LANGUAGES:
      try:
        copy = await self.fomo_gen.generate_fomo_copy(
          business_id=business_id,
          link_id=link_id,
          platform=platform,
          force_urgency=base_urgency,
          language=lang,
        )

        if copy:
          results[lang] = {
            'copy': copy.fomo_copy,
            'urgency_trigger': copy.urgency_trigger,
            'language_name': self.LANGUAGE_NAMES[lang],
          }
      except Exception as e:
        print(f'Error generating {lang} copy: {e}')
        results[lang] = {'error': str(e)}

    return results

  async def generate_for_language(
    self,
    business_id: UUID,
    link_id: UUID,
    platform: str,
    language: str,
    urgency: str | None = None,
  ) -> dict[str, object]:
    """Generate FOMO copy for a specific language."""

    if language not in self.SUPPORTED_LANGUAGES:
      return {
        'error': f'Unsupported language: {language}. Supported: {self.SUPPORTED_LANGUAGES}',
      }

    try:
      copy = await self.fomo_gen.generate_fomo_copy(
        business_id=business_id,
        link_id=link_id,
        platform=platform,
        force_urgency=urgency,
        language=language,
      )

      if copy:
        return {
          'language': language,
          'language_name': self.LANGUAGE_NAMES[language],
          'copy': copy.fomo_copy,
          'urgency_trigger': copy.urgency_trigger,
          'platform': platform,
        }
      else:
        return {'error': 'Failed to generate copy'}
    except Exception as e:
      return {'error': str(e)}

  async def get_language_comparison(
    self,
    business_id: UUID,
    link_id: UUID,
    platform: str,
  ) -> dict[str, object]:
    """Get FOMO copy comparison across all languages."""

    comparison = {
      'link_id': str(link_id),
      'platform': platform,
      'languages': await self.generate_multilingual(business_id, link_id, platform),
    }

    return comparison
