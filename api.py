"""
@Author: Gün Yanik
@Date: 12.03.2021
@License: MIT
"""

import errno
import os
import re
import urllib.request
from urllib.request import urlretrieve

import eyed3
import spotipy
import spotipy.oauth2 as oauth2
import youtube_dl
from dotenv import load_dotenv

# Load PW from .env ( you need Spotify API CLIENT_ID and CLIENT_SECRET, you then save this info in .env of this folder --> see README)
load_dotenv()
path = os.path.dirname(__file__)


def make_dir(dirnew='/music'):
    try:
        os.mkdir((path + dirnew))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass


def read_txt(filename) -> list:
    with open(filename) as f:
        lines = [line.rstrip('\n') for line in f]
    return lines


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


class SpYt:

    def __init__(self):
        self.ydl_opts = {
            # 'quiet': True,
            'format': 'bestaudio/best',
            'outtmpl': './music/%(id)s.%(ext)s',
            'ffmpeg_location': './ffmpeg/bin/',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.auth_manager = oauth2.SpotifyClientCredentials(
            os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET')
        )
        self.playlist_txt = read_txt('Playlist.txt')

    def spotify_fetch(self, list_id) -> (list, list):
        counter = 0
        term = ""
        song_container = []
        link_container = []
        table = str.maketrans(dict.fromkeys("><:\?/|*"))

        sp = spotipy.Spotify(auth_manager=self.auth_manager)
        playlists = sp.playlist_items(playlist_id=list_id)

        self.ydl_opts['outtmpl'] = './music/' + str(list_id) + '/%(title)s.%(ext)s'

        while playlists:
            for i, playlist in enumerate(playlists['items']):
                term = str(playlist['track']['name'] + ' ' + playlist['track']['artists'][0]['name'])
                term = term.translate(table)
                urlretrieve(playlist["track"]['album']['images'][0]['url'], "images/" + term + ".jpg")
                song_container.append(term)
            if playlists['next']:
                counter += 100
                playlists = sp.playlist_items(playlist_id=list_id, offset=counter)
            else:
                playlists = None

        leange = len(song_container)
        for i, song in enumerate(song_container):
            printProgressBar(i, leange, prefix='Search Songs Progress: ', suffix='Complete', length=50)

            html = urllib.request.urlopen(
                "https://www.youtube.com/results?search_query=" +
                str(''.join([y if ord(y) < 128 else ' ' for y in song]).strip().replace(' ', '%20') + '.')
            )
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            link_container.append("https://www.youtube.com/watch?v=" + video_ids[0])
        return link_container, song_container

    def youtube_fetch(self, link) -> list:
        return [link]

    def get_mp3(self):
        for item in self.playlist_txt:

            option = 0
            if 'https://open.spotify.com/playlist/' in item:
                item = item.lstrip('https://open.spotify.com/playlist/').split('?')[0].strip()
            elif 'spotify:playlist:' in item:
                item = item.lstrip('spotify:playlist:')
            elif 'https://youtu' in item or "https://www.youtu":
                option = 1
            else:
                continue

            if not option:
                link_container, terms = self.spotify_fetch(item)
                self.downloadSpotify(link_container, terms, item)
            else:
                link_container = self.youtube_fetch(item)

                self.download(link_container)
            # MERGE
            if not option:
                for term in terms:
                    audiofile = eyed3.load('music/' + item + "/" + term + ".mp3")
                    if audiofile.tag is None:
                        audiofile.initTag()

                    audiofile.tag.images.set(3, open('images/' + term +'.jpg', 'rb').read(), 'image/jpeg')
                    audiofile.tag.save(version=eyed3.id3.ID3_V2_3)

                  #  audiofile.tag.save()

    def download(self, container: list):
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download(container)

    def downloadSpotify(self, container: list, terms: list, item):
        for n, term in enumerate(terms):
            self.ydl_opts['outtmpl'] = './music/'+item+"/"+term+'.%(ext)s'
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([container[n]])
        self.ydl_opts['outtmpl'] = './music/%(id)s.%(ext)s'


if __name__ == '__main__':
    make_dir("images")
    SPFY = SpYt()
    SPFY.get_mp3()
