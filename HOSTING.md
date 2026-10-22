# Putting the game on the web

This guide explains how to publish the browser build of the Third Person project and what the hosting
services allow. You do not need to know anything about web servers to follow it.

Hosting limits were checked on **2026-10-22** against the providers' own documentation (links at the end).
Providers change their limits, so re-check them before relying on a plan.

---

## 1. What you upload

`make_deploy.bat` creates the folder **`WebGPUPort\M6-Deploy\dist`**. That folder *is* the website. Upload
the whole folder, keeping its file and folder names exactly as they are:

| File | What it is |
|---|---|
| `index.html` | The page: loading screen, quality setting, full-screen and log buttons. |
| `manifest.json` | A list of the game files. The page reads this first. |
| `game/UnrealGame.wasm.<code>.part000.bin` ... | The engine, compressed and cut into pieces of at most 20 MiB. |
| `game/WebThirdPerson.data.<code>.part000.bin` ... | The game content (maps, meshes, textures, shaders), also compressed and cut into pieces. |
| `game/*.js` | Two small start-up scripts. |
| `_headers` | Settings for **Cloudflare Pages** (how long browsers may cache each file). Other hosts ignore it. |
| `vercel.json` | The same settings for **Vercel**. Other hosts ignore it. |
| `.gitignore`, `.gitattributes` | For a GitHub repository: only the files above can be committed, and Git stores them unchanged (section 7A). Harmless on any host. |

The current build is **14 files, about 108 MiB (113 MB)**. The largest file is 20 MiB.

### Why the files are cut into pieces
- Some hosts refuse files larger than a certain size: 25 MiB per file on Cloudflare Pages.
- The page downloads the pieces (four at a time, with a progress bar) and unpacks them in the browser. Hosts
  therefore don't need to compress anything or know what a `.wasm` file is.
- Each piece's name contains a code that changes whenever the file's content changes. Browsers may keep the
  pieces for a year, and a new build always gets new names, so nobody ends up with a mix of old and new files.

---

## 2. Test it locally

### 2a. On this PC
1. Double-click **`WebGPUPort\M6-Deploy\run_local_test.bat`**. A black window opens and says "Serving ...".
   Leave it open; closing it stops the game server.
2. Open **http://localhost:8080/** in Chrome or Edge.

This test server behaves like a plain web host: it sends **no special settings**. If the game works here, it
will work on any host that serves files unchanged.

> **Why not just double-click `index.html`?** Browsers do not let a page opened straight from disk
> (`file:///...`) download its own game files, so it would stop at "Reading the game manifest". A local server
> is always needed. The `.bat` file is that server.

### 2b. On another computer

**What to copy:** three things from `E:\UnrealEngine - dont touch\WebGPUPort\M6-Deploy\`, about 108 MiB.
Put them together in any folder on the other PC, for example `D:\ue-web\`. Spaces in the path are fine.

```
D:\ue-web\
├── dist\                  <- the whole folder, with its "game" subfolder (14 files)
├── serve_dist.py          <- the small test server
└── run_local_test.bat     <- double-click this
```

Nothing else is needed: no Unreal Engine, no project, no `Engine\Binaries`. **Do not** copy `dist_previous`;
it is the build before the last one.

**What the other PC needs:**
- **Chrome or Edge** (current version) and a graphics card with WebGPU support. Check: open `chrome://gpu` and
  look for "WebGPU: Hardware accelerated".
- **Python 3** for the test server. Install it from python.org and tick **"Add python.exe to PATH"** in the
  installer. To check, open Command Prompt and type `python --version`.
- Free memory: about 2 GB for the browser tab while the game loads.

**How to test:**
1. Double-click `run_local_test.bat`. Leave the black window open.
2. Open **http://localhost:8080/** in Chrome or Edge.
3. You should see the loading screen with a progress bar, then the level with the mannequin.
4. Click the picture, then use W A S D, Space, the mouse, and Esc.

**If the other PC is on the same network and you want to test from a phone or a third PC:** this test server
only answers on the PC it runs on (`localhost`), on purpose. Use real hosting (sections 6 and 7) instead.
WebGPU also needs HTTPS when the address is not `localhost`.

