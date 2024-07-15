# SoundCloud Downloader

## Description

This project provides a Python script for downloading entire playlists from SoundCloud. It uses yt-dlp (a fork of youtube-dl) to handle the downloading process, making it robust against changes in SoundCloud's website structure. The script downloads each track in the playlist, converts them to MP3 format, and packages them into a zip file for easy distribution.

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
- On Windows, download from the official FFmpeg website and add it to your PATH.

## Usage

1. Run the script:

```python
python soundcloud_downloader.py
```

2. When prompted, enter the URL of the SoundCloud playlist you want to download.

3. Enter the output directory where you want the files to be saved (or press Enter to use the current directory).

4. The script will download all tracks in the playlist, convert them to MP3, and create a zip file containing all the tracks.

## How It Works

1. The script uses yt-dlp to extract information about the playlist and its tracks.
2. It then downloads each track concurrently using a ThreadPoolExecutor.
3. As each track is downloaded, it's converted to MP3 format using FFmpeg.
4. After all tracks are downloaded, they're packaged into a single zip file for the user to download

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [LICENSE](./LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws and SoundCloud's terms of service when using this script. The authors are not responsible for any misuse of this software.