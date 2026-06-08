#!/usr/bin/env bash
#
# test_local.sh
#
# Safe local test for Bosphorus Breeze Radio.
#
# This script does NOT stream to YouTube.
# It checks the files and runs the same FFmpeg audio/video pipeline for a short
# time, sending the output to /dev/null instead of RTMP.
#
# Use it after adding at least one .mp3, .m4a, or .wav file to music/:
#   ./test_local.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLAYLIST_FILE="${SCRIPT_DIR}/playlist.txt"
ASSETS_DIR="${SCRIPT_DIR}/assets"
BACKGROUND_FILE=""
BACKGROUND_KIND=""
LOG_DIR="${SCRIPT_DIR}/logs"
TEST_LOG="${LOG_DIR}/test.log"
ENV_FILE="${SCRIPT_DIR}/.env"

mkdir -p "${LOG_DIR}"

log() {
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${message}" | tee -a "${TEST_LOG}"
}

fail() {
    log "ERROR: $1"
    exit 1
}

load_safe_settings() {
    if [[ -f "${ENV_FILE}" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "${ENV_FILE}"
        set +a
    fi

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

find_background() {
    local candidates=(
        "${ASSETS_DIR}/background.jpg"
        "${ASSETS_DIR}/background.jpeg"
        "${ASSETS_DIR}/background.png"
        "${ASSETS_DIR}/background.mp4"
        "${ASSETS_DIR}/background.mov"
        "${ASSETS_DIR}/background.webm"
        "${ASSETS_DIR}/background.mkv"
    )
    local candidate=""

    for candidate in "${candidates[@]}"; do
        if [[ -f "${candidate}" ]]; then
            BACKGROUND_FILE="${candidate}"
            break
        fi
    done

    [[ -n "${BACKGROUND_FILE}" ]] || fail "Background not found. Upload assets/background.jpg, .png, .mp4, .mov, .webm, or .mkv."
    [[ -s "${BACKGROUND_FILE}" ]] || fail "Background is empty: ${BACKGROUND_FILE}"

    case "${BACKGROUND_FILE,,}" in
        *.jpg|*.jpeg|*.png) BACKGROUND_KIND="image" ;;
        *.mp4|*.mov|*.webm|*.mkv) BACKGROUND_KIND="video" ;;
        *) fail "Unsupported background format: ${BACKGROUND_FILE}" ;;
    esac
}

main() {
    log "Starting safe local test. This will not stream to YouTube."
    load_safe_settings

    command -v ffmpeg >/dev/null 2>&1 || fail "ffmpeg is not installed. Run sudo ./install.sh first."
    command -v ffprobe >/dev/null 2>&1 || fail "ffprobe is not installed. Run sudo ./install.sh first."

    find_background

    log "Generating playlist."
    "${SCRIPT_DIR}/update_playlist.sh"

    [[ -f "${PLAYLIST_FILE}" ]] || fail "Playlist was not created: ${PLAYLIST_FILE}"
    [[ -s "${PLAYLIST_FILE}" ]] || fail "Playlist is empty: ${PLAYLIST_FILE}"

    log "Checking background file: ${BACKGROUND_FILE}."
    ffprobe -v error -select_streams v:0 -show_entries stream=codec_type -of csv=p=0 "${BACKGROUND_FILE}" >/dev/null \
        || fail "FFmpeg cannot read the background file."

    log "Running 5-second FFmpeg pipeline test."
    local background_input_args=()
    local tune_args=()
    if [[ "${BACKGROUND_KIND}" == "image" ]]; then
        background_input_args=(-loop 1 -framerate "${VIDEO_FPS}" -i "${BACKGROUND_FILE}")
        tune_args=(-tune stillimage)
    else
        background_input_args=(-stream_loop -1 -i "${BACKGROUND_FILE}")
    fi

    timeout 25s ffmpeg \
        -hide_banner \
        -loglevel warning \
        -stream_loop -1 \
        -f concat \
        -safe 0 \
        -i "${PLAYLIST_FILE}" \
        "${background_input_args[@]}" \
        -map 1:v:0 \
        -map 0:a:0 \
        -t 5 \
        -vf "scale=${VIDEO_WIDTH}:${VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop=${VIDEO_WIDTH}:${VIDEO_HEIGHT},fps=${VIDEO_FPS},format=yuv420p" \
        -c:v libx264 \
        -preset "${X264_PRESET}" \
        -threads "${FFMPEG_THREADS}" \
        "${tune_args[@]}" \
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
        -f null -

    log "Local test passed. The FFmpeg pipeline works without streaming to YouTube."
}

main "$@"