**Port 8080 already in use?** Run `run_local_test.bat --port 8090` from Command Prompt and open
`http://localhost:8090/`.

---

## 3. Which host to use

| | **Cloudflare Pages (free plan)** | **Vercel Hobby (free)** | **Vercel Pro** |
|---|---|---|---|
| Largest single file | 25 MiB (our pieces: 20 MiB ✅) | not limited per file in the docs | not limited per file in the docs |
| Number of files | 20,000 (drag-and-drop upload: 1,000) ✅ | 15,000 (command-line upload) ✅ | 15,000 ✅ |
| Total upload size | not limited in the docs ✅ | **100 MB with the command-line tool ❌ (ours: 113 MB)** | 1 GB ✅ |
| Monthly traffic | static files: free and unlimited (see the note below) | 100 GB per month (about 900 first-time visitors at ~113 MB each) | covered by Pro's monthly usage credit, more is billed per GB (see vercel.com/pricing) |
| Commercial use | allowed | **not allowed (personal, non-commercial only)** | allowed ($20 per developer per month) |

**Recommendation: Cloudflare Pages.** It is free, our build fits, and traffic for static files is unlimited.

Notes:
- **Cloudflare, large files:** Cloudflare's blog post on its free plans says "large assets (like videos) are not
  supported on our Free plan under its terms of service". Our pieces are game data, not video, but if a site
  becomes popular, read Cloudflare's current terms or consider a paid plan.
- **Vercel Hobby:** the documented 100 MB limit is for uploads with Vercel's command-line tool. The docs do not
  say whether deploying from a GitHub repository has the same limit. Section 7A explains that route; it is
  untested, with Cloudflare Pages as the fallback.
- **Vercel Hobby limits:** when a Hobby project goes over its free amounts, Vercel says you usually have to
  wait 30 days before that feature works again.

---

## 4. Required headers (server settings)

**None are required for this build.** In particular:

- **COOP/COEP** (`Cross-Origin-Opener-Policy` / `Cross-Origin-Embedder-Policy`) are only needed for
  multi-threaded WebAssembly (SharedArrayBuffer). This build is single-threaded, so it does not need them.
  If a future build uses threads, add both headers to `_headers` / `vercel.json`:
  `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp`.
- **The `.wasm` MIME type** (`application/wasm`) is not needed either: the page unpacks the engine itself and
  labels it correctly in the browser.
- **Caching (optional, already set up):** `_headers` (Cloudflare) and `vercel.json` (Vercel) tell browsers to
  keep the `game/` pieces for a year and to always check for a new `index.html` and `manifest.json`.
- **HTTPS:** both hosts serve HTTPS automatically. WebGPU only works on HTTPS sites (and on `localhost`).

## 5. Compression

The pieces are **already compressed** (gzip). Do not turn on anything extra. Hosts compress text files such as
`index.html` and the two `.js` scripts on their own, and they leave the `.bin` pieces alone, which is correct.

Sizes for this build:

| File | Unpacked | Compressed (what is downloaded) |
|---|---|---|
| Engine (`UnrealGame.wasm`, debug names removed) | 207 MiB | 49 MiB |
| Content (`WebThirdPerson.data`) | 166 MiB | 58 MiB |

---

## 6. Publishing on Cloudflare Pages (no tools needed)

1. Create a free account at **dash.cloudflare.com** (or log in).
2. Open **Workers & Pages** → **Create application** → **Pages** tab → **Get started** under
   *"Drag and drop your files"* (the dashboard wording may differ slightly).
3. Enter a project name, for example `ue-thirdperson`. It becomes part of the address:
   `https://ue-thirdperson.pages.dev`.
4. Drag the **contents of the `dist` folder** (or the folder itself) into the upload box. Wait until all
   files show as uploaded (12 to 14 files). If any file shows a red warning, see "Problems" below.
5. Click **Deploy site**. After a minute the game is available at the address shown. (`.gitignore` and
   `.gitattributes` may be listed among the uploaded files; they are harmless.)

