"""Builds the deployable web folder (dist/) for a packaged project.

Input:  Engine/Binaries/Web/UnrealGame.js + UnrealGame.wasm   (WebGPUPort/Build/BuildWeb.bat)
        WebGPUPort/M3-Boot/out/<Project>.data + .data.js      (WebGPUPort/M3-Boot/package_content.bat Linux <Project>)
Output: WebGPUPort/M6-Deploy/dist/  - upload this folder as-is to any static web host (see HOSTING.md).

What it does:
  - removes the debug "name" section from the .wasm (function names for crash call stacks; ~84 MB). The full .wasm
    stays in Engine/Binaries/Web for local debugging.
  - gzip-compresses the two big files and splits them into parts of at most PART_MIB, so every file is below the
    hosts' per-file limits (Cloudflare Pages: 25 MiB) and the upload is small. The page downloads the parts,
    decompresses them in the browser (DecompressionStream) and hands them to the engine - the host needs no special
    compression or MIME settings.
  - part file names contain a content hash, so hosts/browsers may cache them forever; index.html and manifest.json
    are always revalidated.
  - copies the page (web/index.html) and the host configuration files (web/_headers for Cloudflare Pages,
    web/vercel.json for Vercel).

Usage: make_deploy.bat [Project=WebThirdPerson]
"""
import gzip
import hashlib
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROJECT = sys.argv[1] if len(sys.argv) > 1 else "WebThirdPerson"
ENGINE_BIN = os.path.join(ROOT, "Engine", "Binaries", "Web")
CONTENT = os.path.join(ROOT, "WebGPUPort", "M3-Boot", "out")
WEB = os.path.join(HERE, "web")
DIST = os.path.join(HERE, "dist")
PART_MIB = 20  # well below Cloudflare Pages' 25 MiB per-file limit
GZIP_LEVEL = 9

DIST_GITIGNORE = """\
# Only the website files may be committed (written by make_deploy.py; see HOSTING.md section 7A).
# Everything else that ends up in this folder by mistake is ignored.
*
!.gitignore
!.gitattributes
!index.html
!manifest.json
!vercel.json
!_headers
!game/
!game/*.bin
!game/*.js
"""


def leb128(data, pos):
    result = shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return result, pos


def strip_wasm_names(wasm):
    """Returns the module without the custom "name" section (other sections unchanged)."""
    out = bytearray(wasm[:8])
    pos = 8
    removed = 0
    while pos < len(wasm):
        start = pos
        section_id = wasm[pos]
        size, body = leb128(wasm, pos + 1)
        end = body + size
        if section_id == 0:
            name_len, name_pos = leb128(wasm, body)
            if wasm[name_pos:name_pos + name_len] == b"name":
                removed += end - start
                pos = end
                continue
        out += wasm[start:end]
        pos = end
    return bytes(out), removed


def write_parts(name, raw, mime):
    """gzip + split; returns the manifest entry."""
    t = time.time()
    packed = gzip.compress(raw, GZIP_LEVEL, mtime=0)
    digest = hashlib.sha256(raw).hexdigest()[:12]
    part_size = PART_MIB * 1024 * 1024
    parts = []
    for index, offset in enumerate(range(0, len(packed), part_size)):
        part_name = f"game/{name}.{digest}.part{index:03d}.bin"
        chunk = packed[offset:offset + part_size]
        with open(os.path.join(DIST, part_name), "wb") as f:
            f.write(chunk)
        parts.append({"url": part_name, "size": len(chunk)})
    print(f"  {name}: {len(raw) / 2**20:.1f} MiB -> gzip {len(packed) / 2**20:.1f} MiB in {len(parts)} part(s) ({time.time() - t:.0f} s)")
    return {"type": mime, "size": len(raw), "compressedSize": len(packed), "sha256": hashlib.sha256(raw).hexdigest(), "parts": parts}


def main():
    sources = {
        "UnrealGame.wasm": os.path.join(ENGINE_BIN, "UnrealGame.wasm"),
        "UnrealGame.js": os.path.join(ENGINE_BIN, "UnrealGame.js"),
        f"{PROJECT}.data": os.path.join(CONTENT, f"{PROJECT}.data"),
        f"{PROJECT}.data.js": os.path.join(CONTENT, f"{PROJECT}.data.js"),
    }
    for name, path in sources.items():
        if not os.path.isfile(path):
            sys.exit(f"Missing {path} - build/package first (see HOSTING.md, 'Rebuilding').")

    if os.path.isdir(DIST):
        # dist/ is generated output (git-ignored); keep the previous one next to it instead of deleting it
        previous = DIST + "_previous"
        if os.path.isdir(previous):
            shutil.rmtree(previous)
        os.rename(DIST, previous)
    os.makedirs(os.path.join(DIST, "game"))

    print(f"Building {DIST} for project {PROJECT}")
    wasm, removed = strip_wasm_names(open(sources["UnrealGame.wasm"], "rb").read())
    print(f"  removed the debug name section from the .wasm ({removed / 2**20:.1f} MiB)")
    files = {
        "UnrealGame.wasm": write_parts("UnrealGame.wasm", wasm, "application/wasm"),
        f"{PROJECT}.data": write_parts(f"{PROJECT}.data", open(sources[f"{PROJECT}.data"], "rb").read(), "application/octet-stream"),
    }

    # Small loader scripts: copied as they are (hosts compress .js themselves); hashed names for caching
    scripts = []
    for name in (f"{PROJECT}.data.js", "UnrealGame.js"):
        raw = open(sources[name], "rb").read()
        hashed = f"game/{name[:-3]}.{hashlib.sha256(raw).hexdigest()[:12]}.js"
        open(os.path.join(DIST, hashed), "wb").write(raw)
        scripts.append(hashed)

    manifest = {
        "project": PROJECT,
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "args": [f"/{PROJECT}/{PROJECT}.uproject", "-loosefileloading", "-stdout", "-unattended", "-windowed"],
        "files": files,
        "scripts": scripts,
    }
    with open(os.path.join(DIST, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    for name in ("index.html", "_headers", "vercel.json"):
        shutil.copy2(os.path.join(WEB, name), os.path.join(DIST, name))
    # Allowlist for the GitHub repository the dist contents are copied into: only website files can be committed,
    # anything else that lands in that folder by mistake (full .wasm, scripts, engine files) stays local.
    with open(os.path.join(DIST, ".gitignore"), "w", newline="\n") as f:
        f.write(DIST_GITIGNORE)
    # Git must store every file byte-for-byte (no Windows line-ending conversion, especially not of the .bin parts)
    with open(os.path.join(DIST, ".gitattributes"), "w", newline="\n") as f:
        f.write("# Store all files unchanged (no line-ending conversion). Written by make_deploy.py.\n* -text\n")

    total = 0
    count = 0
    largest = 0
    for dirpath, _, names in os.walk(DIST):
        for n in names:
            size = os.path.getsize(os.path.join(dirpath, n))
            total += size
            count += 1
            largest = max(largest, size)
    print(f"dist: {count} files, {total / 2**20:.1f} MiB total, largest file {largest / 2**20:.1f} MiB")
    print("  Cloudflare Pages (25 MiB per file, 20,000 files):", "OK" if largest <= 25 * 2**20 and count <= 20000 else "TOO LARGE")
    print("  Vercel Hobby CLI upload (100 MB total):", "OK" if total <= 100 * 1000 * 1000 else f"TOO LARGE ({total / 1e6:.0f} MB) - use Vercel Pro (1 GB) or Cloudflare Pages")


if __name__ == "__main__":
    main()
