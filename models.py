from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"

    id = Column(String(30), primary_key=True, index=True, doc="Уникальный ID трека (максимум 30 символов, передается вручную)")
    song_link = Column(String(100), doc="Ссылка на песню")
    artist = Column(String(100), doc="Исполнитель")
    track_name = Column(String(100), doc="Название трека")
    full_track_name = Column(String, doc="Полное название трека")

    def __repr__(self):
        return f"<Track(id='{self.id}', track_name='{self.track_name}')>"

async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)