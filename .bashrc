#
# ~/.bashrc
#

### FROM EOS INSTALL (2022/2023?)
# If not running interactively, don't do anything
[[ $- != *i* ]] && return

[[ -f ~/.welcome_screen ]] && . ~/.welcome_screen

_set_liveuser_PS1() {
    PS1='[\u@\h \W]\$ '
    if [ "$(whoami)" = "liveuser" ] ; then
        local iso_version="$(grep ^VERSION= /usr/lib/endeavouros-release 2>/dev/null | cut -d '=' -f 2)"
        if [ -n "$iso_version" ] ; then
            local prefix="eos-"
            local iso_info="$prefix$iso_version"
            PS1="[\u@$iso_info \W]\$ "
        fi
    fi
}
_set_liveuser_PS1
unset -f _set_liveuser_PS1

ShowInstallerIsoInfo() {
    local file=/usr/lib/endeavouros-release
    if [ -r $file ] ; then
        cat $file
    else
        echo "Sorry, installer ISO info is not available." >&2
    fi
}


alias ls='ls --color=auto'
alias ll='ls -lav --ignore=..'   # show long listing of all except ".."
alias l='ls -lav --ignore=.?*'   # show long listing but no hidden dotfiles except "."

[[ "$(whoami)" = "root" ]] && return

[[ -z "$FUNCNEST" ]] && export FUNCNEST=100          # limits recursive functions, see 'man bash'

## Use the up and down arrow keys for finding a command in history
## (you can write some initial letters of the command first).
#bind '"\e[A":history-search-backward'
#bind '"\e[B":history-search-forward'

################################################################################
## Some generally useful functions.
## Consider uncommenting aliases below to start using these functions.
##
## October 2021: removed many obsolete functions. If you still need them, please look at
## https://github.com/EndeavourOS-archive/EndeavourOS-archiso/raw/master/airootfs/etc/skel/.bashrc

_open_files_for_editing() {
    # Open any given document file(s) for editing (or just viewing).
    # Note1:
    #    - Do not use for executable files!
    # Note2:
    #    - Uses 'mime' bindings, so you may need to use
    #      e.g. a file manager to make proper file bindings.

    if [ -x /usr/bin/exo-open ] ; then
        echo "exo-open $@" >&2
        setsid exo-open "$@" >& /dev/null
        return
    fi
    if [ -x /usr/bin/xdg-open ] ; then
        for file in "$@" ; do
            echo "xdg-open $file" >&2
            setsid xdg-open "$file" >& /dev/null
        done
        return
    fi

    echo "$FUNCNAME: package 'xdg-utils' or 'exo' is required." >&2
}

#------------------------------------------------------------

## Aliases for the functions above.
## Uncomment an alias if you want to use it.
##

alias ef='_open_files_for_editing'     # 'ef' opens given file(s) for editing
# alias pacdiff=eos-pacdiff
################################################################################


### MERGED FROM LARBS INSTALL (~2019)
stty -ixon # Disable ctrl-s and ctrl-q.
#HISTSIZE= HISTFILESIZE= # Infinite history.
#export PS1="\[$(tput bold)\]\[$(tput setaf 1)\][\[$(tput setaf 3)\]\u\[$(tput setaf 2)\]@\[$(tput setaf 4)\]\h \[$(tput setaf 5)\]\W\[$(tput setaf 1)\]]\[$(tput setaf 7)\]\\$ \[$(tput sgr0)\]"

# Eternal bash history.
# ---------------------
# Undocumented feature which sets the size to "unlimited".
# http://stackoverflow.com/questions/9457233/unlimited-bash-history
export HISTFILESIZE=
export HISTSIZE=
export HISTTIMEFORMAT="[%F %T] "
# Change the file location because certain bash sessions truncate .bash_history file upon close.
# http://superuser.com/questions/575479/bash-history-truncated-to-500-lines-on-each-login
export HISTFILE=~/.bash_eternal_history
# Force prompt to write history after every command.
# http://superuser.com/questions/20900/bash-history-loss
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

[ -f "$HOME/.config/shortcutrc" ] && source "$HOME/.config/shortcutrc" # Load shortcut aliases
[ -f "$HOME/.config/aliasrc" ] && source "$HOME/.config/aliasrc"


