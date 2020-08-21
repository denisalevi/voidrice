#!/bin/sh
# Profile file. Runs on login.

# Adds `~/.scripts` and all subdirectories to $PATH
export PATH="$PATH:$(du "$HOME/.scripts/" | cut -f2 | tr '\n' ':' | sed 's/:*$//')"
export EDITOR="nvim"
export VISUAL="nvim"
export TERMINAL="st"
export BROWSER="firefox"
export ALTBROWSER="chromium"
export READER="zathura"
export FILE="vu"
export BIB="$HOME/Documents/LaTeX/uni.bib"
export REFER="$HOME/Documents/referbib"
export SUDO_ASKPASS="$HOME/.scripts/tools/dmenupass"
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
sudo -n loadkeys ~/.scripts/ttymaps.kmap 2>/dev/null

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

# source gtk scale environmental variables before launching
gtk_application_with_dpi_scaling() {
    # $1 is the application name with all options etc.

    # save GDK_..._SCALE if they are already set
    if [ -n "$GDK_SCALE" ]; then
        GDK_SCALE_OLD=$GDK_SCALE
    fi
    if [ -n "$GDK_DPI_SCALE" ]; then
        GDK_SCALE_DPI_OLD=$GDK_DPI_SCALE
    fi

    cat ~/.gtk-3-scale
    notify-send $(cat ~/.gtk-3-scale)
    source ~/.gtk-3-scale


    # run the application
    "$@"

    # restore previous variables
    if [ -n "$GDK_SCALE_OLD" ]; then
        export GDK_SCALE=$GDK_SCALE_OLD
    else
        unset GDK_SCALE
    fi
    if [ -n "$GDK_DPI_SCALE" ]; then
        export GDK_SCALE_DPI=$GDK_DPI_SCALE_OLD
    else
        unset GDK_DPI_SCALE
    fi
}
alias eclipse='gtk_application_with_dpi_scaling eclipse'
alias inkscape='gtk_application_with_dpi_scaling inkscape'
