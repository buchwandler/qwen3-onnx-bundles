# qwen3-onnx-bundles — implementation brief

**Status:** catalog-only repository specification / feasibility reviewed 2026-10-14  
**Target GitHub repository:** `buchwandler/qwen3-onnx-bundles` (proposed; not created by this brief)  
**Related producer package:** [`qwen3synth`](./qwen3synth-implementation-brief.md)  
**Consumer/owner of installation and ONNX runtime:** existing `onnxvoice` project  
**Distribution:** Git repository containing deterministic JSON, schema, provenance, documentation, and CI. **Not a Python package.**

## 0. Decision, name, scope

**Proceed.** This is directly analogous to the supplied `pocket-onnx-bundles` snapshot, but it must handle **several independent upstream Hugging Face repositories** and **multiple graph layouts and model types**. Avoid treating “Qwen3-TTS” as one ONNX bundle: VoiceDesign, Base voice clone, and CustomVoice are different model capabilities, and community exporters split them into different ONNX components.

### Namespace checks as of 2026-10-14

- `https://pypi.org/project/qwen3synth/` and `https://pypi.org/pypi/qwen3synth/json` returned HTTP 404.
- `https://pypi.org/project/qwen3-onnx-bundles/` and its JSON API returned HTTP 404. This repository **should not** claim that PyPI name.
- `https://github.com/buchwandler/qwen3synth` and `https://github.com/buchwandler/qwen3-onnx-bundles` returned HTTP 404. GitHub namespace is only *apparently* vacant; HTTP 404 can also indicate a private repository, so this is not a reservation or ownership check.
- `qwen3synth` is a good project name alongside `pocketsynth`; `qwen3-onnx-bundles` mirrors `pocket-onnx-bundles` precisely. Keep independent-project/non-affiliation language because “Qwen” identifies an upstream model family; PyPI/GitHub availability does not establish trademark permission.

### What this repository **is**

1. A **normalized, validated and reproducible ONNX bundle catalog** referencing remote public artifacts at immutable commits.
2. A compact provenance record of upstream sources, license declarations, export-specific model layouts, tokenizer and config assets, graph roles, quality profiles, and validation status.
3. A portable machine-readable contract consumed by `onnxvoice` and queryable by `qwen3synth` through `onnxvoice`'s public catalog API.
4. A controlled scheduled/manual catalog-refresh process with reviewable diffs and audit logs.

### What it **is not**

- **Not** `pyproject.toml`, a PyPI wheel, an import package, a CLI, a model mirror, a collection of ONNX `.onnx.data` binaries, a Hugging Face downloader, a voice-profile registry, or a second ONNX Runtime layer.
- **Not** an ONNX exporter or graph converter.
- **Not** an executable copy of third-party inference examples (`generate_onnx.py`, `onnx_inference.py`, etc.). Those are research references, never installed, imported, bundled or executed as part of release validation.
- **Not** an assertion of cross-exporter compatibility. A `wavekat-v1` bundle is not interchangeable with an `xkos-v1` bundle simply because both implement Qwen3-TTS.

## 1. Supplied repository precedent and ownership

The reconstructed `pocket-onnx-bundles` repository provides these conventions worth reusing:

```text
catalog/bundles.json
catalog/source.json
schemas/bundle-catalog.schema.json
README.md
NOTICE
LICENSE
.github/workflows/checks.yml
.github/workflows/refresh-catalog.yml
```

Its `catalog/bundles.json` holds bundle IDs/aliases, artifact roles, relative paths, quality profiles, sample rates and source provenance. Its README explicitly says `onnxvoice` owns catalog parsing, download/verification, installation manifests, cache, providers, graph sessions and the Pocket runtime adapter. Its scheduled workflow calls `onnxvoice catalog pocket build` and `onnxvoice catalog pocket verify`. Its bootstrap snapshot documents unset hashes/sizes; **the Qwen project must improve on this by requiring complete hashes before publishing installable catalog entries**.

**Do not break that boundary:**

| Responsibility | Owner |
| --- | --- |
| Data model/schema/curated bundle entries | `qwen3-onnx-bundles` |
| HF source enumeration, pinning, metadata resolution and catalog generation | `onnxvoice` catalog tools |
| Asset downloading, cache, size/SHA-256 verification, offline installs | `onnxvoice` |
| ONNX providers, session graph contracts, Qwen talker decode, code predictor, vocoder, encoder, KV cache | `onnxvoice` Qwen adapter |
| BPE prompt template, voice design & clone public API, generated voice profiles, CLI | `qwen3synth` |
| Document/SSMD semantics, pauses/timeline/final mastering | Calling application |

