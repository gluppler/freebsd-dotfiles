# Login environment only; graphical startup belongs to the Wayland session.
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"
export XDG_DATA_HOME="$HOME/.local/share"
export LANG=en_US.UTF-8
export EDITOR=vis VISUAL=vis TERMINAL=foot BROWSER=nostromo-browser
export NNN_OPENER=nostromo-open
export SHELL=/usr/local/bin/oksh ENV="$HOME/.config/oksh/okshrc"
export CC=/usr/bin/clang CXX=/usr/bin/clang++
export UV_PYTHON_DOWNLOADS=never
export PASSWORD_STORE_DIR="$HOME/.password-store" PASSWORD_STORE_CLIP_TIME=45
export PASSWORD_STORE_UMASK=077
export PAGER=less LESS='-iMR'
# A trailing colon preserves the system manual search path.
export MANPATH="$HOME/.local/share/man${MANPATH:+:$MANPATH}:"
export FZF_DEFAULT_COMMAND='rg --files --hidden -g !.git'
export FZF_DEFAULT_OPTS='--layout=reverse --border=sharp --color=bw --height=70%'
