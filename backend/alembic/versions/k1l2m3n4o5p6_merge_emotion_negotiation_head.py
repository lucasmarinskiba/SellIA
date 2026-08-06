"""merge_emotion_negotiation_head

Revision ID: k1l2m3n4o5p6
Revises: j1k2l3m4n5o6, 9a03g4b5c6d7
Create Date: 2026-08-05 19:00:00.000000+00:00

9a03g4b5c6d7 was orphaned when 0ecfa96b7780's down_revision tuple was
fixed to remove the two entries that made the history cyclic (it had
listed 9a03g4b5c6d7 as its own parent while also being 9a03g4b5c6d7's
ancestor). This merge folds that now-dangling head back into the main
line at the tip.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = ('j1k2l3m4n5o6', '9a03g4b5c6d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
