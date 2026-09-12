# `clear_sannux_transients`

`scripts/clear_sannux_transients` removes eligible disposable Sannux agent homes.
It never stops consumers and refuses cleanup when matching processes or containers
are active.

A normal run is a preview:

```sh
clear_sannux_transients
```

Deletion requires both explicit flags after confirming all work and publication
continuations are idle:

```sh
clear_sannux_transients --apply --idle-confirmed
```

The command preserves persistent homes, unexpected entries, and the session
directory. It also refuses symlinked, foreign, mounted, changed, or otherwise
ambiguous trees.

Focused test:

```sh
python3 -m unittest tests.test_idle_cleanup
```
