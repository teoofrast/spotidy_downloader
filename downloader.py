import os
import re
import asyncio

import aiofiles
import httpx
from aiogram import types

from logger_file import setup_logger
from DAO import *

logger = setup_logger(__name__)

class SpotifyDownloaderFacade:
    __slots__ = ('rapidapi_key',)

    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key

    async def fetch_song_data(self, song_id: str):
        url = "https://spotify-music-mp3-downloader-api.p.rapidapi.com/download"
        querystring = {"link": song_id}
        headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": "spotify-music-mp3-downloader-api.p.rapidapi.com"
        }
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.get(url, params=querystring, headers=headers)
            logger.info('logger was fetch data %s', response.json())
            return response.json()['data']['medias'][0]['url']
        except Exception as e:
            logger.error('logger was fetch data %s', str(e))
            raise e

    @staticmethod
    async def downloading_song(url: str, output_file: str = 'output.mp3'):
        async with httpx.AsyncClient(timeout=300) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                async with aiofiles.open(output_file, 'wb') as f:
                    await f.write(response.content)
            except Exception as e:
                logger.error('http response is not excellent %s', str(e))
                raise e
            return True

    async def get_track_name_async(self, track_url, track_id, client_id, client_secret):
        """Асинхронно получает название трека по ссылке на Spotify."""


        # Аутентификация
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }

        async with httpx.AsyncClient() as client:
            try:
                auth_response = await client.post(auth_url, data=auth_data)
                auth_response.raise_for_status()
                auth_json = auth_response.json()
                access_token = auth_json['access_token']

                # Получаем информацию о треке
                track_url = f'https://api.spotify.com/v1/tracks/{track_id}'
                headers = {'Authorization': f'Bearer {access_token}'}

                track_response = await client.get(track_url, headers=headers)
                track_response.raise_for_status()
                track_info = track_response.json()
                track_name = track_info['name']
                artist_name = track_info['artists'][0]['name']
                artists = ', '.join([artist['name'] for artist in track_info['artists']])
                full_track_name = f"{artists} - {track_name}.mp3"
                return full_track_name, artist_name, track_name

            except httpx.HTTPStatusError as e:
                logger.error('Ошибка HTTP: %s', e)
                return None
            except httpx.RequestError as e:
                logger.error('Ошибка запроса: %s', e)
                return None
            except KeyError as e:
                logger.error('Ошибка при разборе JSON ответа %s', e)
                return None

    async def get_mp3(self, song_id: str, client_id, client_secret, bot, chat_id):
        track_id = await asyncio.to_thread(get_track_id, song_id)
        logger.info('The track id is %s', track_id)
        track = await get_track(track_id)
        logger.info('The track is %s, and the type of track is %s', track, type(track))
        if track is not None:
            logger.info('Get data from database %s', track)
            song_link = track.song_link
            output_file = track.full_track_name
        else:
            song_link = await self.fetch_song_data(song_id)
            track_info = await self.get_track_name_async(song_id, track_id, client_id, client_secret)
            output_file = track_info[0]
            artist_name = track_info[1]
            track_name = track_info[2]
            logger.info('Song is %s and download link is %s', output_file, song_link)
            await create_new_track(track_id, song_link, artist_name, track_name, output_file)
        try:
            await self.__class__.downloading_song(song_link, output_file)
        except Exception as e:
            logger.info('Download failed %s', str(e))
            await bot.send_message(chat_id, 'Произошла ошибка при скачивании файла. Повторите попытку!!')
        await asyncio.sleep(2)
        try:
            input_file = types.FSInputFile(output_file)
            await bot.send_audio(chat_id, audio=input_file)
            await asyncio.to_thread(os.remove, output_file)

        except FileNotFoundError:
            await bot.send_message(chat_id, "Ошибка при отправке файла.")

        except Exception as e:
            logger.error('Error sending audio: %s', str(e))
            await bot.send_message(chat_id, "Произошла ошибка при отправке файла.")


def get_track_id(track_url: str,):
    # Извлекаем ID трека из URL
    track_id = re.search(r'track/([a-zA-Z0-9]+)', track_url)
    if not track_id:
        return None

    track_id = track_id.group(1)
    return track_id