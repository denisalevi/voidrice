#!/bin/sh

xrandr --output eDP-1 --primary --mode 1920x1200 --pos 1920x0 --rotate normal \
       --output HDMI-1 --off \
       --output DP-1 --mode 1920x1200 --pos 0x0 --rotate normal \
       --output DP-2 --off \
       --output DP-3 --off \
       --output DP-4 --off
scaledpi 2

touch_device='Silicon Integrated System Co. SiS HID Touch Controller'

xinput map-to-output "$touch_device" DP-1
