from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
paste = Table('paste', post_meta,
    Column('db_id', Integer, primary_key=True, nullable=False),
    Column('url', String(length=240)),
    Column('name', String(length=120)),
    Column('content', Text),
    Column('datetime', DateTime),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['paste'].columns['db_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['paste'].columns['db_id'].drop()
