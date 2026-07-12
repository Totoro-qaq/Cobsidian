# Cobsidian Quality Evaluations

The quality evaluator measures behavior, not only contract stability:

- duplicate precision and recall;
- append-target accuracy;
- backlink precision at `k` (default `3`);
- mode accuracy when host/model predictions are supplied.

## Dataset format

Datasets are JSONL files with one object per case:

```json
{"id":"rag","query":"RAG","material":"...","expected_action":"append","expected_target":"学习-RAG.md","expected_backlinks":["Embedding Models.md","Vector Search.md","Agent Workflows.md"],"expected_mode":"learning"}
```

`expected_backlinks` may be empty when a case is intended only for duplicate or
mode evaluation. Mode routing is performed by the active agent rather than the
deterministic helper scripts, so mode accuracy uses a separate JSONL predictions
file containing `id` and `mode`.

Do not copy labels into the predictions file and treat the resulting `1.0` as a
model result. The bundled predictions are only a parser/metric smoke fixture;
real mode evaluation must capture outputs from the host or model version under test.

## Public smoke evaluation

```bash
python skills/cobsidian/scripts/quality_eval.py \
  evals/public-smoke.jsonl \
  evals/fixtures/public-vault \
  --mode-predictions evals/public-mode-predictions.jsonl \
  --json
```

## Private real-vault evaluation

Put private datasets under `evals/private/`; that directory is ignored by Git.
Never commit real vault paths, private note titles, note bodies, or model
predictions derived from unpublished material.

```bash
python skills/cobsidian/scripts/quality_eval.py \
  evals/private/real-vault.jsonl \
  --config /absolute/path/to/cobsidian.config.yml \
  --mode-predictions evals/private/mode-predictions.jsonl \
  --json
```

Treat generated candidates as a labeling aid only. A human must verify the
expected action, target, three related notes, and mode before using a case as a
quality gate.
