# Cloudflare Pages deployment

## URLs

- Project: `divider-explainer`
- Production: https://divider-explainer.pages.dev/
- Deployment: https://d1019d6d.divider-explainer.pages.dev

## Rebuild and redeploy

Run from the repository root with `/usr/bin/python3` (Pillow is required) and an authenticated Wrangler installation:

```sh
/usr/bin/python3 scripts/build_site.py
/usr/bin/python3 presentation/verify_site.py
grep -rIn -E '/home/|@[a-z0-9-]+\.[a-z]{2,}|password|token|secret|ghp_|gho_' site
npx --yes wrangler pages deploy site --project-name divider-explainer --branch main --commit-dirty=true
```

Review every privacy match before deploying. The builder regenerates both presentation pages and replaces the `site/` output; it keeps the original images and writes only referenced, content-hashed WebP files to the deploy directory.

## Rollback

List deployments with:

```sh
npx --yes wrangler pages deployment list --project-name divider-explainer
```

In the Cloudflare dashboard, open Workers & Pages → divider-explainer → Deployments, select the earlier production deployment, and choose Rollback. Wrangler's deployment command has no rollback subcommand in the installed version. Confirm the production URL after rollback.

## Checks

The baseline generated pages passed `presentation/verify_site.py`. The requested headless `--window-size` command clamped `innerWidth` to 500 for both 360 and 390, so it could not measure phone widths: at that width it reported 50 small controls on the explainer and 185 on the glossary. Baseline screenshots were inspected. The final probe uses Chrome DevTools device metrics to set the actual viewport. Values below are scrollWidth, innerWidth, oversized images, and visible interactive elements smaller than 44 px, respectively.

| Page | Requested width | scrollWidth | innerWidth | Oversized images | Small targets |
|---|---:|---:|---:|---:|---:|
| index.html | 360 | 360 | 360 | 0 | 0 |
| index.html | 390 | 390 | 390 | 0 | 0 |
| index.html | 768 | 753 | 768 | 0 | 0 |
| index.html | 1440 | 1425 | 1440 | 0 | 0 |
| glossary.html | 360 | 360 | 360 | 0 | 0 |
| glossary.html | 390 | 390 | 390 | 0 | 0 |
| glossary.html | 768 | 768 | 768 | 0 | 0 |
| glossary.html | 1440 | 1440 | 1440 | 0 | 0 |

Local `presentation/verify_site.py` and its `node --check` validation exited 0. Local link checks (all unique non-fragment href and src URLs):

```text
200 http://127.0.0.1:8788/assets/drc_result.b8175dd5aeee.webp
200 http://127.0.0.1:8788/assets/fig_circuit_latch.ea9d1623a6d5.webp
200 http://127.0.0.1:8788/assets/fig_circuit_ring.59a819629685.webp
200 http://127.0.0.1:8788/assets/fig_fsweep.36ac97b9b8e5.webp
200 http://127.0.0.1:8788/assets/fig_phase_steps.72b7941690a1.webp
200 http://127.0.0.1:8788/assets/fig_pvt_heatmap_B_6g.25c6050b511f.webp
200 http://127.0.0.1:8788/assets/fig_pvt_heatmap_D_1p4.94fa2d02b5b7.webp
200 http://127.0.0.1:8788/assets/fig_tail_saturation_D_1p4.cfa2457b585d.webp
200 http://127.0.0.1:8788/assets/layout_core_full.7033a0b0b1bd.webp
200 http://127.0.0.1:8788/assets/layout_dlatch_full.7a7048f0677f.webp
200 http://127.0.0.1:8788/assets/schematic_core_full.42dc9972f6d3.webp
200 http://127.0.0.1:8788/assets/schematic_dlatch_full.69e983be1862.webp
200 http://127.0.0.1:8788/assets/virtuoso_ciw_gpdk045_loaded.b95594df7868.webp
200 http://127.0.0.1:8788/assets/viva_tran_D_1p4GHz_full.cced45042d56.webp
200 http://127.0.0.1:8788/favicon.svg
200 http://127.0.0.1:8788/glossary.html
200 http://127.0.0.1:8788/index.html
```

