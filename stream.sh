#!/usr/bin/env bash
#
# stream.sh
#
# Starts a 24/7 YouTube live radio stream using FFmpeg.
#
# What it does:
# - Loads the YouTube stream key from .env.
# - Validates required files before streaming.
# - Regenerates playlist.txt automatically.
# - Uses assets/background.jpg as a looping video background.
# - Streams audio from music/ forever.
# - Writes useful logs for both journalctl and local troubleshooting.
# - Performs simple health checks before handing the process to FFmpeg.
#
# This script is intended to be run by systemd, but you can also run it manually:
#   ./stream.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
PLAYLIST_FILE="${SCRIPT_DIR}/playlist.txt"
BACKGROUND_IMAGE="${SCRIPT_DIR}/assets/background.jpg"
LOG_DIR="${SCRIPT_DIR}/logs"
STREAM_LOG="${LOG_DIR}/stream.log"
PID_FILE="${LOG_DIR}/ffmpeg.pid"

mkdir -p "${LOG_DIR}"

log() {
    # stdout/stderr are captured by systemd, so every message is journalctl friendly.
    # tee also keeps a local log at logs/stream.log.
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${message}" | tee -a "${STREAM_LOG}"
}

fail() {
    log "ERROR: $1"
    exit 1
}

cleanup() {
    rm -f "${PID_FILE}"
}

trap cleanup EXIT

load_env() {
    [[ -f "${ENV_FILE}" ]] || fail "Missing .env file. Copy .env.example to .env and add your YouTube stream key."

    # Export variables defined in .env so FFmpeg settings can be configured
    # without editing this script.
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a

    YOUTUBE_RTMP_URL="${YOUTUBE_RTMP_URL:-rtmp://a.rtmp.youtube.com/live2}"
    FFMPEG_LOG_LEVEL="${FFMPEG_LOG_LEVEL:-info}"
}

validate_stream_key() {
    # YouTube stream keys vary by account and format. This check is intentionally
    # conservative: it catches empty/default values without rejecting valid keys.
    if [[ -z "${YOUTUBE_STREAM_KEY:-}" ]]; then
        fail "YOUTUBE_STREAM_KEY is empty in .env."
    fi

    if [[ "${YOUTUBE_STREAM_KEY}" == "replace_with_your_youtube_stream_key" ]]; then
        fail "YOUTUBE_STREAM_KEY still has the example value. Edit .env before streaming."
    fi

    if [[ "${#YOUTUBE_STREAM_KEY}" -lt 8 ]]; then
        fail "YOUTUBE_STREAM_KEY looks too short. Please check the value copied from YouTube Studio."
    fi

    if [[ "${YOUTUBE_STREAM_KEY}" =~ [[:space:]] ]]; then
        fail "YOUTUBE_STREAM_KEY contains whitespace. Remove spaces or line breaks from .env."
    fi
}

validate_background() {
    [[ -f "${BACKGROUND_IMAGE}" ]] || fail "Background image not found: ${BACKGROUND_IMAGE}"
    [[ -s "${BACKGROUND_IMAGE}" ]] || fail "Background image exists but is empty: ${BACKGROUND_IMAGE}"
}

validate_tools() {
    command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg is not installed. Run ./install.sh first."
    command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is not installed. Run ./install.sh first."
}

generate_playlist() {
    log "Generating playlist from music directory."
    "${SCRIPT_DIR}/update_playlist.sh"
    [[ -f "${PLAYLIST_FILE}" ]] || fail "Playlist was not created: ${PLAYLIST_FILE}"
    [[ -s "${PLAYLIST_FILE}" ]] || fail "Playlist is empty: ${PLAYLIST_FILE}"
}

health_check_inputs() {
    log "Running input health checks."

    # Confirm FFmpeg can decode the background image.
    ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "${BACKGROUND_IMAGE}" >/dev/null \
        || fail "FFmpeg cannot read the background image. Replace assets/background.jpg with a valid JPG."

    # Confirm at least the first playlist item is decodable.
    # The concat demuxer itself handles all playlist paths during streaming.
    ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i "${PLAYLIST_FILE}" -t 1 -f null - >/dev/null \
        || fail "FFmpeg cannot read the generated playlist. Check your audio files."

    log "Health checks passed."
}

start_stream() {
    local output_url="${YOUTUBE_RTMP_URL}/${YOUTUBE_STREAM_KEY}"

    log "Starting FFmpeg stream to YouTube RTMP."
    log "Video: 1920x1080, 30fps, H.264, YouTube optimized."
    log "Audio: AAC 192k."

    # exec replaces the shell with ffmpeg.
    # This helps systemd track and restart the actual streaming process.
    echo "$$" > "${PID_FILE}"

    exec ffmpeg \
        -hide_banner \
        -loglevel "${FFMPEG_LOG_LEVEL}" \
        -nostdin \
        -re \
        -stream_loop -1 \
        -f concat \
        -safe 0 \
        -i "${PLAYLIST_FILE}" \
        -loop 1 \
        -framerate 30 \
        -i "${BACKGROUND_IMAGE}" \
        -map 1:v:0 \
        -map 0:a:0 \
        -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p" \
        -c:v libx264 \
        -preset veryfast \
        -tune stillimage \
        -profile:v high \
        -level 4.2 \
        -pix_fmt yuv420p \
        -r 30 \
        -g 60 \
        -keyint_min 60 \
        -sc_threshold 0 \
        -b:v 4500k \
        -maxrate 4500k \
        -bufsize 9000k \
        -c:a aac \
        -b:a 192k \
        -ar 44100 \
        -ac 2 \
        -af "aresample=async=1:first_pts=0" \
        -f flv \
        -flvflags no_duration_filesize \
        "${output_url}"
}

main() {
    load_env
    validate_stream_key
    validate_background
    validate_tools
    generate_playlist
    health_check_inputs
    start_stream
}

main "$@"
