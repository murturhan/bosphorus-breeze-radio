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
# - Installs the systemd services.
# - Enables auto start on reboot.
#
# Run from the repository directory:
#   sudo ./install.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="bosphorus-radio.service"
ADMIN_SERVICE_NAME="bosphorus-radio-admin.service"
SERVICE_SOURCE="${SCRIPT_DIR}/systemd/${SERVICE_NAME}"
ADMIN_SERVICE_SOURCE="${SCRIPT_DIR}/systemd/${ADMIN_SERVICE_NAME}"
SERVICE_TARGET="/etc/systemd/system/${SERVICE_NAME}"
ADMIN_SERVICE_TARGET="/etc/systemd/system/${ADMIN_SERVICE_NAME}"
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
    if [[ -f "${SCRIPT_DIR}/test_local.sh" ]]; then
        chmod +x "${SCRIPT_DIR}/test_local.sh"
    fi
    if [[ -f "${SCRIPT_DIR}/radio_admin.py" ]]; then
        chmod +x "${SCRIPT_DIR}/radio_admin.py"
    fi

    if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
        log "Creating .env from .env.example."
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        chmod 600 "${SCRIPT_DIR}/.env"
        log "Use the web admin panel or edit ${SCRIPT_DIR}/.env before streaming."
    else
        log ".env already exists; leaving it unchanged."
    fi
}

install_service() {
    [[ -f "${SERVICE_SOURCE}" ]] || fail "Missing systemd service file: ${SERVICE_SOURCE}"

    log "Installing stream service: ${SERVICE_TARGET}"
    cp "${SERVICE_SOURCE}" "${SERVICE_TARGET}"
    sed -i "s|/opt/bosphorus-breeze-radio|${SCRIPT_DIR}|g" "${SERVICE_TARGET}"

    if [[ -f "${ADMIN_SERVICE_SOURCE}" ]]; then
        log "Installing admin panel service: ${ADMIN_SERVICE_TARGET}"
        cp "${ADMIN_SERVICE_SOURCE}" "${ADMIN_SERVICE_TARGET}"
        sed -i "s|/opt/bosphorus-breeze-radio|${SCRIPT_DIR}|g" "${ADMIN_SERVICE_TARGET}"
    fi

    log "Reloading systemd."
    systemctl daemon-reload

    log "Enabling stream auto start on reboot."
    systemctl enable "${SERVICE_NAME}"

    if [[ -f "${ADMIN_SERVICE_TARGET}" ]]; then
        log "Enabling admin panel auto start on reboot."
        systemctl enable "${ADMIN_SERVICE_NAME}"
    fi
}

print_next_steps() {
    cat <<EOF

Installation complete.

Useful commands:
   sudo systemctl start ${ADMIN_SERVICE_NAME}
   sudo systemctl status ${SERVICE_NAME}
   sudo journalctl -u ${SERVICE_NAME} -f
   sudo systemctl stop ${SERVICE_NAME}

Web admin panel:
   1. Start the admin panel service:
      sudo systemctl start ${ADMIN_SERVICE_NAME}

   2. From your own computer, open an SSH tunnel:
      ssh -L 8788:127.0.0.1:8788 ubuntu@YOUR_SERVER_IP

   3. Open this in your browser:
      http://127.0.0.1:8788

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
