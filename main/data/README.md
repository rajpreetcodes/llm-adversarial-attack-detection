# Data directory

Datasets are NEVER committed. `raw/`, `interim/`, `processed/` are gitignored.
Rebuild everything with:

```bash
python -m dgad.eval.datasets --build --synthetic   # offline, deterministic
python -m dgad.eval.datasets --build               # real HF sources, needs network
```

## Unified schema

| Column | Meaning |
| :--- | :--- |
| `text` | the prompt |
| `label` | 0 benign, 1 attack |
| `attack_family` | none, gcg_optimised, jailbreak_roleplay, injection_direct, injection_indirect, obfuscation |
| `source` | dataset name, for per-source reporting |
| `split` | train, val, test, holdout (holdout locked until final evaluation) |
| `license` | source license, for citation |

Splits are grouped by attack family and source, never random. Dedup funnel
(total -> after quality filter -> after dedup -> final) is written to
`processed/funnel.json` on every build.

## Sources and licenses (real mode)

| Source | Use | License | Link |
| :--- | :--- | :--- | :--- |
| AdvBench (walledai) | GCG-style optimisation attacks | MIT | https://huggingface.co/datasets/walledai/AdvBench |
| JBB-Behaviors | curated misuse + matched benign | MIT | https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors |
| deepset prompt-injections | injection vs benign smoke test | Apache-2.0 | https://huggingface.co/datasets/deepset/prompt-injections |
| In-The-Wild Jailbreak Prompts | fluent human jailbreaks | research use | https://huggingface.co/datasets/TrustAIRLab/in-the-wild-jailbreak-prompts |
| Lakera Gandalf / Mosscap | player-submitted injections | CC-BY | https://huggingface.co/datasets/Lakera/gandalf_ignore_instructions |
| NotInject | trigger-word benign (over-defense) | research use | https://huggingface.co/datasets/leolee99/NotInject |
| Alpaca | benign instructions | CC0 | https://huggingface.co/datasets/tatsu-lab/alpaca |
| Dolly 15k | human-written benign instructions | CC-BY-SA-3.0 | https://huggingface.co/datasets/databricks/databricks-dolly-15k |
| BIPIA | indirect injection benchmark | MIT | https://github.com/microsoft/BIPIA |

Verify each license before redistributing anything; where redistribution is
not allowed, we ship the builder, not the data.

Download date and row-count funnel are recorded per build in
`processed/funnel.json`; cite those numbers, never raw row counts.

## Synthetic mode

`--synthetic` generates a deterministic benchmark from the project seed
covering every family, including NotInject-style trigger-word benign prompts
and deliberately hard cases (polite fluent attacks, emphatic benign prompts).
It exists so the pipeline, tests, CI, and demos run hermetically. Its numbers
are pipeline proof, not research results.
