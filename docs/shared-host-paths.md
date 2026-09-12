# Shared host paths

`config/paths.sh` is the source of truth for shared host paths used by shells and
unattended scripts. Its default is:

```sh
PROJECTS_DIR="$HOME/Desktop/tutoriais_e_cursos"
```

Supported callers load a machine-specific file from `OM_PATHS_FILE`.
`scripts/omnivoice_m4128_half` also accepts `OMNIVOICE_REMOTE_APP`.

On macOS, Zsh adds Apple Silicon Homebrew paths and native-build flags. Linux
keeps inherited build flags and does not substitute Linuxbrew libraries globally.
Existing shells and unattended processes are not reloaded when these files
change, and Queue jobs may have a different PATH from interactive terminals.
