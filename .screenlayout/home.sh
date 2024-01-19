#!/bin/sh
sh ~/.screenlayout/_only-external-home.sh
sleep 0.1
xrandr --output eDP-1 --mode 1920x1200 --pos 0x240 --rotate normal --output HDMI-1 --primary --mode 2560x1440 --pos 1920x0 --rotate normal --output DP-1 --off --output DP-2 --off --output DP-3 --off --output DP-4 --off
scaledpi 2
sleep 0.1
~/.local/bin/remaps
feh --bg-fill /home/denis/pictures/wallpapers/Landscapes/1490458801251.jpg
