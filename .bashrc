#!/bin/bash
stty -ixon # Disable ctrl-s and ctrl-q.
shopt -s autocd #Allows you to cd into directory merely by typing the directory name.
HISTSIZE= HISTFILESIZE= # Infinite history.
export PS1="\[$(tput bold)\]\[$(tput setaf 1)\][\[$(tput setaf 3)\]\u\[$(tput setaf 2)\]@\[$(tput setaf 4)\]\h \[$(tput setaf 5)\]\W\[$(tput setaf 1)\]]\[$(tput setaf 7)\]\\$ \[$(tput sgr0)\]"

[ -f "$HOME/.config/shortcutrc" ] && source "$HOME/.config/shortcutrc" # Load shortcut aliases
[ -f "$HOME/.config/aliasrc" ] && source "$HOME/.config/aliasrc"

# activate conda commands
source /etc/profile.d/conda.sh
export CONDA_EXE=/usr/bin/conda

# add local binary folder
export PATH="$PATH:~/.local/bin/"

# add go binary folder
export PATH="$PATH:~/go/bin/"

# set XLA_FLAGS for jax to find cuda install
export XLA_FLAGS=--xla_gpu_cuda_data_dir=/opt/cuda

# wal setup (https://github.com/dylanaraps/pywal/wiki/Getting-Started)
(cat ~/.cache/wal/sequences &)
source ~/.cache/wal/colors-tty.sh
