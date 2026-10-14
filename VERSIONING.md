# Versioning

`qwen3-onnx-bundles` is not a Python package and intentionally has no version constant.

- **Catalog ABI:** `catalog/bundles.json` → integer `schema`.
- **Catalog data releases:** Git tags, e.g. `v0.1.0`.
- **Development identity:** Git commit SHA.
- **Upstream bundle identity:** immutable 40-character source revision stored per bundle.

This avoids synchronizing a redundant file version with Git and mirrors the data-repository role of `pocket-onnx-bundles`.
