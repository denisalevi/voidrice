#!/bin/bash

# Parse command line options
QUIET=0
while [[ "$1" =~ ^- ]]; do
    case "$1" in
        -q|--quiet)
            QUIET=1
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

FLAG="$HOME/.cache/backup-nas-last-success"
TODAY=$(date +%F)

# Only run if on home Wi-Fi
SSID=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
if [ "$SSID" = "We-dont-have-WiFi" ]; then
    # Check if backup already ran today
    if [ -f "$FLAG" ] && [ "$(cat $FLAG)" = "$TODAY" ]; then
        echo "Backup already completed today. Exiting."
        exit 0
    fi
    INFO="--info=name0 --info=flist0 --info=progress2"
    if [ "$QUIET" -eq 1 ]; then
        INFO="--quiet"
    fi  
    rsync -avz --delete $INFO \
        --exclude='.cache/' \
        --exclude='Downloads/' \
        --exclude='projects/uwrhorn/uwrhorn-server/docker_server/mosquitto/data' \
        --exclude='projects/uwrhorn/uwrhorn-server/docker_server/mosquitto/log' \
        --exclude='projects/uwrhorn/uwrhorn-server/docker_server/ssl' \
        --exclude='projects/uwrhorn/uwrhorn-server/docker_server/certbot/conf/accounts' \
        --exclude='tmp/var-lib-docker-backup' \
        --exclude='.miracle-sink.history' \
        --exclude='.miracle-wifi.history' \
        "$HOME/" ssh-backups:/mnt/zelos_home/
    if [ $? -ne 0 ]; then
        echo "Backup failed"
        notify-send -u critical "Backup of /home/denis failed"
        exit 1
    fi
    echo "$TODAY" > "$FLAG"
    notify-send "Backup of /home/denis completed successfully"
    exit 0
else
    echo "Not on home Wi-Fi, skipping backup."
    exit 1
fi
