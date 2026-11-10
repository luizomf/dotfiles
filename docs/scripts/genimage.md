# `genimage`

`scripts/genimage` generates one image with a local open model through
[mflux](https://github.com/filipstrand/mflux). It runs where mflux is installed
(`m4128`, via `uv tool install mflux`); on other hosts it runs there over SSH
and copies the PNG back. Set `GENIMAGE_HOST` to use another machine.

```sh
genimage -p "a blue terminal on a desk"                 # Z-Image Turbo, 1280x720
genimage -m qwen -f prompt.txt -o cover.png --seed 42   # Qwen-Image-2512
genimage -m flux3 -f - < prompt.txt -- --steps 20       # extra args go to mflux
```

Models are limited to licenses that allow commercial use: `z-image` (Z-Image
Turbo, Apache 2.0), `qwen` (Qwen-Image-2512, Apache 2.0) and `flux3` (FLUX 3
Image Klein, FLUX Kommunity, free under US$5M yearly revenue). Check the license
before adding another model. Weights download to the Hugging Face cache on the
first run of each model.

## `genimage-server`

`scripts/genimage-server` exposes `genimage` over HTTP on `127.0.0.1` (port
`GENIMAGE_PORT`, default 3790) so sandboxed agents can request images without
SSH access. `POST /generate?model=<name>` takes the prompt as the body and
returns a PNG; `GET /health` returns `ok`. Requests run one at a time.

It runs as a user systemd service on the host that has SSH to the image machine.
A reverse proxy in front of it decides who may reach it; the server itself has
no authentication. Host-specific service and proxy details live in the private
environment notes.
