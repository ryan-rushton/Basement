from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
paste = Table('paste', pre_meta,
    Column('db_id', INTEGER, primary_key=True, nullable=False),
    Column('url', VARCHAR(length=240)),
    Column('name', VARCHAR(length=120)),
    Column('content', TEXT),
    Column('datetime', TIMESTAMP),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['paste'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['paste'].create()
