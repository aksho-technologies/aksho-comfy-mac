## Working on this repo

- Explain it in plain language: Aksho Comfy is AKSHOAI's Windows installer for a local ComfyUI; this repo, originally written by bdotnet, rebuilds that setup for Apple Silicon Macs.
- Keep Atelier pointed at `127.0.0.1:8188`. ComfyUI itself listens on `127.0.0.1:18188`; `browser_bridge.py` owns 8188 through nginx and accepts both plain HTTP and the HTTPS Safari upgrades that address to.
- A working Atelier connection is a browser check in Safari, Orion, Firefox and Chrome. A terminal request to the server is not enough.

## Facts

- The installed app lives at `~/AkshoComfy` and runs ComfyUI v0.38.0 with Metal PyTorch, checked out at its pinned commit (`COMFY_COMMITS` in `bootstrap_comfy.py`). A manifest naming a release missing from that table stops the install until the table is updated and reviewed. Skip the Windows portable zip and the CUDA wheels; they cannot run on Apple Silicon.
- Assets come from the live manifest at https://dl.akshoai.com and are checked with sha256 before use. Every manifest path must stay inside the install folder, and downloads are HTTPS only.
- Aksho-authored code from the Windows bundle: `extensions/ComfyUI-Aksho-ModelInfo` (`/aksho/checkpoint-clip`), `extensions/gligen-xl` and `agent/aksho-agent.py`. Users do not run `publish/`.
- Leave Z-Image and Krea2 support off: their FP8 text encoders crash on Metal with ComfyUI v0.38.0.
- Packs come in tiers from the manifest: the required core, the base checkpoints (one or more, or none), the model support packs a checkpoint or tool names in `worksWith` (brought along with it), and the tools. A base pack with no components is coming soon and is not offered. `--yes` on a first run installs 2.5D (`YES_BASE`), the checkpoint this port is tested on.
- akshoai.com's CSP carries `upgrade-insecure-requests`, so Safari and Orion send TLS to `127.0.0.1:8188`; Chrome and Firefox do not. The bridge answers TLS with one self-signed certificate for 127.0.0.1 and localhost (`CA:FALSE`, serverAuth), trusted for SSL only. Never go back to a certificate authority: a trusted CA key on disk can vouch for any site. `--uninstall` removes the trust, and the CA earlier versions created is removed wherever it is found.
- The CORS patch in `bootstrap_comfy.py` replaces ComfyUI's middleware at every launch, on a `server.py` restored from git first: only `AKSHO_ORIGINS` and pages served from this machine may call it, every other origin or a foreign Host gets a 403 before the request runs, and the private-network grant goes to the admitted origins only. Never echo an arbitrary Origin and never send `Allow-Credentials`.
