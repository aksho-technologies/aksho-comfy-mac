#!/usr/bin/env python3
# Aksho Comfy for Mac, originally written by bdotnet. MIT licensed, see LICENSE.
"""Install the Mac ComfyUI runtime into an Aksho Comfy folder.

The Windows bundle downloads comfyui-portable.zip (embedded CPython plus a
CUDA build of PyTorch). That zip does not run on Apple Silicon. This module
checks out the same ComfyUI tag and installs the normal macOS PyTorch wheel,
which uses Metal (MPS).
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMFY_REPO = "https://github.com/Comfy-Org/ComfyUI.git"
PYTHON_VERSION = "3.13"

# Each ComfyUI release this installer accepts, pinned to its exact commit: a
# tag can be moved, a commit cannot. The Windows bundle pins the same release
# by its zip's sha256 in the manifest; a manifest naming a release missing
# here stops the install until this table is updated and reviewed.
COMFY_COMMITS = {
    "v0.38.0": "6b747c0428c343e1417219641db93a4fb7cb69ae",
}

# The sites allowed to call this ComfyUI from a browser, besides pages served
# from this machine itself. Every other web page is refused.
AKSHO_ORIGINS = ("https://akshoai.com", "https://testing-akshoai.com", "http://localhost:3000")


def info(message: str) -> None:
    print(f"[AKSHO COMFY] {message}", flush=True)


def die(message: str) -> None:
    print(f"[AKSHO COMFY] ERROR: {message}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def require_apple_silicon() -> None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        die("This installer is for Apple Silicon Macs (M1 or later).")


def require_tool(name: str, hint: str) -> str:
    found = shutil.which(name)
    if not found:
        die(f"Could not find `{name}` on PATH. {hint}")
    return found


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        die(f"Command failed ({result.returncode}): {' '.join(command)}")


def venv_python(root: Path) -> Path:
    return root / ".venv" / "bin" / "python"


def ensure_venv(root: Path) -> Path:
    python = venv_python(root)
    if python.exists():
        return python
    uv = require_tool("uv", "Install it from https://docs.astral.sh/uv/getting-started/installation/")
    info(f"Creating a Python {PYTHON_VERSION} environment...")
    run([uv, "venv", "--python", PYTHON_VERSION, str(root / ".venv")])
    if not python.exists():
        die(f"uv did not create {python}")
    return python


def installed_comfy_version(comfy_dir: Path) -> str:
    stamp = comfy_dir / ".aksho-version"
    if not stamp.is_file():
        return ""
    return stamp.read_text(encoding="utf-8").strip()


def ensure_comfy(root: Path, source_version: str) -> None:
    """Check out ComfyUI without touching models or custom nodes.

    Those directories are untracked (ComfyUI gitignores them), so a later
    tag checkout keeps weights the installer already downloaded.
    """
    dest = root / "ComfyUI"
    if dest.is_dir() and (dest / "main.py").is_file() and installed_comfy_version(dest) == source_version:
        info(f"ComfyUI {source_version} is already present.")
        patch_browser_cors(dest)
        return
    if dest.exists() and not (dest / ".git").is_dir():
        die(f"{dest} exists but is not a ComfyUI git checkout. Move that folder aside and run the installer again.")

    commit = COMFY_COMMITS.get(source_version)
    if not commit or not re.fullmatch(r"v\d+\.\d+\.\d+", source_version):
        die(f"This installer does not know ComfyUI {source_version!r} yet. Download the newest installer and run it again.")

    git = require_tool("git", "Install the Xcode command line tools, or Homebrew git.")
    if not dest.exists():
        info(f"Cloning ComfyUI {source_version}...")
        run([git, "clone", "--depth", "1", "--branch", source_version, "--", COMFY_REPO, str(dest)])
    else:
        info(f"Updating ComfyUI to {source_version}...")
        # The launch patch edits server.py; put it back before moving on.
        run([git, "checkout", "--", "server.py"], cwd=dest)
        run([git, "fetch", "--depth", "1", "origin", "tag", source_version], cwd=dest)
        run([git, "checkout", "--detach", source_version], cwd=dest)
    head = subprocess.run([git, "rev-parse", "HEAD"], cwd=dest, capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != commit:
        die(f"ComfyUI {source_version} did not check out at its pinned commit {commit[:12]}. The download was refused.")
    (dest / ".aksho-version").write_text(source_version + "\n", encoding="utf-8")
    patch_browser_cors(dest)


def pip_install(python: Path, packages: list[str]) -> None:
    if not packages:
        return
    uv = require_tool("uv", "Install it from https://docs.astral.sh/uv/getting-started/installation/")
    run([uv, "pip", "install", "--python", str(python), *packages])


def install_runtime_packages(python: Path, comfy_dir: Path) -> None:
    # PyPI's macOS torch wheel is the Metal build. Do not pass a CUDA index.
    info("Installing PyTorch for Apple Silicon...")
    pip_install(python, ["torch", "torchvision"])
    info("Installing ComfyUI's Python packages. The first run takes a while...")
    pip_install(python, ["-r", str(comfy_dir / "requirements.txt")])


CORS_ORIGINAL = """def create_cors_middleware(allowed_origin: str):
    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        if request.method == "OPTIONS":
            # Pre-flight request. Reply successfully:
            response = web.Response()
        else:
            response = await handler(request)

        response.headers['Access-Control-Allow-Origin'] = allowed_origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    return cors_middleware