**Updating the game later:** open the project → **Create deployment** → drag the new `dist` folder in again.
Old visitors automatically get the new version, because the page and manifest are always re-checked.

**Command-line alternative** (needs Node.js from nodejs.org): `npx wrangler pages deploy dist` from the
`WebGPUPort\M6-Deploy` folder. The first time, it asks you to log in through the browser.

---

## 7. Publishing on Vercel

There are two ways. **7A (GitHub import) is the one to try first on the free Hobby plan.**

### Will GitHub → Vercel work? (honest answer)

**Probably yes, but I could not test it.** My working rules do not allow me to push to GitHub, and I have no
Vercel account.

What the documentation says:

| Check | Limit | This build | Result |
|---|---|---|---|
| GitHub: largest file in a push | 100 MiB (warning above 50 MiB) | 20 MiB | ✅ |
| GitHub: largest file uploaded in the **web browser** | 25 MiB | 20 MiB | ✅ |
| GitHub: repository size | "ideally less than 1 GB" | ~108 MiB per version | ✅ |
| Vercel Hobby: 100 MB upload limit | documented **for the command-line tool**; the docs say nothing about Git imports | 113 MB | ❓ probably not applied, unverified |
| Vercel Hobby: Deployment Storage | 10 GB; keeps the 3 latest production + 3 latest other deployments per project | ~113 MB each | ✅ |
| Vercel Hobby: number of files | 15,000 (documented for the command-line tool) | 12 | ✅ |
| Vercel Hobby: traffic | 100 GB per month | ~113 MB per first-time visitor | ⚠️ about 900 new visitors per month |
| Vercel Hobby: Git repository owner | Hobby cannot connect to repositories owned by a GitHub **organization** | use a repository under your personal account | ⚠️ |
| Vercel Hobby: use | personal, non-commercial only | | ⚠️ |

If Vercel refuses the deployment because of its size, use Cloudflare Pages (section 6) or Vercel Pro.

> ⚠️ **Never push the engine repository** (`E:\UnrealEngine - dont touch`) to a public GitHub repository.
> Epic's EULA does not allow publishing Unreal Engine source code. Make a **new, separate repository**
> **outside** `E:\UnrealEngine - dont touch` that contains only the contents of `dist`.
>
> **Two safety nets are built in:**
> - **`dist` brings a `.gitignore` allowlist.** Your GitHub repository can only commit the website files
>   (`index.html`, `manifest.json`, `vercel.json`, `_headers`, `game\*.bin`, `game\*.js`). Anything copied in by
>   mistake (a full `.wasm`, scripts, engine files) stays on your PC. A `.gitattributes` file makes Git store
>   every file unchanged.
> - **`WebGPUPort\M6-Deploy\.gitignore` ignores everything.** If a repository is ever created in that folder
>   by mistake, it cannot commit anything.
>
> Neither can protect a repository made at `E:\UnrealEngine - dont touch` itself. In GitHub Desktop, never use
> **"Add existing repository"** on any folder inside `E:\UnrealEngine - dont touch`.

### 7A. GitHub repository → Vercel import (no command line needed)

**One-time setup:**
1. Create a free account on **github.com** (if you do not have one).
2. Install **GitHub Desktop** (desktop.github.com). It handles large uploads better than the browser and
   needs no commands.
3. In GitHub Desktop: **File → New repository**.
   - Name: `ue-thirdperson-web`
   - Local path: for example `D:\GitHub`
   - Initialize with a README: optional
   - **Git ignore: None**
   - Click **Create repository**.
4. Open the new folder (`D:\GitHub\ue-thirdperson-web`) in Explorer and copy the **contents** of
   `WebGPUPort\M6-Deploy\dist` into it: select all (Ctrl+A), copy, paste, and allow the replacement of the
   `.gitignore` / `.gitattributes` that GitHub Desktop may have created. `index.html` must sit directly in the
   repository folder, **not** inside a `dist` subfolder:
   ```
   ue-thirdperson-web\
   ├── .gitignore       (from dist: lets only the website files be committed)
   ├── .gitattributes   (from dist: Git stores files unchanged)
   ├── index.html
   ├── manifest.json
   ├── vercel.json
   ├── _headers
   └── game\  (8 files: 6 .bin pieces + 2 .js scripts, as created by make_deploy)
   ```
   In GitHub Desktop the "Changes" list should show exactly these 14 files. If it shows anything else, stop and
   check what was copied.
