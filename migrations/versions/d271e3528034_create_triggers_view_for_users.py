"""create triggers view for users

Revision ID: d271e3528034
Revises: 266f6fd632dc
Create Date: 2025-11-05 11:16:42.527844

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd271e3528034'
down_revision = '266f6fd632dc'
branch_labels = None
depends_on = None


def upgrade():
    op.execute (
    """
        -- =========================
        -- TRIGGERS untuk updated_at
        -- =========================
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER update_fakultas_updated_at BEFORE UPDATE ON fakultas
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_program_studi_updated_at BEFORE UPDATE ON program_studi
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        CREATE TRIGGER update_permohonan_updated_at BEFORE UPDATE ON permohonan
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    """
    )

def downgrade():
    op.execute("DROP VIEW IF EXISTS v_mahasiswa CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_dosen CASCADE;")
    op.execute("DROP VIEW IF EXISTS v_admin CASCADE;")