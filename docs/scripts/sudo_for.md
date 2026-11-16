# `sudo_for`

`scripts/sudo_for` grants passwordless sudo to the current user for a limited
time, for example while an agent needs root for a task.

```sh
sudo_for 10m       # grant or extend (s, m or h; a plain number is seconds)
sudo_for --status  # show the expiry
sudo_for --revoke  # remove it now
```

The grant lives in its own file, `/etc/sudoers.d/zz-sudo-for-$USER`, so other
sudoers files are never edited. It is validated with `visudo -cf` before it goes
live. A background root timer removes it at expiry; each grant carries a token,
so running `sudo_for` again extends it without the older timer cutting it short.

A reboot before expiry kills the timer and leaves the grant in place. Run
`sudo_for --revoke` after rebooting in that window.

Focused test:

```sh
python3 -m unittest tests.test_sudo_for
```