## 2. Initial supported upstream sources

Prioritize **one validated exporter family** for MVP. The checked public sources are:

| Upstream repository | Capability | Planned catalog ID | Priority |
| --- | --- | --- | --- |
| [`wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX`](https://huggingface.co/wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX) | Prompt-based VoiceDesign; FP32 + INT4 | `wavekat-voice-design-1.7b` | P0/MVP |
| [`wavekat/Qwen3-TTS-0.6B-Base-ONNX`](https://huggingface.co/wavekat/Qwen3-TTS-0.6B-Base-ONNX) | Voice cloning; FP32 + INT4 | `wavekat-base-0.6b` | P0/MVP |
| [`xkos/Qwen3-TTS-12Hz-1.7B-ONNX`](https://huggingface.co/xkos/Qwen3-TTS-12Hz-1.7B-ONNX) | Different Base + VoiceDesign export organization | Separate `xkos-*` IDs | Investigation only |
| [`onnx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign`](https://huggingface.co/onnx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign) | Alternative VoiceDesign exports/precisions | Separate `onnx-community-*` IDs | Investigation only |
| [`zhangluoyang/qwen3-tts-onnxruntime`](https://github.com/zhangluoyang/qwen3-tts-onnxruntime) | Export/inference study for Base/CustomVoice/VoiceDesign | **No automatic catalog entry** | Research only |

Official lineage should be linked (e.g. `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` or `Qwen/Qwen3-TTS-12Hz-0.6B-Base`). Never present a community ONNX revision as the official Qwen checkpoint revision. Each catalog entry records both identities separately.

**Do not invent commit hashes or artifact checksums.** The source repository page sometimes shows abbreviated commit IDs. The builder must resolve an exact **40-hex immutable revision** using the Hugging Face API or an equivalent verified revision-resolution method before emitting entries.

## 3. Directory structure

```text
qwen3-onnx-bundles/
├── .codecrate.toml
├── .gitignore
├── LICENSE
├── NOTICE
├── README.md
├── CHANGELOG.md
├── catalog/
│   ├── bundles.json              # canonical normalized bundle catalog
│   └── source.json               # pinned source(s) / catalog build provenance
├── schemas/
│   └── bundle-catalog.schema.json
├── docs/
│   ├── sources.md                 # reviewed exporter list, capabilities, status
│   ├── formats.md                 # graph layout/profiles/artifact semantics
│   ├── consumer.md                # onnxvoice + qwen3synth integration
│   ├── licensing.md
│   └── maintainers.md              # refresh procedure and review checklist
└── .github/workflows/
    ├── checks.yml                 # schema & static artifact metadata verification
    └── refresh-catalog.yml        # scheduled/manual, controlled update PR
```

Only small, textual source-controlled files. No ONNX model binaries, tokenizer binary blobs, generated voice samples, or Python packaging in this repo.

## 4. A deliberately versioned catalog contract

Start from Pocket's `schema: 1`, `kind`, `source`, `bundles`, `profiles`, `artifacts` approach. For Qwen add **source-per-bundle**, **model type**, **ONNX export layout**, **component-wise quality**, and **external ONNX data dependencies**. The JSON schema must reject unknown/invalid fields (except intentionally extensible `metadata`). The following are **proposed normative fields**, not claims about an existing `onnxvoice` schema.

### Top-level object

```json
{
  "schema": 1,
  "kind": "qwen3-onnx-bundle-catalog",
  "source": {
    "generator": "onnxvoice catalog qwen3 build",
    "generated_from": "pinned-huggingface-revisions",
    "bundle_count": 2
  },
  "bundles": {
    "wavekat-voice-design-1.7b": { "...": "see definition below" },
    "wavekat-base-0.6b": { "...": "see definition below" }
  }
}
```

This sketch is **illustrative, not a distributable valid release file**. The real schema must specify every required field and prohibit `"..."` placeholders.

### Required bundle fields

| Field | Meaning and constraint |
| --- | --- |
| `id` | Stable exporter-qualified ID; unique across catalog |
| `aliases` | Human-friendly unique aliases, e.g. `voice-design-1.7b`, `base-0.6b` (only when unambiguous) |
| `family` | `qwen3-tts` |
| `model_type` | enum: `voice_design`, `base`, `custom_voice` |
| `model_size` | `0.6b`, `1.7b` (validated against config) |
| `layout` | explicit ABI version such as `qwen3-wavekat-v1` |
| `languages` | BCP-47 or source-backed normalized language tags; list, not single locale |
| `sample_rate` | native PCM output Hz (24,000 for reviewed WaveKat exports) |
| `codec_frame_rate` | semantic codec frame rate (12 Hz for reviewed 12Hz exports) |
| `capabilities` | enum set (`voice_design`, `voice_clone`, `icl`, `custom_voice`, `streaming` only if tested) |
| `profiles` | profile names → **role-wise quality assignments**, never a global bool |
| `artifacts` | pinned list of model and non-model files with normalized roles |
| `source` | exact export HF repo/revision, official parent model, declared license, source URL |
| `metadata` | descriptive model details only; never security-critical data read from here |

### Recommended normalized artifact roles

**Shared/static per bundle:** `model_config`, `tokenizer_json`, `tokenizer_config`, `tokenizer_vocab`, `tokenizer_merges` when present, `embedding_*` for every required pre-extracted `.npy` or other embedding asset. Do **not** force one particular set of static files on exports that differ; source manifest describes actual dependencies.

**WaveKat VoiceDesign (FP32 or INT4):**

- `talker_prefill`
- `talker_decode`
- `code_predictor`
- `vocoder`
- each ONNX graph's **external data files** as required by ONNX model metadata

**WaveKat Base (additional FP32 components):**

- `speaker_encoder` (FP32)
- `tokenizer_encoder` (FP32)
- the same prefill/decode/predictor/vocoder role set plus their external data and shared static assets

Do not equate the audio `tokenizer_encoder` graph with the text tokenizer JSON. They are unrelated components.

### Every artifact entry

Require:

```text
role:          nonempty stable normalized role
quality:       fp32 | fp16 | int4 | null  (only where source provides it)
format:        onnx | onnx-external-data | json | npy | text | ... (whitelisted)
filename:      original source basename
path:          safe source-relative POSIX path
install_path:  safe bundle-relative layout path preserving external-data adjacency
repository:    exact owning Hugging Face repository (when needed)
revision:      exact 40-character SHA for that artifact's owning repo
url:           URL incorporating repository, pinned revision and path
size:          positive verified byte count
sha256:        64 lowercase hex characters, verified from provider metadata or downloaded content
depends_on:    role/path references, used for ONNX external data linkage if applicable
```

Artifact keys must not be inferred from basename alone. A file such as `fp32/talker_prefill.onnx.data` is **required** if the accompanying `talker_prefill.onnx` uses external tensor weights; never fetch just the small `.onnx` file and claim the model is installed. Parent/child graph/data relationships and colocated relative paths must survive the content-addressed blob store's installation materialization.

### Profiles

For MVP, expose only exporter-supported profile combinations. Example (conceptual):

```json
{
  "int4": {
    "speaker_encoder": "fp32",
    "tokenizer_encoder": "fp32",
    "talker_prefill": "int4",
    "talker_decode": "int4",
    "code_predictor": "int4",
    "vocoder": "int4"
  },
  "fp32": {
    "speaker_encoder": "fp32",
    "tokenizer_encoder": "fp32",
    "talker_prefill": "fp32",
    "talker_decode": "fp32",
    "code_predictor": "fp32",
    "vocoder": "fp32"
  }
}
```

The Base pattern reflects WaveKat's model-card statement that `speaker_encoder` and `tokenizer_encoder` are FP32. VoiceDesign has **no** encoder roles; exclude them from its profile instead of using empty/null assignments. If exporter metadata does not demonstrate FP16 availability, do not synthesize an FP16 profile from FP32/INT4. Profile selection must produce a **closed artifact set** (including static/transitive external data) with no mixed variants outside explicitly declared combinations.

### Different sources require different layouts

`qwen3-wavekat-v1`, `qwen3-xkos-v1`, and `qwen3-onnx-community-v1` must not share ONNX ABI assumptions. Each layout has an independently verified graph manifest, required role set, preprocessing signatures, embedding conventions, and exact public runtime capability. Catalog validation ensures declared layout support in the installed `onnxvoice` runtime. If catalog includes a newer unsupported layout, list it as discoverable but fail installation/open with a typed unsupported-layout error; do not select a superficially similar adapter.

## 5. Source provenance and updates

`catalog/source.json` must identify **each** upstream bundle source, instead of copying Pocket's single-source `bundle_root` field. Example structure:

```text
schema
catalog_generated_at (optional; do not affect canonical content hash without intention)
sources:
  - bundle_id
    provider: huggingface
    repository: wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX
    requested_revision: main
    revision: <RESOLVED_FULL_40_HEX_SHA>
    official_parent_model: Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
    license: apache-2.0  # only after verifying the exact model revision/card
    artifact_count
    status: validated | experimental | disabled
  - ...
source_count
bundle_count
schema_abi_revision
```

The above angle-bracket revision is a **documentation placeholder**, never a released catalog value. Preserve card URL/revision and upstream model source separately; include checked license identifiers and any additional export license restrictions, not a claim that all conversions share one license.

Keep aliases stable once public. An upstream graph rename, new precision, new tokenizer or changed config should result in a **new pinned revision and a reviewed manifest diff**; change the `layout` ABI version if graph I/O, preprocessing or conditioning semantics change. Do not retarget previously published versions in place without recording the changed revision.

## 6. `onnxvoice` catalog integration (required upstream code)

The data repository **does not implement these commands**. Extend the existing `onnxvoice` CLI/catalog tooling to add the proposal below, consistent with Pocket's commands:

```bash
onnxvoice catalog qwen3 build \
  --output catalog/bundles.json \
  --source-output catalog/source.json

onnxvoice catalog qwen3 verify \
  --catalog catalog/bundles.json \
  --source catalog/source.json

onnxvoice catalog qwen3 inspect \
  --catalog catalog/bundles.json \
  --bundle wavekat-base-0.6b
```

User-facing `onnxvoice` operations should use normalized Qwen bundle identity, e.g.:

```bash
onnxvoice list --system qwen3
onnxvoice install qwen3:wavekat-voice-design-1.7b --quality int4
onnxvoice install qwen3:wavekat-base-0.6b --quality int4
onnxvoice installed
onnxvoice cache info
```

**Important:** These commands are acceptance targets; the supplied `onnxvoice` snapshot does **not** yet contain a Qwen adapter/catalog subcommand. `qwen3synth` must not work around missing features by implementing another downloader.

### Build algorithm

1. Load a deliberately reviewed **allowlist** of candidate HF repository IDs and supported model types (never “discover every repo matching qwen”).
2. Query the provider for current `main`, resolve to full immutable SHA, get repository file listing and metadata. Support authentication for metadata where terms permit, but never put access tokens into JSON/catalog/logs.
3. Read the upstream `config.json` and inspect model file layout. Collect all `tokenizer/`, `embeddings/`, ONNX graph files, **external data**, and required auxiliary metadata. Do not include reference scripts, README images, irrelevant archive files or original PyTorch weights.
4. Map graph/files to **exact role + quality + layout**; prove required roles from a layout descriptor in `onnxvoice` and derive profile combinations from files that exist.
5. Retrieve trusted artifact byte lengths + SHA-256 from content-addressed provider metadata where supported; otherwise fetch+hash actual bytes before publishing. Hugging Face Xet/LFS pointer digests must be distinguished from pointer-file hash and validated against the actual downloadable artifact bytes. Never blindly claim the metadata SHA is the model SHA without verifying its semantics.
6. Validate URLs contain immutable revisions and are constructed from encoded, allowlisted host/repository/path components, avoiding arbitrary redirects to untrusted hosts and path traversal.
7. Generate stable ordering of bundles, roles and sources; deterministic JSON encoding with normalized newlines. No dates/volatile counters inside the content identity unless intentionally versioned.
8. Validate generated catalog against strict JSON Schema **and additional semantic rules**. Emit human-readable change report of added, removed, renamed and upgraded artifact paths.
9. Write to temporary files and atomically replace target catalog/source only when both verify. Never leave a half-refreshed pair.

### Verification algorithm — mandatory checks

- JSON Schema 2020-12 validation, known `kind` and `schema`, exact required fields, no unsafe additional properties.
- Source and bundle counts are identical to actual entries; each entry's source revision agrees with `source.json`.
- Unique bundle IDs and aliases; no ambiguous alias across exporter families.
- Model type, size, language list, sample rate, codec rate, capabilities and profile names are valid and source-backed.
- 40-char pinned revisions; 64-char real content hashes; positive sizes. **No `null` hash/size in a published installable bundle.**
- No external URLs beyond allowlisted Hugging Face patterns; URL encodes exact repository/revision/path without `main`/unbounded mutable refs.
- No duplicate role+quality+path, unsafe `../`, absolute path, `\\` traversal, symlink escape or case-insensitive target collision.
- Every profile has exactly one file for each mandatory component and its complete external data closure.
- All graph external data references resolve within the bundle directory with the required relative locations; reject missing `onnx.data` even if graph file exists.
- Every `layout` is known or explicitly marked discover-only/experimental. No publishing a profile that the runtime would silently misinterpret.
- Source metadata does not claim benchmark, provider/precision support, streaming or clone capability without actual validation.
- Verification is **offline by default** for structural checks; separately mark optional online source-hash and real-model loading checks.

## 7. CI workflows

### `checks.yml` — PR/push, lightweight

1. Checkout code; set up Python only to run the **owned** `onnxvoice` catalog validator (not a third-party inference tool).
2. Install a pinned released `onnxvoice` or test a pinned commit while the Qwen catalog feature is being developed.
3. Run `onnxvoice catalog qwen3 verify` with committed JSON.
4. Validate JSON syntax and schema; check sorted deterministic serialization and no changed generated files after rebuild in a controlled fixture test.
5. Check duplicate aliases/paths, every hash/size, pinned URLs, license and source consistency; verify no binary weight files or Python runtime packaging crept into the repo.
6. On failure, attach a small validation report (without credentials). No multi-GB model download on ordinary PRs.

### `refresh-catalog.yml` — scheduled/manual

- Use cron + `workflow_dispatch` with allowlist or bundle ID filter; concurrency prevents overlapping updates.
- Resolve upstream refs to immutable SHAs, regenerate data, verify full integrity data, and produce a **pull request** for maintainer review rather than automatically committing changed revisions straight to default branch.
- CI may download very large weight files if the provider doesn't expose trusted hashes. Budget time, storage, and network accordingly; separate metadata candidate refresh from heavyweight hash verification if needed. Any partially verified entries stay `experimental`/unpublished.
- Attach a clear change summary (model type, revisions, added/removed artifacts, precision, license, total/download size) and note unvalidated changes.
- Never trust arbitrary content from model cards as instructions to execute; never execute scripts from remote model repositories.
- Release tags track catalog data history; `schema` version tracks consumer compatibility. No Python distribution version.

## 8. Consumer behavior and examples

`onnxvoice` must support metadata-only discovery without model download:

```python
from onnxvoice import OnnxVoice

ov = OnnxVoice()
# Example conceptual API: adapt to the actual onnxvoice catalog data methods.
models = ov.list_voices()  # Qwen entries may be catalog items rather than named voices
installation = ov.install("qwen3:wavekat-base-0.6b", quality="int4")
with ov.open(installation, provider="cpu") as runtime:
    # Low-level model-specific adapter is called by qwen3synth.
    ...
```

**Important correction to the example:** Qwen VoiceDesign/Base entries are model bundles, not necessarily named voices. The `qwen3synth` discovery API should project installed catalog items and their capabilities, **not** fake a `VoiceRecord` for a Base model. A generated clone profile is a **user asset** held separately by `qwen3synth`/`onnxvoice` auxiliary cache, not a static catalog named voice.

Offline behavior:
- Metadata-only `models list`, `inspect`, and `check --offline` must not open graph sessions or download weights.
- An installed bundle is immutable against its pinned source revision; verify size/SHA on request/reopen under the existing `onnxvoice` policy.
- A local bundle can be opened by explicit role manifest without contacting the catalog.
- The Qwen runtime adapter rejects incompatible profiles, missing external data, unsupported graph layouts, or providers before executing generation.
- Cache reuse across VoiceDesign/Base or qualities is safe **only** for byte-identical blobs and role-specific compatibility; no silent metadata merging.

## 9. Model storage, performance, and licensing

- WaveKat's model card lists the VoiceDesign INT4 directory at approximately **4.27 GB** and the Base INT4 directory at approximately **2.2 GB**. Include **all** required tokenizer/embedding/shared FP32 files and physical storage overhead in install estimates. On-disk bundle size is not memory footprint.
- Published WaveKat FP32 variants are much larger. Choose INT4 as **installation default only after** an end-to-end parity/quality/CPU-provider test; otherwise label it recommended but leave default explicit.
- ONNX Runtime supports multiple providers in principle; actual ONNX operators and INT4 kernels must be proven for each graph/provider. Do not advertise Termux/Android, OpenVINO, or DirectML merely because `onnxvoice` has provider aliases.
- Keep source-code/catalog license separate from model weights and exported graph licenses. The supplied Pocket repo has MIT-authored metadata and its NOTICE explicitly excludes upstream artifacts; mirror this. Its existing `LICENSE` is Apache 2.0 text despite README describing repository metadata as MIT — **resolve and make the Qwen repository's LICENSE, README, NOTICE and SPDX headers internally consistent** rather than duplicating that inconsistency.
- Record copyright/attribution for original Qwen models, converter/exporter and individual bundled artifacts, including pretrained vocab. Do not add commercially restrictive terms that were not verified from the pinned source.

## 10. Milestones and acceptance tests

| Phase | Deliverable | Gate |
| --- | --- | --- |
| C0 | Source inventory and ABI evidence | Two pinned 40-hex WaveKat refs; complete file listing; all external data paths and role mappings documented |
| C1 | JSON Schema v1 and two curated entries | Only `wavekat-voice-design-1.7b` and `wavekat-base-0.6b`; exact roles and metadata; no placeholder hashes/sizes |
| C2 | `onnxvoice catalog qwen3` build/verify | Repeatable deterministic output; typed validation; offline structural checks; all URLs pinned |
| C3 | Integration with existing installer/cache | Install/open selected INT4 bundles, verify file integrity and external data adjacency, offline reopen |
| C4 | CI and scheduled refresh | PR validation blocks malformed/unverified entries; scheduled refresh submits reviewable PR |
| C5 | 0.1 catalog release | Both entries pass `qwen3synth` real-model smoke tests (voice design and voice clone) |
| C6, optional | Other exporters/model variants | Per-layout ABI parity, provenance and quality review before catalog promotion |

**Definition of done:** `onnxvoice` can list, select, download, integrity-check, install and open two Qwen3-TTS ONNX bundles from reproducible, immutable catalog entries; `qwen3synth` can discover their declared capabilities and use them to design and clone a synthetic reference voice *without installing or importing original Qwen Python tools*.

## 11. Risks to explicitly test

1. **External tensor data:** ONNX graph loading fails if graph/data paths are moved, incomplete or changed. Check in installer tests.
2. **Different exporter ABIs:** Names, tensor shapes, text embeddings, sampling behavior and voice-conditioning pipeline may vary. Never infer solely from `model_size`.
3. **Incomplete source checksums:** HF Xet/LFS metadata may need careful normalization and/or download hashing. Missing integrity data is a release blocker.
4. **Source churn:** Revisions can be deleted or reorganized; pinned references + provenance are mandatory, mirror only if license and storage policy explicitly permit.
5. **Large assets:** Online CI downloads can be expensive; reserve full validation for dedicated capacity.
6. **Quantized-provider mismatch:** Some INT4 operators may be CPU-specific or fallback unexpectedly. Provider-supported status must derive from real tests.
7. **User voice assets:** A 20s generated reference is **not** a bundled model or catalog asset. Do not store user recordings, transcripts or cloned speaker profiles here.

## 12. Source references

**Supplied source repository snapshots reconstructed with strict Codecrate checks:**
- `context_pocket_onnx_bundles.md` → `README.md`, `catalog/bundles.json`, `catalog/source.json`, `schemas/bundle-catalog.schema.json`, `.github/workflows/*`.
- `context_onnxvoice.md` → `docs/architecture.md`, `onnxvoice/catalog.py`, `onnxvoice/catalog_tools/`, `onnxvoice/manager.py`, `onnxvoice/store.py`, `onnxvoice/systems/`.
- `context_pocketsynth.md` → `docs/architecture.md`, `pocketsynth/discovery.py`, `pocketsynth/runtime.py`.

**Public evidence checked 2026-10-14:**
- [WaveKat VoiceDesign ONNX](https://huggingface.co/wavekat/Qwen3-TTS-1.7B-VoiceDesign-ONNX)
- [WaveKat 0.6B Base ONNX](https://huggingface.co/wavekat/Qwen3-TTS-0.6B-Base-ONNX)
- [xkos alternative ONNX bundle](https://huggingface.co/xkos/Qwen3-TTS-12Hz-1.7B-ONNX)
- [ONNX Community VoiceDesign](https://huggingface.co/onnx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign)
- [Official Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)

**Verification limitation:** This document reviews public model cards/repository trees and the user's supplied repositories. It does not claim to have downloaded full multi-gigabyte ONNX graphs or validated actual ONNX Runtime generation. C0 requires that proof before implementation treats the model layout as final.