5. In GitHub Desktop: write a summary such as "First web build", click **Commit to main**, then
   **Publish repository**. You may untick "Keep this code private"; a private repository works with Vercel
   too. Wait until the upload finishes (about 110 MB).

**Import into Vercel:**
6. Go to **vercel.com** → sign up or log in **with GitHub** → **Add New… → Project**.
7. Under "Import Git Repository", choose `ue-thirdperson-web` → **Import**.
   If it is not listed, click "Adjust GitHub App Permissions" and allow access to that repository.
8. Settings on the import screen:
   - **Framework Preset: Other**
   - **Root Directory:** leave as `./`
   - **Build Command:** leave empty (or switch its "Override" on and leave the box empty)
   - **Output Directory:** leave empty / default
   - **Install Command:** leave empty
9. Click **Deploy**. After about a minute Vercel shows the address, for example
   `https://ue-thirdperson-web.vercel.app`. Open it in Chrome.

`vercel.json` in the repository is applied automatically (caching rules). `_headers` is ignored by Vercel,
which is harmless.

**Updating the game later:**
1. Run `make_deploy.bat` again.
2. In the repository folder, **delete the old `game` folder first**. The new pieces have new names; without
   this, old pieces pile up and the repository grows with every build. Keep the hidden `.git` folder.
3. Copy the new `dist` contents in, then commit and push in GitHub Desktop ("Push origin").
4. Vercel redeploys automatically.

**If the import or deployment fails:**
- "Deployment is too large" or a similar size error: the Hobby limit applies to Git imports too. Use Cloudflare
  Pages or Vercel Pro.
- The page loads, but you see "manifest.json not found (HTTP 404)": `index.html` is inside a subfolder. Either
  move the files up to the repository's top level, or set **Root Directory** to that subfolder in the Vercel
  project settings.
- GitHub Desktop says a file is too large: something other than `dist` was copied in. The largest file should
  be 20 MiB.

### 7B. Command-line upload (Vercel CLI)

**This build (113 MB) is over the Hobby plan's documented 100 MB command-line upload limit**, so this route
needs Vercel Pro, or a build smaller than 100 MB.

1. Install **Node.js** (LTS version) from nodejs.org.
2. Open a terminal in `WebGPUPort\M6-Deploy` (in Explorer: click the address bar, type `cmd`, press Enter).
3. Run `npx vercel login` and log in through the browser.
4. Run `npx vercel deploy dist --prod`. When asked:
   - "Set up and deploy?" → **yes**
   - "Which scope?" → your account
   - "Link to existing project?" → **no**
   - project name → for example `ue-thirdperson`
   - "In which directory is your code located?" → `./` (just press Enter)
   - "Want to modify these settings?" → **no**
5. Vercel prints the address, for example `https://ue-thirdperson.vercel.app`.

`vercel.json` inside `dist` is picked up automatically.

---

## 8. Making the build smaller (optional, later)

Ideas, roughly from most to least effective:

- **Engine:** a "Shipping" engine build, or compiling for size instead of speed, would shrink the 49 MiB engine
  download. Both need a full engine rebuild and testing.
- **Shaders:** turn on shader compression in the cook again. Oodle now works in the browser, but the shader
  translator would have to learn to unpack Oodle first.
- **Content:** remove engine content the game does not use. NNEDenoiser, 106 MB, is already excluded.

---

## 9. Problems and what they mean

