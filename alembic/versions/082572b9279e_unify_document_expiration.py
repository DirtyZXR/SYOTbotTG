"""unify_document_expiration

Revision ID: 082572b9279e
Revises: 0625cfd877dd
Create Date: 2026-05-28 15:43:06.858737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '082572b9279e'
down_revision: Union[str, Sequence[str], None] = '0625cfd877dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Data migration: Unify document expiration by setting access_granted_at 
    # to the maximum of all passed_at dates and access_granted_at itself.
    # Additionally, reset all expiration notification flags to ensure users 
    # and admins receive notifications correctly based on the new unified date.
    op.execute("""
        UPDATE users 
        SET 
            notified_7d = 0,
            notified_1d = 0,
            notified_3g_exp_7d = 0,
            notified_3g_exp_1d = 0,
            notified_4g_exp_7d = 0,
            notified_4g_exp_1d = 0,
            notified_5g_exp_7d = 0,
            notified_5g_exp_1d = 0,
            access_granted_at = (
                SELECT MAX(val) 
                FROM (
                    SELECT access_granted_at AS val
                    UNION ALL SELECT group2_passed_at
                    UNION ALL SELECT group3_passed_at
                    UNION ALL SELECT group4_passed_at
                    UNION ALL SELECT group5_passed_at
                ) WHERE val IS NOT NULL
            )
        WHERE is_verified = 1
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
