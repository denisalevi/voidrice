#!/bin/sh
sh ~/.screenlayout/_only-external-work.sh
sleep 0.1
xrandr --output eDP-1 --mode 1920x1200 --pos 3840x1390 --rotate normal --output HDMI-1 --off --output DP-1 --off --output DP-2 --off --output DP-3 --primary --mode 3840x2160 --pos 0x0 --rotate normal --output DP-4 --off
scaledpi 4
sleep 0.1
~/.local/bin/remaps
feh --bg-fill /home/denis/pictures/wallpapers/Landscapes/1490458801251.jpg
