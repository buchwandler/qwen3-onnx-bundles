# Catalog maintenance

The catalog contains normalized metadata for pinned WaveKat model revisions. The scheduled drift checker and manual rebuild workflow are read-only with respect to `catalog/bundles.json` and `catalog/source.json`. An upstream change is a review signal, not permission to update the snapshot automatically.

## When scheduled drift fails

Review the upstream change before preparing a catalog update:

1. Inspect upstream release notes and model-card changes.
2. Inspect the changed upstream file tree and identify additions, removals, or changed assets.
3. Do not change an existing catalog entry in place without reviewing the compatibility and artifact consequences.
4. Update the source seed or pinned revision through the supported ONNXVoice catalog tooling.
5. Rebuild the normalized catalog from the reviewed pinned sources.
6. Inspect the `bundles.json` and `source.json` diffs, including artifact inventory, sizes, hashes, and revisions.
7. Run the independent catalog verifier.
8. Run the released-consumer verifier using the ONNXVoice release intended for this catalog update.
9. Rerun the ONNXVoice real-model gate if graph, tokenizer, or runtime assets changed.
10. Merge and tag the catalog update only after the preceding review and checks pass.

The drift checker never edits catalog files. Its nonzero result means a maintainer should perform this review.

## Release validation commands

Run these from the repository root. The released consumer for the initial catalog release is ONNXVoice 0.2.8.

```bash
python scripts/verify_catalog.py

python -m pip install "onnxvoice==0.2.8"
onnxvoice catalog qwen3 verify \
  --catalog catalog/bundles.json \
  --source catalog/source.json

python scripts/check_upstream_drift.py
```

A drift-check failure is expected when a pinned upstream repository has moved. Do not treat that failure as a request to rewrite the catalog automatically.

To reproduce the normalized snapshot against the pinned sources, use the released builder and compare both outputs:

```bash
onnxvoice catalog qwen3 build \
  --output /tmp/qwen3-bundles.json \
  --source-output /tmp/qwen3-source.json
cmp /tmp/qwen3-bundles.json catalog/bundles.json
cmp /tmp/qwen3-source.json catalog/source.json
```

The manual `qwen3-catalog-rebuild` workflow runs this rebuild and comparison using the pinned released consumer.

## Repository boundary

This is a catalog-only repository. It contains:

- no Python package;
- no downloader;
- no ONNX Runtime;
- no model mirror;
- no generated voices.

Do not add model weights, generated audio, caches, or runtime implementation here. ONNXVoice owns bundle acquisition, integrity verification, runtime, and inference.
