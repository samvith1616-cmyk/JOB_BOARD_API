"""add search vector to jobs

Revision ID: f864a58d47d7
Revises: eb160bac7be9
Create Date: 2026-07-17 10:56:25.932244

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR



# revision identifiers, used by Alembic.
revision: str = 'f864a58d47d7'
down_revision: Union[str, Sequence[str], None] = 'eb160bac7be9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # Add tsvector column
    op.add_column('jobs',
        sa.Column('search_vector', TSVECTOR, nullable=True)
    )
    
    # Create GIN index on the tsvector column
    op.create_index(
        'idx_jobs_search_vector',
        'jobs',
        ['search_vector'],
        postgresql_using='gin'
    )
    
    # Populate existing rows with their search vectors
    op.execute("""
        UPDATE jobs 
        SET search_vector = to_tsvector('english', 
            coalesce(title, '') || ' ' || 
            coalesce(description, '') || ' ' ||
            coalesce(location, '')
        )
    """)
    
    # Create a trigger to auto-update search_vector when job is updated
    op.execute("""
        CREATE OR REPLACE FUNCTION update_job_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector = to_tsvector('english',
                coalesce(NEW.title, '') || ' ' ||
                coalesce(NEW.description, '') || ' ' ||
                coalesce(NEW.location, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER jobs_search_vector_update
        BEFORE INSERT OR UPDATE ON jobs
        FOR EACH ROW
        EXECUTE FUNCTION update_job_search_vector();
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS jobs_search_vector_update ON jobs")
    op.execute("DROP FUNCTION IF EXISTS update_job_search_vector")
    op.drop_index('idx_jobs_search_vector', table_name='jobs')
    op.drop_column('jobs', 'search_vector')
