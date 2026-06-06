#!/usr/bin/env bash
#
# install.sh
#
# Installs and prepares Bosphorus Breeze Radio on Ubuntu 24.04.
#
# This script:
# - Installs FFmpeg.
# - Creates required folders.
# - Sets executable permissions on scripts.
# - Creates .env from .env.example if .env does not exist.
# - Installs the systemd service.
# - Enables auto start on reboot.
#
# Run from the repository directory:
#   sudo ./install.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="bosphorus-radio.service"
SERVICE_SOURCE="${SCRIPT_DIR}/systemd/${SERVICE_NAME}"
SERVICE_TARGET="/etc/systemd/system/${SERVICE_NAME}"
LOG_DIR="${SCRIPT_DIR}/logs"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$1"
}

fail() {
    log "ERROR: $1"
    exit 1
}

require_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        fail "Please run this installer with sudo: sudo ./install.sh"
    fi
}

require_ubuntu() {
    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        source /etc/os-release
        if [[ "${ID:-}" != "ubuntu" ]]; then
            log "WARNING: This project is designed for Ubuntu 24.04. Detected: ${PRETTY_NAME:-unknown Linux}."
        elif [[ "${VERSION_ID:-}" != "24.04" ]]; then
            log "WARNING: This project is tested for Ubuntu 24.04. Detected Ubuntu ${VERSION_ID:-unknown}."
        else
            log "Detected Ubuntu 24.04."
        fi
    else
        log "WARNING: Cannot read /etc/os-release. Continuing anyway."
    fi
}

install_packages() {
    log "Updating package list."
    apt-get update

    log "Installing FFmpeg and basic certificates."
    apt-get install -y --no-install-recommends ffmpeg ca-certificates
}

prepare_files() {
    log "Creating required directories."
    mkdir -p "${SCRIPT_DIR}/music" "${SCRIPT_DIR}/assets" "${LOG_DIR}"

    log "Setting executable permissions on scripts."
    chmod +x "${SCRIPT_DIR}/install.sh" "${SCRIPT_DIR}/update_playlist.sh" "${SCRIPT_DIR}/stream.sh"

    if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
        log "Creating .env from .env.example."
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        chmod 600 "${SCRIPT_DIR}/.env"
        log "Edit ${SCRIPT_DIR}/.env and add your real YouTube stream key before starting the service."
    else
        log ".env already exists; leaving it unchanged."
    fi
}

install_service() {
    [[ -f "${SERVICE_SOURCE}" ]] || fail "Missing systemd service file: ${SERVICE_SOURCE}"

    log "Installing systemd service: ${SERVICE_TARGET}"
    cp "${SERVICE_SOURCE}" "${SERVICE_TARGET}"

    # Replace the repository path in the service file with the actual install path.
    # This keeps the repository portable no matter where it is cloned.
    sed -i "s|/opt/bosphorus-breeze-radio|${SCRIPT_DIR}|g" "${SERVICE_TARGET}"

    log "Reloading systemd."
    systemctl daemon-reload

    log "Enabling auto start on reboot."
    systemctl enable "${SERVICE_NAME}"
}

print_next_steps() {
    cat <<EOF

Installation complete.

Next steps:
1. Put .mp3, .m4a, or .wav files into:
   ${SCRIPT_DIR}/music

2. Replace the starter image with your own JPG:
   ${SCRIPT_DIR}/assets/background.jpg

3. Edit your YouTube stream key:
   sudo nano ${SCRIPT_DIR}/.env

4. Test playlist generation:
   ${SCRIPT_DIR}/update_playlist.sh

5. Start streaming:
   sudo systemctl start ${SERVICE_NAME}

Useful commands:
   sudo systemctl status ${SERVICE_NAME}
   sudo journalctl -u ${SERVICE_NAME} -f
   sudo systemctl stop ${SERVICE_NAME}

EOF
}

main() {
    require_root
    require_ubuntu
    install_packages
    prepare_files
    install_service
    print_next_steps
}

main "$@"
