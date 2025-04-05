from database import get_db, dispose_database
from models import Track


async def create_new_track(track_id: str, song_link: str, artist: str, track_name: str, full_track_name: str) -> Track | None:
    async for session in get_db():
        try:
            new_track = Track(id=track_id, song_link=song_link, artist=artist, track_name=track_name, full_track_name=full_track_name)
            session.add(new_track)
            await session.commit()
            await session.refresh(new_track) # Обновляем объект, чтобы получить данные из БД (например, если есть автоинкрементные поля)
            return new_track
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await dispose_database()


async def get_track(track_id: str):
    async for session in get_db():
        try:
            track = await session.get(Track, track_id)
            return track
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await dispose_database()