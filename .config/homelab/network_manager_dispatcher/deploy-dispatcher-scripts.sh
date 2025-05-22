#!/bin/bash
# deploy-dispatcher-scripts.sh

SRC_DIR="$HOME/.config/homelab/network_manager_dispatcher"

for SRC in "$SRC_DIR"/*; do
    if [ -f "$SRC" ]; then
        # ignore this script here, use $0 to get the script name
        if [[ "$SRC" == *"$0"* ]]; then
            echo "Skipping install script $SRC"
            continue
        fi

        # Ask user if script should be installed
        echo "Do you want to install the script: $SRC? (y/n)"
        read -r answer
        if [[ ! $answer =~ ^[Yy]$ ]]; then
            echo "Skipping $SRC"
            continue
        fi
        # Check if destionation file exists and ask before overwriting
        if [ -e "/etc/NetworkManager/dispatcher.d/$(basename "$SRC")" ]; then
            echo "File /etc/NetworkManager/dispatcher.d/$SRC already exists. Do you want to overwrite it? (y/n)"
            read -r answer
            if [[ ! $answer =~ ^[Yy]$ ]]; then
                echo "Skipping $SRC"
                continue
            fi
        fi

        DEST="/etc/NetworkManager/dispatcher.d/$(basename "$SRC")"
        echo "Installing $SRC to $DEST"
        sudo install -m 755 "$SRC" "$DEST"
    fi
done