The production root, `/glossary`, and the first image returned HTTP/2 200 with the intended cache and security headers. Live emulation at 360 and 390 returned `[360,360,0,0]` and `[390,390,0,0]` respectively. The live 390 screenshot was inspected.

Privacy grep output follows. These are ordinary references to a completion token and to credential remediation, not values of credentials. No absolute home path, email address, access-token prefix, or actual password was found by this scan. This scan cannot prove the absence of every possible secret.

```text
site/index.html:1938:                  Built an automated headless test harness for the 32-bit CentOS 6.5 Cadence virtual machine (<code class="inline-code">CadenceVM</code>) hosting Virtuoso IC615, Spectre 12.1, and Assura 4.1. Resolved missing 32-bit perl and gcc libraries required for BSIM4 C-model compilation. Developed a headless virtual serial console (<code class="inline-code">vmx.sh</code>, <code class="inline-code">serial.txt</code>) with completion tokens (<code class="inline-code">__DONE_$n</code>), automated ISO file staging (<code class="inline-code">xorriso</code>) to virtual CD-ROM (<code class="inline-code">/mnt/r</code>), and mutual exclusion via <code class="inline-code">flock vm.lock</code>.
site/index.html:3899:                <p class="qna-answer">Because the legacy Cadence tools run inside a headless VirtualBox VM without network sharing, host scripts communicate via a virtual serial port (`/dev/ttyS0`). The host injects shell commands into the guest using `VBoxManage controlvm CadenceVM keyboardputstring`, and monitors host file `serial.txt` until a unique completion token (`echo __DONE_$n &gt; /dev/ttyS0`) appears. Large scripts and RSF templates are packaged dynamically into temporary ISO9660 filesystems via `xorriso` and attached to the virtual CD-ROM drive (`/mnt/r`). Concurrency across background subagents is strictly serialized using POSIX file lock `flock vm.lock`.</p>
site/index.html:3901:                  <strong>Numbers to quote:</strong> Serial console: /dev/ttyS0; completion token __DONE_$n; ISO staging via xorriso mounted at /mnt/r; mutual exclusion enforced via flock vm.lock.
site/index.html:4236:              <span class="checklist-title">(k) Security remediation: Rotate and purge plaintext VM password</span>
site/index.html:4242:            <p class="checklist-desc">A plaintext login password exists in the legacy task prompt file (`PROMPT.md`). The guest account password should be rotated, and git history scrubbed or the file updated to use environment variables or local credentials ignored by git (v2 schedule task W2, risk R9, requirement SR-12, decision D6).</p>
site/index.html:4590:                    <td>Plaintext VM password exposed in repository history</td>
site/index.html:4592:                    <td>Immediate security remediation: rotate guest password and scrub PROMPT.md from git history.</td>
site/index.html:4600:                <li><strong>Security Action (W2 / R9):</strong> Rotate the VM login credential and scrub the plaintext password from git commit history or replace PROMPT.md with environment variable references (do not print credentials).</li>
site/index.html:4621:                  Sign decisions D1–D6; scrub secret from history; rerun nominal Designs D and B under VM lock; check PDK for Monte Carlo model files; begin E1 parameter sweep and manual routing.
```

## Sizes

Measured with `gzip -c` on each deployable file: total **803,550 bytes** [MEASURED]. The explainer HTML plus its eager image totals **96,084 bytes** [DERIVED; sum of gzip sizes], excluding browser request headers. In a fresh live Chrome session at 360 px, Resource Timing reported **89,527 bytes** [DERIVED; 56,739 HTML + 32,318 image + 470 favicon transferSize], including reported header overhead. Cache state, encoding and the browser's lazy-loading behavior affect actual transfer.
