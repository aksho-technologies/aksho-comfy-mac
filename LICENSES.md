# Credits and Licenses

The Mac port was written by **bdotnet** and contributed to AKSHOAI. The installer scripts in this repository are MIT licensed (see [LICENSE](LICENSE)).

The Aksho-authored pieces the installer downloads (the model-info route, the gligen-xl loader and the relay agent) come from [Aksho Comfy](https://github.com/aksho-technologies/aksho-comfy) and share its MIT license.

The ComfyUI release, the custom nodes and the models the bundle downloads are third-party projects, each under its own license. They are the same files the Windows installer downloads; see [Aksho Comfy's credits and licenses](https://github.com/aksho-technologies/aksho-comfy/blob/main/LICENSES.md) for the full list.

On a Mac the installer also uses, without redistributing them:

| Tool | Project | License |
|---|---|---|
| PyTorch (Metal build) | PyTorch Foundation | BSD-3-Clause |
| uv | Astral | Apache-2.0 / MIT |
| nginx | F5 / nginx | BSD-2-Clause |
