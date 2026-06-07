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
    VIDEO_WIDTH="${VIDEO_WIDTH:-854}"
    VIDEO_HEIGHT="${VIDEO_HEIGHT:-480}"
    VIDEO_FPS="${VIDEO_FPS:-24}"
    VIDEO_BITRATE="${VIDEO_BITRATE:-900k}"
    VIDEO_MAXRATE="${VIDEO_MAXRATE:-1100k}"
    VIDEO_BUFSIZE="${VIDEO_BUFSIZE:-2200k}"
    X264_PRESET="${X264_PRESET:-ultrafast}"
    FFMPEG_THREADS="${FFMPEG_THREADS:-1}"
    AUDIO_BITRATE="${AUDIO_BITRATE:-128k}"
    AUDIO_RATE="${AUDIO_RATE:-44100}"
    AUDIO_CHANNELS="${AUDIO_CHANNELS:-2}"
}

validate_number() {
    local name="$1"
    local value="$2"

    if [[ ! "${value}" =~ ^[0-9]+$ ]]; then
        fail "${name} must be a whole number. Current value: ${value}"
    fi
}

validate_stream_settings() {
    validate_number "VIDEO_WIDTH" "${VIDEO_WIDTH}"
    validate_number "VIDEO_HEIGHT" "${VIDEO_HEIGHT}"
    validate_number "VIDEO_FPS" "${VIDEO_FPS}"
    validate_number "FFMPEG_THREADS" "${FFMPEG_THREADS}"
    validate_number "AUDIO_RATE" "${AUDIO_RATE}"
    validate_number "AUDIO_CHANNELS" "${AUDIO_CHANNELS}"

    if (( VIDEO_WIDTH < 320 || VIDEO_HEIGHT < 180 )); then
        fail "Video resolution is too small. Use at least 320x180."
    fi

    if (( VIDEO_FPS < 1 || VIDEO_FPS > 30 )); then
        fail "VIDEO_FPS must be between 1 and 30 on this VPS."
    fi

    if (( FFMPEG_THREADS < 1 || FFMPEG_THREADS > 2 )); then
        fail "FFMPEG_THREADS must be 1 or 2 on this VPS."
    fi
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
    timeout 20s ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i "${PLAYLIST_FILE}" -t 1 -f null - >/dev/null \
        || fail "FFmpeg cannot read the generated playlist. Check your audio files."

    log "Health checks passed."
}

start_stream() {
    local output_url="${YOUTUBE_RTMP_URL}/${YOUTUBE_STREAM_KEY}"

    log "Starting FFmpeg stream to YouTube RTMP."
    log "Video: ${VIDEO_WIDTH}x${VIDEO_HEIGHT}, ${VIDEO_FPS}fps, H.264, ${VIDEO_BITRATE}."
    log "Audio: AAC ${AUDIO_BITRATE}. FFmpeg threads: ${FFMPEG_THREADS}."

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
        -framerate "${VIDEO_FPS}" \
        -i "${BACKGROUND_IMAGE}" \
        -map 1:v:0 \
        -map 0:a:0 \
        -vf "scale=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop=${VIDEO_WIDTH}:${VIDEO_HEIGHT},fps=${VIDEO_FPS},format=yuv420p" \
        -c:v libx264 \
        -preset "${X264_PRESET}" \
        -threads "${FFMPEG_THREADS}" \
        -tune stillimage \
        -profile:v baseline \
        -level 3.1 \
        -pix_fmt yuv420p \
        -r "${VIDEO_FPS}" \
        -g "$((VIDEO_FPS * 2))" \
        -keyint_min "$((VIDEO_FPS * 2))" \
        -sc_threshold 0 \
        -b:v "${VIDEO_BITRATE}" \
        -maxrate "${VIDEO_MAXRATE}" \
        -bufsize "${VIDEO_BUFSIZE}" \
        -c:a aac \
        -b:a "${AUDIO_BITRATE}" \
        -ar "${AUDIO_RATE}" \
        -ac "${AUDIO_CHANNELS}" \
        -af "aresample=async=1:first_pts=0" \
        -f flv \
        -flvflags no_duration_filesize \
        "${output_url}"
}

main() {
    load_env
    validate_stream_settings
    validate_stream_key
    validate_background
    validate_tools
    generate_playlist
    health_check_inputs
    start_stream
}

main "$@"
