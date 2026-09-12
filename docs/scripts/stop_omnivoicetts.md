# `stop_omnivoicetts`

`scripts/stop_omnivoicetts` stops OmniVoice workers before running
`scripts/clear_tts_cache`.

It sends TERM, waits up to five seconds, then escalates to KILL and checks again.
If workers remain or process inspection fails, cache cleanup is refused. Its
process match intentionally does not include Pi or Omnews.

This is an explicit destructive maintenance command. `synchosts` does not run it.

Focused test:

```sh
python3 -m unittest tests.test_idle_cleanup
```
