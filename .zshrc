# Use powerline
USE_POWERLINE="true"
# Source manjaro-zsh-configuration
if [[ -e /usr/share/zsh/manjaro-zsh-config ]]; then
  source /usr/share/zsh/manjaro-zsh-config
fi
# Use manjaro zsh prompt
if [[ -e /usr/share/zsh/manjaro-zsh-prompt ]]; then
  source /usr/share/zsh/manjaro-zsh-prompt
fi
## gruvbox powerline prompt (find something faster..., doubles terminal startup time...)
#powerline-daemon -q
#source /usr/share/powerline/bindings/zsh/powerline.zsh
#source ~/git/gruvbox-zsh/gruvbox.zsh-theme

export PATH="$PATH:$HOME/.local/bin"
export PATH="$PATH:$HOME/.local/bin/i3cmds/"
export PATH="$PATH:$HOME/.local/bin/tools/"

[ -f "$HOME/.config/aliasrc" ] && source "$HOME/.config/aliasrc"
export TERMINAL='st'

# >>> mamba initialize >>>
# !! Contents within this block are managed by 'mamba init' !!
export MAMBA_EXE="/usr/bin/micromamba";
export MAMBA_ROOT_PREFIX="/home/denis/.conda";
__mamba_setup="$('/usr/bin/micromamba' shell hook --shell zsh --prefix '/home/denis/.conda' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    if [ -f "/home/denis/.conda/etc/profile.d/micromamba.sh" ]; then
        . "/home/denis/.conda/etc/profile.d/micromamba.sh"
    else
        export  PATH="/home/denis/.conda/bin:$PATH"  # extra space after export prevents interference from conda init
    fi
fi
unset __mamba_setup
# <<< mamba initialize <<<

# Make gnome keyring with seahorse and ssh-agent via gcr work
export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/keyring/ssh"

export EDITOR=nvim

# zsh-vi-mode plugin
source /usr/share/zsh/plugins/zsh-vi-mode/zsh-vi-mode.plugin.zsh

# Use ipdb as default Python debugger
export PYTHONBREAKPOINT="ipdb.set_trace"

# Set zathura as default PDF viewer
export PDFVIEWER="zathura"
