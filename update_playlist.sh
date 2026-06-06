#!/usr/bin/env bash
#
# update_playlist.sh
#
# Builds playlist.txt from audio files in the music/ directory.
#
# Design goals:
# - Beginner friendly: prints clear messages.
# - Safe with spaces, apostrophes, and other common filename characters.
# - Ignores hidden files and hidden directories.
# - Supports mp3, m4a, and wav files.
# - Produces an FFmpeg concat demuxer playlist.
#
# FFmpeg concat playlist lines look like:
#   file '/absolute/path/to/song with spaces.mp3'
#
# The script writes to a temporary file first, then moves it into place.
# That avoids leaving a half-written playlist if something fails.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MUSIC_DIR="${SCRIPT_DIR}/music"
PLAYLIST_FILE="${SCRIPT_DIR}/playlist.txt"
TMP_PLAYLIST="${SCRIPT_DIR}/playlist.txt.tmp"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/playlist.log"

mkdir -p "${LOG_DIR}"

log() {
    # Print to stdout for systemd/journalctl and also append to a local log file.
    # Example journal view:
    #   sudo journalctl -u bosphorus-radio -f
    local message="$1"
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${message}" | tee -a "${LOG_FILE}"
}

escape_for_ffmpeg_concat() {
    # The concat demuxer accepts single-quoted paths.
    # Inside single quotes, a literal apostrophe is represented as: '\''.
    local path="$1"
    local escaped="${path//\'/\'\\\'\'}"
    printf "%s" "${escaped}"
}

main() {
    log "Starting playlist update."

    if [[ ! -d "${MUSIC_DIR}" ]]; then
        log "ERROR: Music directory does not exist: ${MUSIC_DIR}"
        exit 1
    fi

    : > "${TMP_PLAYLIST}"

    local count=0
    local file

    # Notes about this find command:
    # - -type f includes files only.
    # - ! -path '*/.*' ignores hidden files and files inside hidden directories.
    # - The grouped -iname tests accept mp3, m4a, and wav in any letter case.
    # - -print0 plus read -d '' keeps filenames with spaces safe.
    while IFS= read -r -d '' file; do
        local escaped
        escaped="$(escape_for_ffmpeg_concat "${file}")"
        printf "file '%s'\n" "${escaped}" >> "${TMP_PLAYLIST}"
        count=$((count + 1))
    done < <(
        find "${MUSIC_DIR}" \
            -type f \
            ! -path '*/.*' \
            \( -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.wav' \) \
            -print0 | sort -z
    )

    if [[ "${count}" -eq 0 ]]; then
        rm -f "${TMP_PLAYLIST}"
        log "ERROR: No supported audio files found in ${MUSIC_DIR}."
        log "Add .mp3, .m4a, or .wav files, then run ./update_playlist.sh again."
        exit 1
    fi

    mv "${TMP_PLAYLIST}" "${PLAYLIST_FILE}"
    log "Playlist written: ${PLAYLIST_FILE}"
    log "Audio tracks found: ${count}"
}

main "$@"
