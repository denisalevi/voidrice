# Denis' dotfiles

1. Clone [my fork](https://github.com/denisalevi/dotfiles.sh) of `dotfiles.sh` from Eli Schwarz.
  ```
  mkdir ~/git
  git clone git@github.com:denisalevi/dotfiles.sh.git ~/git/dotfiles.sh
  ```
2. Install `dotfiles.sh`:
   - Arch: `cd ~/git/dotfiles.sh && makepkg -sri`
   - Other distros: `cd ~/git/dotfiles.sh && make install` (or probably `sudo make install`)
3. Clone this dotfiles repo using the `dotfiles` command installed by `dotfiles.sh`
   ```
   dotfiles clone git@github.com:denisalevi/voidrice.git ~/git/dotfiles
   ```
   - This clones this dotfiles repo as bare git repository into `~/git/dotfiles` and sets its working directory to `~`. It also takes care of doing a spasce checkout (`README`, `LICENCE`, `.gitignore`, `.gitattributes` are not checked out, avoiding cluttering of `$HOME`). To use git commands on the config files in `$HOME`, use `dotfiles` instead of `git`. Run `dotfiles --help` or read the README in [dotfiles.sh](https://github.com/denisalevi/dotfiles.sh) for additional commands implemented by `dotfiles`.
   - My fork of `dotfiles.sh` adds this feature: During the `dotfiles clone` command, any configuration files already present on the system are commited to a local `backup-before-clone` branch and are then replaced with any config files in the `~/git/dotfiles` repository (`master` branch). If you want to compare the two, open `nvim`, install all plugins with `:PlugInstall` and open a diff view of the dotfiles repository via `:DiffviewOpen backup-before-clone`.

## Dotfile management
The repo could be used as a git repo in $HOME. But for now I use
[dotbot](https://github.com/anishathalye/dotbot?tab=readme-ov-file#getting-started).
Just install via `yay -S dotbot` or via `pip`. Then run `dotbot -c
/path/to/dotbot.conf.yaml` to install the dotfiles.

# Old README from Luke's GNU/Linux Dotfiles

These are my dotfiles! The name of the repo, "voidrice", came from the fact they were originally on my Void Linux machine, but these files are distro-independent. In fact, I now push changes from my X200 running Parabola or my X220 running Arch.

## Programs whose configs can be found here

+ i3 (i3-gaps)
+ Xresourses info used by [my st build](https://github.com/lukesmithxyz/st) as a terminal
+ vim
+ bash
+ ranger (see full documentation [here](.config/ranger/luke_ranger_readme.md))
+ ~~mutt/msmtp/offlineimap~~ Now moved to [LukeSmithxyz/mutt-wizard](https://github.com/LukeSmithxyz/mutt-wizard)
+ calcurse
+ ncmpcpp and mpd (my main music player)
+ mpv
+ neofetch
+ And many little scripts I use filed in the `~/.scripts/` directory

## More documentation

There's a full .pdf write-up of the repository [here: https://larbs.xyz/larbs_readme.pdf](https://larbs.xyz/larbs_readme.pdf).

Or, if you actually installed my dotfiles, you can just press `Super+F1` to
show the same document offline.

In the system, you can also press `Super+Shift+e` to watch tutorial videos on
different programs used. See [my YouTube channel](https://youtube.com/c/LukeSmithxyz) for more.

The command `getkeys` will also show basic key binds for different programs.

## Dynamic Configuration Files

Store your favorite or high-traffic directories in `~/.config/bmdirs` or your most
important config files in `~/.config/bmfiles` with keyboard shortcuts. When you add
things to theses files my vimrc will automatically run `shortcuts` which will
dynamically generate shortcuts for these in bash, ranger and optionally
qutebrowser and fish.

## Like my rice?

Feel free to add other suggestions and I may implement them.

I have a job, but every penny I get from followers or subscribers is more incentive to perfect what I'm doing.
You can donate to me at [https://paypal.me/LukeMSmith](https://paypal.me/LukeMSmith).
Donations are earmarked for whatever the donator wants, usually to go to funds for buying new equipment for the [YouTube channel](https://youtube.com/c/LukeSmithxyz).

# "Dependencies" and programs used

The programs I use here are always changing, but luckily you can just look at the installation list for [LARBS](http://larbs.xyz) here:

+ [List of programs installed by LARBS, including optional packages](https://github.com/LukeSmithxyz/LARBS/blob/master/progs.csv)

`A` marks programs in the AUR, `G` marks git repositories.
