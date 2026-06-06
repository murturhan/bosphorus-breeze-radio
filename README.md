# Bosphorus Breeze Radio

A production-ready 24/7 YouTube live radio setup for an Oracle Cloud Free Tier Ubuntu VPS.

It uses FFmpeg to combine:

- audio files from `music/`
- a still background image from `assets/background.jpg`
- your YouTube RTMP stream key from `.env`

The stream runs forever, starts automatically on reboot, and restarts automatically if FFmpeg crashes.

## Repository Structure

```text
bosphorus-breeze-radio/
├── music/
├── assets/
│   └── background.jpg
├── logs/
├── systemd/
│   └── bosphorus-radio.service
├── .env.example
├── install.sh
├── update_playlist.sh
├── stream.sh
├── README.md
```

## What This System Does

- Runs on Ubuntu 24.04.
- Streams continuously to YouTube Live RTMP.
- Uses FFmpeg for all audio/video processing.
- Reads `.mp3`, `.m4a`, and `.wav` files from `music/`.
- Ignores hidden files and hidden folders.
- Handles spaces in filenames.
- Automatically generates `playlist.txt`.
- Loops the playlist forever.
- Uses `assets/background.jpg` as the video image.
- Outputs 1920x1080 video at 30fps.
- Uses H.264 video and AAC 192k audio.
- Logs to both local files and `journalctl`.
- Includes a systemd service for auto start and auto restart.

## Server Requirements

Recommended server:

- Oracle Cloud Free Tier Ampere or AMD Ubuntu VPS
- Ubuntu 24.04
- At least 1 GB RAM
- A stable internet connection

You also need:

- A YouTube channel with live streaming enabled
- Your YouTube Live stream key

YouTube may require up to 24 hours to enable live streaming on a new channel.

## 1. Clone The Repository

On your Ubuntu server:

```bash
git clone https://github.com/murturhan/bosphorus-breeze-radio.git
cd bosphorus-breeze-radio
```

If you upload the folder manually instead of using Git, just enter the folder:

```bash
cd bosphorus-breeze-radio
```

## 2. Run The Installer

```bash
sudo ./install.sh
```

The installer will:

- install FFmpeg
- create required folders
- create `.env` from `.env.example` if needed
- install the systemd service
- enable the service so it can start on reboot

The installer does not start streaming immediately. You need to add music and configure your stream key first.

## 3. Add Your Music

Copy your audio files into:

```text
music/
```

Supported formats:

- `.mp3`
- `.m4a`
- `.wav`

Examples:

```text
music/Song One.mp3
music/Evening Set.m4a
music/live recording.wav
```

Hidden files are ignored. For example, `.secret.mp3` will not be added to the playlist.

## 4. Add Your Background Image

Replace:

```text
assets/background.jpg
```

with your real radio background image.

Recommended image:

- JPG format
- 1920x1080 resolution
- not too small
- not transparent

The included starter image is only there so the repository has the required file. For a real stream, replace it with your own artwork.

## 5. Add Your YouTube Stream Key

Open the `.env` file:

```bash
sudo nano .env
```

Change this:

```bash
YOUTUBE_STREAM_KEY=replace_with_your_youtube_stream_key
```

to your real stream key from YouTube Studio.

Example format:

```bash
YOUTUBE_STREAM_KEY=abcd-efgh-ijkl-mnop-1234
```

Do not add spaces around the key.

Do not commit `.env` to GitHub. It is ignored by `.gitignore`.

## 6. Generate The Playlist

Run:

```bash
./update_playlist.sh
```

This creates:

```text
playlist.txt
```

You do not need to edit `playlist.txt` manually. The stream script regenerates it automatically each time the service starts.

## 7. Test The Stream Manually

Before using systemd, you can test directly:

```bash
./stream.sh
```

Stop it with:

```bash
Ctrl+C
```

If something is wrong, the script prints a clear error message before starting FFmpeg.

## 8. Start The 24/7 Service

Start streaming:

```bash
sudo systemctl start bosphorus-radio
```

Check status:

```bash
sudo systemctl status bosphorus-radio
```

Watch live logs:

```bash
sudo journalctl -u bosphorus-radio -f
```

Stop streaming:

```bash
sudo systemctl stop bosphorus-radio
```

Restart streaming:

```bash
sudo systemctl restart bosphorus-radio
```

## 9. Auto Start On Reboot

The installer runs:

```bash
sudo systemctl enable bosphorus-radio
```

That means the stream will start automatically when the VPS reboots.

To disable auto start:

```bash
sudo systemctl disable bosphorus-radio
```

## Logs

System logs:

```bash
sudo journalctl -u bosphorus-radio -f
```

Local logs:

```text
logs/stream.log
logs/playlist.log
```

Systemd is the best place to watch production logs because it captures everything from the service.

## Health Checks

Before streaming, `stream.sh` checks that:

- `.env` exists
- `YOUTUBE_STREAM_KEY` is set
- the stream key is not the example value
- the stream key does not contain spaces
- `assets/background.jpg` exists
- FFmpeg and FFprobe are installed
- `playlist.txt` can be generated
- FFmpeg can read the background image
- FFmpeg can read the generated playlist

If a check fails, the script exits cleanly with a useful error message.

## FFmpeg Output Settings

The stream uses YouTube-friendly settings:

- Resolution: `1920x1080`
- Frame rate: `30fps`
- Video codec: `H.264`
- Pixel format: `yuv420p`
- GOP/keyframe interval: `2 seconds`
- Video bitrate: `4500k`
- Audio codec: `AAC`
- Audio bitrate: `192k`
- Audio sample rate: `44100 Hz`
- Output format: `FLV`
- Destination: YouTube RTMP

## Updating Music

To add or remove songs:

1. Stop the stream if you want the change to apply immediately.

   ```bash
   sudo systemctl stop bosphorus-radio
   ```

2. Add or remove files in `music/`.

3. Regenerate the playlist:

   ```bash
   ./update_playlist.sh
   ```

4. Start the stream again:

   ```bash
   sudo systemctl start bosphorus-radio
   ```

The service also regenerates the playlist automatically when it starts.

## Troubleshooting

### The Service Starts And Then Stops

Check logs:

```bash
sudo journalctl -u bosphorus-radio -n 100 --no-pager
```

Common causes:

- `.env` is missing
- stream key is still the example value
- `music/` has no supported audio files
- `assets/background.jpg` is missing or invalid
- FFmpeg is not installed

### YouTube Says No Data

Check:

- You started the service with `sudo systemctl start bosphorus-radio`
- your stream key is correct
- your YouTube live event is ready
- your VPS has outbound internet access
- logs do not show RTMP connection errors

### Audio Filename Has Spaces

Spaces are supported. This is fine:

```text
music/Istanbul Night Mix.mp3
```

### Hidden Files Are Ignored

These are ignored:

```text
music/.hidden.mp3
music/.archive/old-song.mp3
```

## Security Notes

- Keep `.env` private.
- Do not publish your YouTube stream key.
- If your stream key is leaked, reset it in YouTube Studio.
- Run updates regularly:

  ```bash
  sudo apt update
  sudo apt upgrade
  ```

## Useful Commands

```bash
./update_playlist.sh
./stream.sh
sudo systemctl start bosphorus-radio
sudo systemctl stop bosphorus-radio
sudo systemctl restart bosphorus-radio
sudo systemctl status bosphorus-radio
sudo journalctl -u bosphorus-radio -f
```

## License

MIT License. Use, modify, and deploy freely.
