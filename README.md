# Aksho Comfy for Mac

One-click local image generation for [AKSHOAI's Atelier](https://akshoai.com/atelier) on Apple Silicon Macs. This is the Mac port of [Aksho Comfy](https://github.com/aksho-technologies/aksho-comfy), originally written by **bdotnet**: the same ComfyUI release, the same checkpoints and the same Atelier add-ons, with Apple's Metal build of PyTorch in place of the Windows CUDA build.

## Requirements

- An Apple Silicon Mac (M1 or later). Intel Macs are not supported.
- macOS 13 or later
- 16 GB of memory is a practical minimum for Dreamhex (SDXL) with image reference. More is better.
- About 20 GB free for a starter set (Core, 2.5D, Illustrious support, 3D Poser and Inpaint) plus ComfyUI and PyTorch, up to about 70 GB more with every pack ticked
- [Homebrew](https://brew.sh), then in Terminal: `brew install uv git nginx`

## Install

1. Download `aksho-comfy-mac.zip` from this repository's Releases and unzip it.
2. Double-click `Install Aksho Comfy.command`.
3. Pick at least one base checkpoint by number (2.5D is the one this port is tested on), or 0 to bring your own. Each checkpoint brings the model support it runs on. Leave Z-Image and Krea2 support off (see below), then pick the tools you want.
4. Wait for the downloads. The default folder is `~/AkshoComfy`.
5. ComfyUI starts and Atelier opens: choose the **Local** provider and connect to `127.0.0.1:8188`.

> **macOS note:** the first time, macOS may say the file "cannot be opened because it is from an unidentified developer". Right-click it, choose **Open**, then **Open** again. The installer is a set of small, readable scripts; open them in TextEdit to see everything they do.

From then on, start everything with `Run Aksho ComfyUI.command` in `~/AkshoComfy`. Add packs later with `Update Aksho ComfyUI.command`. `Run Aksho Agent.command` starts the optional relay agent, so Atelier can reach this ComfyUI when you are away from this Mac.

An install from Terminal with no questions, without opening ComfyUI at the end. `--yes` alone installs the 2.5D checkpoint and its tools; `--packs` names packs instead (each brings the model support it runs on, and no `base-` pack means you bring your own checkpoint):

```bash
python3 install.py --yes --packs base-2-5d,inpaint --no-launch
```

## What's in the box

The packs are the ones the Windows installer offers, from the same manifest, every file checked against its sha256 before it is used.

| Pack | On a Mac |
|---|---|
| Core | The model-info route and the relay agent. Always installed. |
| 2.5D, with Illustrious support | Dreamhex, image reference, face and hand cleanup and the upscaler. The path Atelier generates with on a Mac today. Face detection may run on the CPU, which is fine. |
| 3D Poser, Inpaint, Anima support | The same files as on Windows. |
| All in One, MOSS support | The same files as on Windows, not yet tested on a Mac. |
| Z-Image, Krea2 support | Leave these off. Their FP8 text encoders crash on Metal with ComfyUI v0.38.0 (`Float8_e4m3fn`). |

Drop extra checkpoints, LoRAs or upscalers into the matching `~/AkshoComfy/ComfyUI/models/` folders. Atelier picks them up through the model-info route.

## How Atelier reaches it

ComfyUI listens on `127.0.0.1:18188`, on this Mac only. A small nginx proxy owns `127.0.0.1:8188`, the address Atelier calls, and passes plain connections straight through.

- **Only the AKSHOAI sites can use it from a browser.** ComfyUI is patched at every launch to admit akshoai.com, testing-akshoai.com and pages served from this Mac, and to refuse every other website before its request runs. No other page you visit can queue work on your Mac or read your images.
- **Safari gets a local certificate.** akshoai.com asks browsers to upgrade insecure requests, so Safari turns `http://127.0.0.1` into `https://127.0.0.1`. The installer makes one self-signed certificate for `127.0.0.1` and `localhost` and asks macOS to trust it for SSL. It is not a certificate authority: it cannot vouch for any other site, even if its key were read. Chrome and Firefox do not need it.

ComfyUI runs pinned to the exact commit of its release (v0.38.0), and the installer refuses any other.

## Uninstall

1. Double-click `Uninstall Aksho ComfyUI.command`. It stops the proxy and takes the local certificate out of your keychain.
2. Delete `~/AkshoComfy`.

Nothing else is left behind apart from the uv, pip and git caches every Python install keeps.

## Credits

The Mac port was written by **bdotnet** and contributed to AKSHOAI. See [LICENSES.md](LICENSES.md) for the projects and models the bundle downloads.