### MERGED FROM MANJARO INSTALL (end of 2022?)
# commented out most settings, maybe check the shopt settings?
colors() {
	local fgc bgc vals seq0

	printf "Color escapes are %s\n" '\e[${value};...;${value}m'
	printf "Values 30..37 are \e[33mforeground colors\e[m\n"
	printf "Values 40..47 are \e[43mbackground colors\e[m\n"
	printf "Value  1 gives a  \e[1mbold-faced look\e[m\n\n"

	# foreground colors
	for fgc in {30..37}; do
		# background colors
		for bgc in {40..47}; do
			fgc=${fgc#37} # white
			bgc=${bgc#40} # black

			vals="${fgc:+$fgc;}${bgc}"
			vals=${vals%%;}

			seq0="${vals:+\e[${vals}m}"
			printf "  %-9s" "${seq0:-(default)}"
			printf " ${seq0}TEXT\e[m"
			printf " \e[${vals:+${vals+$vals;}}1mBOLD\e[m"
		done
		echo; echo
	done
}

[ -r /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion

# Change the window title of X terminals
case ${TERM} in
	xterm*|rxvt*|Eterm*|aterm|kterm|gnome*|interix|konsole*)
		PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME%%.*}:${PWD/#$HOME/\~}\007"'
		;;
	screen*)
		PROMPT_COMMAND='echo -ne "\033_${USER}@${HOSTNAME%%.*}:${PWD/#$HOME/\~}\033\\"'
		;;
esac

#use_color=true
#
## Set colorful PS1 only on colorful terminals.
## dircolors --print-database uses its own built-in database
## instead of using /etc/DIR_COLORS.  Try to use the external file
## first to take advantage of user additions.  Use internal bash
## globbing instead of external grep binary.
#safe_term=${TERM//[^[:alnum:]]/?}   # sanitize TERM
#match_lhs=""
#[[ -f ~/.dir_colors   ]] && match_lhs="${match_lhs}$(<~/.dir_colors)"
#[[ -f /etc/DIR_COLORS ]] && match_lhs="${match_lhs}$(</etc/DIR_COLORS)"
#[[ -z ${match_lhs}    ]] \
#	&& type -P dircolors >/dev/null \
#	&& match_lhs=$(dircolors --print-database)
#[[ $'\n'${match_lhs} == *$'\n'"TERM "${safe_term}* ]] && use_color=true
#
#if ${use_color} ; then
#	# Enable colors for ls, etc.  Prefer ~/.dir_colors #64489
#	if type -P dircolors >/dev/null ; then
#		if [[ -f ~/.dir_colors ]] ; then
#			eval $(dircolors -b ~/.dir_colors)
#		elif [[ -f /etc/DIR_COLORS ]] ; then
#			eval $(dircolors -b /etc/DIR_COLORS)
#		fi
#	fi
#
#	if [[ ${EUID} == 0 ]] ; then
#		PS1='\[\033[01;31m\][\h\[\033[01;36m\] \W\[\033[01;31m\]]\$\[\033[00m\] '
#	else
#		PS1='\[\033[01;32m\][\u@\h\[\033[01;37m\] \W\[\033[01;32m\]]\$\[\033[00m\] '
#	fi
#
#	alias ls='ls --color=auto'
#	alias grep='grep --colour=auto'
#	alias egrep='egrep --colour=auto'
#	alias fgrep='fgrep --colour=auto'
#else
#	if [[ ${EUID} == 0 ]] ; then
#		# show root@ when we don't have colors
#		PS1='\u@\h \W \$ '
#	else
#		PS1='\u@\h \w \$ '
#	fi
#fi
#
#unset use_color safe_term match_lhs sh
#
##alias cp="cp -i"                          # confirm before overwriting something
##alias df='df -h'                          # human-readable sizes
##alias free='free -m'                      # show sizes in MB
##alias np='nano -w PKGBUILD'
##alias more=less
#
#xhost +local:root > /dev/null 2>&1
#
## Bash won't get SIGWINCH if another process is in the foreground.
## Enable checkwinsize so that bash will check the terminal size when
## it regains control.  #65623
## http://cnswww.cns.cwru.edu/~chet/bash/FAQ (E11)
#shopt -s checkwinsize
#
#shopt -s expand_aliases
#
## export QT_SELECT=4
#
## Enable history appending instead of overwriting.  #139609
# Denis: Without it, history is kept in memory and written to file at the end
# of a bash session. If you use multiple bash instances in parallel, the
# history file only contains the contents of the last exiting shell.
shopt -s histappend

#
# # ex - archive extractor
# # usage: ex <file>
ex ()
{
  if [ -f $1 ] ; then
    case $1 in
      *.tar.bz2)   tar xjf $1   ;;
      *.tar.gz)    tar xzf $1   ;;
      *.bz2)       bunzip2 $1   ;;
      *.rar)       unrar x $1     ;;
      *.gz)        gunzip $1    ;;
      *.tar)       tar xf $1    ;;
      *.tbz2)      tar xjf $1   ;;
      *.tgz)       tar xzf $1   ;;
      *.zip)       unzip $1     ;;
      *.Z)         uncompress $1;;
      *.7z)        7z x $1      ;;
      *.xz)        unxz $1      ;;
      *)           echo "'$1' cannot be extracted via ex()" ;;
    esac
  else
    echo "'$1' is not a valid file"
  fi
}


### MANUALLY ADDED

# set XLA_FLAGS for jax to find cuda install
export XLA_FLAGS=--xla_gpu_cuda_data_dir=/opt/cuda

export PATH="$PATH":~/.local/bin
export MAMBA_ROOT_PREFIX="~/.conda"

export OPENAI_API_KEY="$(cat ~/.config/openai.key)"
export ANTHROPIC_API_KEY="$(cat ~/.config/anthropic.key)"
export TAVILY_API_KEY="$(cat ~/.config/tavily.key)"

## wal setup (https://github.com/dylanaraps/pywal/wiki/Getting-Started)
#(cat ~/.cache/wal/sequences &)
#source ~/.cache/wal/colors-tty.sh
## added this to set LS_COLORS, which fd needs for colored output
#source ~/.cache/wal/colors.sh

# tab-completion for tmuxp
# install python-shtab before tmuxp (via pacman) to get tab completion

# >>> mamba initialize >>>
# !! Contents within this block are managed by 'mamba init' !!
export MAMBA_EXE='/usr/bin/micromamba';
export MAMBA_ROOT_PREFIX='/home/denis/.conda';
__mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__mamba_setup"
else
    alias micromamba="$MAMBA_EXE"  # Fallback on help from mamba activate
fi
unset __mamba_setup
# <<< mamba initialize <<<

# ssh-agent, copied from https://wiki.archlinux.org/title/SSH_keys#ssh-agent
if ! pgrep -u "$USER" ssh-agent > /dev/null; then
    ssh-agent -t 1h > "$XDG_RUNTIME_DIR/ssh-agent.env"
fi
if [[ ! -f "$SSH_AUTH_SOCK" ]]; then
    source "$XDG_RUNTIME_DIR/ssh-agent.env" >/dev/null
fi
