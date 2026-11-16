# `stop_omnivoicetts`

`scripts/stop_omnivoicetts` stops OmniVoice workers before running
`scripts/clear_tts_cache`.

It sends TERM, waits up to five seconds, then escalates to KILL and checks
again. If workers remain or process inspection fails, cache cleanup is refused.
Its process match intentionally does not include Pi or Omnews.

`clear_tts_cache` also removes finished Daily Paper TTS worker jobs from
`~/.local/state/daily-paper-tts` (override with `DAILY_PAPER_TTS_WORK_ROOT`).
Only jobs with a `completed` marker go, since the coordinator has already
fetched them; unfinished jobs and the root itself stay, and symlinks are not
followed.

This is an explicit destructive maintenance command. `synchosts` does not run
it.

Focused test:

```sh
python3 -m unittest tests.test_idle_cleanup
```
