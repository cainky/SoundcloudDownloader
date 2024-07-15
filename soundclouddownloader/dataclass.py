from dataclasses import dataclass
from typing import List


@dataclass
class Track:
    id: str
    title: str
    artist: str
    url: str


@dataclass
class Playlist:
    id: str
    title: str
    tracks: List[Track]
