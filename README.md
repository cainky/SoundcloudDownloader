# SoundCloud Downloader

## Description

This project provides a Python script for downloading entire playlists from SoundCloud. It uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to handle the downloading process, making it robust against changes in SoundCloud's website structure. The script downloads each track in the playlist, converts them to MP3 format, and packages them into a zip file.

## Requirements

- Python 3.10+
- yt-dlp
- FFmpeg

## Installation

1. Clone this repository:
```python
git clone https://github.com/yourusername/soundcloud-playlist-downloader.git
cd soundcloud-playlist-downloader
```

2. Install the required Python package:
```python
pip install yt-dlp
```

3. Install FFmpeg:
- On Ubuntu or Debian: `sudo apt-get install ffmpeg`
- On macOS with Homebrew: `brew install ffmpeg`
- On Windows, download from the [official FFmpeg website](https://www.ffmpeg.org/download.html) and add it to your PATH.

## Usage

1. Run the script:

```python
python soundcloud_downloader.py
```

2. When prompted, enter the URL of the SoundCloud playlist you want to download. Paste the entire url including the `?si=` part. Playlist can be private.

3. Enter the output directory where you want the files to be saved (or press Enter to use the `output` directory).

4. The script will download all tracks in the playlist, convert them to MP3, and create a zip file containing all the tracks.


## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](./LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws and SoundCloud's terms of service when using this script. The authors are not responsible for any misuse of this software.