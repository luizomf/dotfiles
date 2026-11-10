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