"""

CORS_GUARDED = """def create_cors_middleware(allowed_origin: str):
    # Aksho: a browser may call this server only from the Aksho sites or from a
    # page on this machine. Anything else is refused before the request runs,
    # so a web page can neither queue work here nor read what comes back. A
    # Host that is not this machine (DNS rebinding) is refused the same way.
    aksho_origins = AKSHO_ORIGINS_PLACEHOLDER
    loopback = ("127.0.0.1", "localhost", "::1")

    def origin_allowed(origin):
        if origin is None:
            return True
        if origin in aksho_origins:
            return True
        parsed = urllib.parse.urlparse(origin)
        return parsed.scheme in ("http", "https") and parsed.hostname in loopback

    def host_allowed(host):
        if host is None:
            return False
        return urllib.parse.urlsplit("//" + host.lower()).hostname in loopback

    @web.middleware
    async def cors_middleware(request: web.Request, handler):
        origin = request.headers.get("Origin")
        if not host_allowed(request.headers.get("Host")) or not origin_allowed(origin):
            logging.warning("Aksho: refused a browser request from origin %s, host %s", origin, request.headers.get("Host"))
            return web.Response(status=403)
        if request.method == "OPTIONS":
            response = web.Response()
        else:
            response = await handler(request)
        if origin is not None:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT, OPTIONS, PATCH'
            requested = request.headers.get("Access-Control-Request-Headers")
            response.headers['Access-Control-Allow-Headers'] = requested or 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Private-Network'] = 'true'
        return response

    return cors_middleware
""".replace("AKSHO_ORIGINS_PLACEHOLDER", repr(AKSHO_ORIGINS))

WS_ORIGINAL = """            ws = web.WebSocketResponse()
            await ws.prepare(request)"""

WS_GUARDED = """            ws = web.WebSocketResponse()
            # Aksho: the 101 is written inside prepare(), before the middleware
            # adds headers, and Firefox drops the live channel without the
            # private-network grant on it. The middleware has already refused
            # every origin that is not allowed.
            origin = request.headers.get("Origin")
            if origin:
                ws.headers["Access-Control-Allow-Origin"] = origin
                ws.headers["Vary"] = "Origin"
                ws.headers["Access-Control-Allow-Private-Network"] = "true"
            await ws.prepare(request)"""


def patch_browser_cors(comfy_dir: Path) -> None:
    """Let the Aksho sites, and only them, call this loopback server.

    ComfyUI with --enable-cors-header answers every origin and switches off its
    own cross-site guard, so any page the user visits could drive it. This
    swaps that middleware for one that admits the Aksho sites and pages on
    this machine, refuses the rest before they run, and grants the browsers'
    private-network permission only to the admitted ones. server.py is put
    back from git first, so the patch always lands on the pinned original.
    """
    git = require_tool("git", "Install the Xcode command line tools, or Homebrew git.")
    run([git, "checkout", "--", "server.py"], cwd=comfy_dir)
    path = comfy_dir / "server.py"
    text = path.read_text(encoding="utf-8")
    if CORS_ORIGINAL not in text or WS_ORIGINAL not in text:
        die(f"Could not guard {path}: ComfyUI's middleware changed. Update the installer for this ComfyUI release.")
    text = text.replace(CORS_ORIGINAL, CORS_GUARDED, 1).replace(WS_ORIGINAL, WS_GUARDED, 1)
    path.write_text(text, encoding="utf-8")
    info("Guarded ComfyUI so only the Aksho sites can reach it from a browser.")


def assert_mps(python: Path) -> None:
    info("Checking Metal acceleration...")
    script = (
        "import torch\n"
        "ok = torch.backends.mps.is_available()\n"
        "print(f'[AKSHO COMFY] torch {torch.__version__}  MPS {ok}')\n"
        "raise SystemExit(0 if ok else 1)\n"
    )
    result = subprocess.run([str(python), "-c", script])
    if result.returncode != 0:
        die("PyTorch installed, but Metal (MPS) is not available. ComfyUI would run on CPU only.")


def bootstrap(root: Path, source_version: str) -> Path:
    """Create .venv, check out ComfyUI, and install MPS PyTorch. Returns the venv python."""
    require_apple_silicon()
    root.mkdir(parents=True, exist_ok=True)
    python = ensure_venv(root)
    ensure_comfy(root, source_version)
    install_runtime_packages(python, root / "ComfyUI")
    assert_mps(python)
    return python
