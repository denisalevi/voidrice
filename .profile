#!/bin/sh
# Profile file. Runs on login.

export PATH="$HOME/.local/bin:$PATH"
export EDITOR="bgcolor_nvim"
export VISUAL="bgcolor_nvim"
export TERMINAL="st"
export BROWSER="firefox"
export ALTBROWSER="chromium"
export READER="zathura"
export FILE="vu"
export BIB="$HOME/$(xdg-user-dir DOCUMENTS)/LaTeX/uni.bib"
export REFER="$HOME/$(xdg-user-dir DOCUMENTS)/referbib"
export SUDO_ASKPASS="$HOME/.local/bin/dmenupass"
export NOTMUCH_CONFIG="$HOME/.config/notmuch-config"
export GTK2_RC_FILES="$HOME/.config/gtk-2.0/gtkrc-2.0"

# less/man colors
export LESS=-R
export LESS_TERMCAP_mb="$(printf '%b' '[1;31m')"; a="${a%_}"
export LESS_TERMCAP_md="$(printf '%b' '[1;36m')"; a="${a%_}"
export LESS_TERMCAP_me="$(printf '%b' '[0m')"; a="${a%_}"
export LESS_TERMCAP_so="$(printf '%b' '[01;44;33m')"; a="${a%_}"
export LESS_TERMCAP_se="$(printf '%b' '[0m')"; a="${a%_}"
export LESS_TERMCAP_us="$(printf '%b' '[1;32m')"; a="${a%_}"
export LESS_TERMCAP_ue="$(printf '%b' '[0m')"; a="${a%_}"

[ ! -f ~/.config/shortcutrc ] && shortcuts >/dev/null 2>&1

echo "$0" | grep "bash$" >/dev/null && [ -f ~/.bashrc ] && source "$HOME/.bashrc"

# Start graphical server if i3 not already running.
[ "$(tty)" = "/dev/tty1" ] && ! pgrep -x i3 >/dev/null && exec startx

# Set caps to excape if tty:
# Denis: It's all handled in ~/.local/bin/remaps now
#sudo -n loadkeys ~/.local/share/ttymaps.kmap 2>/dev/null

# zsh like implementation of precmd: sends bell alarm after command execution
# in TMUX
if [ -f ~/.bash-preexec.sh ]
then
    source ~/.bash-preexec.sh
    precmd() {
        if [ -n "$TMUX" ]
        then
            # -e '\a' sends bell alarm, -n does not print trialing newline
            echo -n -e '\a'
        fi
    }
fi

# scaling script and alias to ~/.local/lib and ~/.local/bin for dmenu