| What you see | Cause and what to do |
|---|---|
| "This browser has no WebGPU" | Use a current desktop **Chrome or Edge**. Firefox and Safari are not supported yet by this build. |
| "no graphics adapter was found" | Update the graphics driver; check `chrome://gpu` (WebGPU should say "Hardware accelerated"). |
| WASD / Space do nothing, arrow keys work | A typing tool for another language (Avro, Bijoy, an IME) is changing the keys. Switch the keyboard to English (Windows: **Win + Space**). |
| Stuck at "Downloading" | Slow connection or a blocked file. Open the browser's developer tools (F12) → Network tab and look for red entries. |
| A red error box, or the game stops | Click **Log** (top right), copy the last lines and send them for diagnosis. |
| Cloudflare upload shows a red warning on a file | A file over 25 MiB; should not happen with `make_deploy.bat` (pieces are 20 MiB). Rebuild `dist`. |
| Vercel says the deployment is too large | Hobby's 100 MB limit (section 3); use Cloudflare Pages or Vercel Pro. |

**Address options for testing:**
- `?quality=low|medium|high|epic` chooses a preset.
- `?cmds=stat~fps` runs engine console commands. `~` is a space; separate several commands with `,`.

**Quality presets** (the menu at the top right, remembered by the browser):

| Preset | Render size | UE scalability level |
|---|---|---|
| Low | 960×540 | 0 |
| Medium | 1280×720 | 1 |
| High (default) | 1600×900 | 2 |
| Epic | 1920×1080 | 3 |

All presets keep High material quality and full character detail; see "Known limitations".

---

## 10. Rebuilding everything

Run these from a normal Command Prompt. Close the Unreal editor first.

1. **Engine:** `WebGPUPort\Build\BuildWeb.bat UnrealGame Development`
2. **Cook:** the command is in `PROGRESS.md` → "Rebuild commands" → "M5 Third Person" step 3.
3. **Content package:** `WebGPUPort\M3-Boot\package_content.bat Linux WebThirdPerson`
4. **Deploy folder:** `WebGPUPort\M6-Deploy\make_deploy.bat`. It prints the sizes and whether they fit
   Cloudflare and Vercel Hobby. The previous `dist` is kept as `dist_previous`.
5. **Check:** `WebGPUPort\M6-Deploy\run_local_test.bat`, then upload `dist`.

---

## 11. Known limitations of this build

- Desktop Chrome or Edge with WebGPU only; not tested on phones, Firefox or Safari.
- No sound (the audio part of the port is not done).
- Keyboard and mouse only: no gamepad and no touch.
- **Rendering bug (open):** the mannequin's lower-detail versions (LODs) render too dark. The presets keep
  full detail, but a character far from the camera may still switch to a darker version.
- **Debug names removed:** the published engine has no function names, so crash reports show numbers instead.
  The full engine with names stays in `Engine\Binaries\Web` for local debugging.

## 12. License note (not legal advice)

- **What you are publishing:** a game made with Unreal Engine. That is allowed under Epic's EULA, the same as a
  packaged Windows game: compiled engine code plus cooked content, including the template's mannequin and
  levels.
- **Royalties:** the EULA's royalty terms apply only if a product earns money (above Epic's revenue threshold).
- **Source code:** do **not** publish engine source code, including the Oodle source files. The `dist` folder
  contains only compiled code.
- **Commercial use:** it is also restricted by the host: Vercel Hobby forbids it.

---

### Sources (checked 2026-10-22)
- Cloudflare Pages limits: <https://developers.cloudflare.com/pages/platform/limits/>
- Cloudflare Pages direct upload: <https://developers.cloudflare.com/pages/get-started/direct-upload/>
- Cloudflare Pages `_headers`: <https://developers.cloudflare.com/pages/configuration/headers/>
- Cloudflare compression: <https://developers.cloudflare.com/speed/optimization/content/compression/>
- Cloudflare Pages pricing (static requests free and unlimited): <https://developers.cloudflare.com/pages/functions/pricing/>
- Cloudflare free plan note on large assets: <https://blog.cloudflare.com/cloudflares-commitment-to-free/>
- Vercel limits: <https://vercel.com/docs/limits>
- Vercel Hobby plan: <https://vercel.com/docs/plans/hobby>
- Vercel compression: <https://vercel.com/docs/how-vercel-cdn-works/compression>
- Vercel Hobby deployment storage (10 GB, retention): <https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage>
- GitHub large files (50 MiB warning, 100 MiB limit, 25 MiB browser upload): <https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github>
