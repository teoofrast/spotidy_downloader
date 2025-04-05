import eyed3

audio_file = eyed3.load('DMX, Swizz Beatz - Get It On The Floor.mp3')
print(audio_file.tag.artist)
print(audio_file.tag.title)
