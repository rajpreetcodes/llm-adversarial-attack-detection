# Graph Report - .  (2026-08-23)

## Corpus Check
- 92 files · ~71,749 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 570 nodes · 1304 edges · 38 communities detected
- Extraction: 48% EXTRACTED · 52% INFERRED · 0% AMBIGUOUS · INFERRED: 672 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Channel Base Abstractions|Channel Base Abstractions]]
- [[_COMMUNITY_Calibration Pipeline|Calibration Pipeline]]
- [[_COMMUNITY_Statistical Channel & Adversarial Mutators|Statistical Channel & Adversarial Mutators]]
- [[_COMMUNITY_Alembic Database Migrations|Alembic Database Migrations]]
- [[_COMMUNITY_Behavioural Probe & Judge Channel|Behavioural Probe & Judge Channel]]
- [[_COMMUNITY_Disagreement Gate Logic|Disagreement Gate Logic]]
- [[_COMMUNITY_Architecture & Literature Concepts|Architecture & Literature Concepts]]
- [[_COMMUNITY_Canary Tripwire Module|Canary Tripwire Module]]
- [[_COMMUNITY_Core Schemas & Caching|Core Schemas & Caching]]
- [[_COMMUNITY_Evaluation Metrics & Reporting|Evaluation Metrics & Reporting]]
- [[_COMMUNITY_Dataset Building & Splitting|Dataset Building & Splitting]]
- [[_COMMUNITY_Offset Channel (Intent Distance)|Offset Channel (Intent Distance)]]
- [[_COMMUNITY_Text Normalisation|Text Normalisation]]
- [[_COMMUNITY_Configuration & Settings|Configuration & Settings]]
- [[_COMMUNITY_Package Init Files|Package Init Files]]
- [[_COMMUNITY_Dashboard Mock Data|Dashboard Mock Data]]
- [[_COMMUNITY_Evaluation Datasets & Ablation|Evaluation Datasets & Ablation]]
- [[_COMMUNITY_Alembic Initial Migration|Alembic Initial Migration]]
- [[_COMMUNITY_Dashboard API Client|Dashboard API Client]]
- [[_COMMUNITY_Dashboard Live Feed|Dashboard Live Feed]]
- [[_COMMUNITY_Dashboard Hooks|Dashboard Hooks]]
- [[_COMMUNITY_Prompt Injection Literature|Prompt Injection Literature]]
- [[_COMMUNITY_Dashboard PostCSS Config|Dashboard PostCSS Config]]
- [[_COMMUNITY_Dashboard Tailwind Config|Dashboard Tailwind Config]]
- [[_COMMUNITY_Dashboard Vite Config|Dashboard Vite Config]]
- [[_COMMUNITY_Dashboard App Root|Dashboard App Root]]
- [[_COMMUNITY_Dashboard Entry Point|Dashboard Entry Point]]
- [[_COMMUNITY_Dashboard Theme|Dashboard Theme]]
- [[_COMMUNITY_Disagreement Scatter Plot|Disagreement Scatter Plot]]
- [[_COMMUNITY_Escalation Funnel Chart|Escalation Funnel Chart]]
- [[_COMMUNITY_Family Breakdown Chart|Family Breakdown Chart]]
- [[_COMMUNITY_Prompt Detail View|Prompt Detail View]]
- [[_COMMUNITY_Dashboard Stat Cards|Dashboard Stat Cards]]
- [[_COMMUNITY_Threshold Playground|Threshold Playground]]
- [[_COMMUNITY_Tests Root Init|Tests Root Init]]
- [[_COMMUNITY_Adversarial Tests Init|Adversarial Tests Init]]
- [[_COMMUNITY_Integration Tests Init|Integration Tests Init]]
- [[_COMMUNITY_Unit Tests Init|Unit Tests Init]]

## God Nodes (most connected - your core abstractions)
1. `Settings` - 125 edges
2. `ChannelResult` - 63 edges
3. `Channel` - 53 edges
4. `StatisticalChannel` - 41 edges
5. `DisagreementGate` - 39 edges
6. `SemanticChannel` - 35 edges
7. `DetectionPipeline` - 34 edges
8. `BehaviouralChannel` - 32 edges
9. `OffsetChannel` - 32 edges
10. `Decision` - 31 edges

## Surprising Connections (you probably didn't know these)
- `Llama Guard [5]` --semantically_similar_to--> `Channel D: LLM-as-a-Judge`  [INFERRED] [semantically similar]
  Final_Synopsis.md → main/docs/viva_prep.md
- `Score calibration layer (final_plan.md Phase 4).  Raw channel scores live on dif` --uses--> `Settings`  [INFERRED]
  main\src\dgad\calibration.py → main\src\dgad\config.py
- `Expected Calibration Error: mean gap between confidence and accuracy.` --uses--> `Settings`  [INFERRED]
  main\src\dgad\calibration.py → main\src\dgad\config.py
- `Per-channel score calibrator: Platt (sigmoid) or isotonic.      Platt suits smal` --uses--> `Settings`  [INFERRED]
  main\src\dgad\calibration.py → main\src\dgad\config.py
- `Fit on validation-split raw scores and binary labels.` --uses--> `Settings`  [INFERRED]
  main\src\dgad\calibration.py → main\src\dgad\config.py

## Hyperedges (group relationships)
- **Cheap Detection Channels (A, B, E)** — channel_a_statistical, channel_b_semantic, channel_e_offset [EXTRACTED 1.00]
- **Expensive Verification Channels (C, D)** — channel_c_behavioural, channel_d_judge, canary_tripwire [EXTRACTED 1.00]
- **Target Attack Categories** — gcg_attack, prompt_injection, roleplay_jailbreak [EXTRACTED 1.00]

## Communities

### Community 0 - "Channel Base Abstractions"
Cohesion: 0.08
Nodes (50): ABC, Channel, The Channel contract. THIS MUST NOT BE BROKEN.  Every detection channel (A stati, Abstract detection channel., Score one normalised prompt.          Args:             text: The prompt after n, BaseSettings, Channel C: black-box behavioural probe (final_plan.md Phase 6).  An optimised at, True when the response looks like a refusal. (+42 more)

### Community 1 - "Calibration Pipeline"
Cohesion: 0.07
Nodes (47): Calibrator, expected_calibration_error(), Score calibration layer (final_plan.md Phase 4).  Raw channel scores live on dif, Expected Calibration Error: mean gap between confidence and accuracy., Per-channel score calibrator: Platt (sigmoid) or isotonic.      Platt suits smal, Fit on validation-split raw scores and binary labels., Map raw scores to calibrated probabilities in [0, 1]., Persist alongside the channel it calibrates (versioned by name). (+39 more)

### Community 2 - "Statistical Channel & Adversarial Mutators"
Cohesion: 0.06
Nodes (40): char_drop(), char_swap(), printable_junk(), random_mutation(), Meaning-preserving mutation operators (final_plan.md Phase 6 step 1).  Used by t, Swap adjacent characters at the given rate (typo simulation)., Delete characters at the given rate (never whitespace-adjacent ends)., Randomly add/remove spaces and punctuation, preserving words. (+32 more)

### Community 3 - "Alembic Database Migrations"
Cohesion: 0.06
Nodes (35): DeclarativeBase, Alembic environment: wired to dgad.storage.models.Base metadata., create_app(), get_app_settings(), get_pipeline(), lifespan(), FastAPI application: detection API, OpenAI-compatible proxy, admin routes., API-key auth; disabled when DGAD_API_KEY/api_key is unset (dev only). (+27 more)

### Community 4 - "Behavioural Probe & Judge Channel"
Cohesion: 0.09
Nodes (30): BehaviouralChannel, is_refusal(), ollama_probe(), _BoundedCache, _call_provider(), JudgeChannel, _make_provider(), MockProvider (+22 more)

### Community 5 - "Disagreement Gate Logic"
Cohesion: 0.09
Nodes (39): disagreement(), DisagreementGate, effective_score(), max_fusion(), mean_fusion(), The disagreement gate. CORE NOVELTY of DGAD.  Prior systems fuse detector scores, Naive baseline: take the most suspicious channel, threshold at 0.5., One scalar per prompt for ranking metrics, honouring the gate.      PASS/BLOCK p (+31 more)

### Community 6 - "Architecture & Literature Concepts"
Cohesion: 0.07
Nodes (38): AutoDAN Fluent Jailbreaks [3], Calibration Layer, Canary Tripwire (Indirect Injection), Channel A: Statistical Perplexity, Channel B: Semantic Embedding Classifier, Channel C: Behavioural Probe, Channel D: LLM-as-a-Judge, Channel E: Representation Offset (+30 more)

### Community 7 - "Canary Tripwire Module"
Cohesion: 0.08
Nodes (33): build_wrapper(), CanaryResult, CanaryStatus, check_response(), generate_token(), load_bipia(), Canary tripwire for indirect prompt injection (final_plan.md Phase 9).  When unt, Outcome of checking one response against its canary. (+25 more)

### Community 8 - "Core Schemas & Caching"
Cohesion: 0.12
Nodes (27): BaseModel, BoundedCache, In-process detection cache when Redis is not configured., OrderedDict, default_channels(), DetectionPipeline, load_calibrators(), The detection pipeline: one request's journey, end to end.  normalise -> cheap c (+19 more)

### Community 9 - "Evaluation Metrics & Reporting"
Cohesion: 0.08
Nodes (30): bootstrap_auc_ci(), cost_per_1000(), detection_metrics(), latency_percentiles(), per_family(), Evaluation metrics (final_plan.md Phase 13).  Every headline number carries a bo, The full detection-quality bundle at one operating threshold., Bootstrap CI on ROC-AUC (>= 1000 resamples per the plan). (+22 more)

### Community 10 - "Dataset Building & Splitting"
Cohesion: 0.11
Nodes (23): build(), clean_and_dedup(), group_split(), _hf_frame(), load_real(), main(), Dataset layer (final_plan.md Phase 1).  One unified schema across every source:, Generic Hugging Face loader into the unified schema (ungrouped). (+15 more)

### Community 11 - "Offset Channel (Intent Distance)"
Cohesion: 0.2
Nodes (14): Channel, _cosine_distance(), heuristic_intent_extractor(), OffsetChannel, ollama_intent_extractor(), axis_embedder(), Tests for Channel E (representation offset). Fakes only, no downloads., Embed by keyword: 'harmful' pulls axis 0, everything else axis 1. (+6 more)

### Community 12 - "Text Normalisation"
Cohesion: 0.22
Nodes (7): demo(), normalise(), Prompt normalisation and de-obfuscation.  Runs before any channel sees the text:, Normalise a prompt before detection.      Steps, in order:     1. NFKC Unicode n, Self-check: prove idempotence and show the pipeline on a tricky input., test_channel_contract_exists(), test_normalise_idempotent()

### Community 13 - "Configuration & Settings"
Cohesion: 0.2
Nodes (3): get_settings(), Central configuration for DGAD.  Project rule: ALL thresholds and tunables live, Construct a Settings instance from the environment and .env file.

### Community 14 - "Package Init Files"
Cohesion: 0.29
Nodes (1): Persistence layer: SQLAlchemy models, Alembic migrations, audit log repository.

### Community 15 - "Dashboard Mock Data"
Cohesion: 0.7
Nodes (4): mockDecisions(), mockMetrics(), mockPlayground(), mulberry32()

### Community 16 - "Evaluation Datasets & Ablation"
Cohesion: 0.4
Nodes (5): 12-Config Ablation Study, AdvBench Dataset, Holdout Split Discipline, NotInject Dataset (over-defense), Synthetic Evaluation Mode

### Community 17 - "Alembic Initial Migration"
Cohesion: 0.5
Nodes (1): 0001: initial audit_log table.  Revision ID: 0001_initial Revises: Create Date:

### Community 18 - "Dashboard API Client"
Cohesion: 0.5
Nodes (0): 

### Community 19 - "Dashboard Live Feed"
Cohesion: 0.67
Nodes (0): 

### Community 20 - "Dashboard Hooks"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Prompt Injection Literature"
Cohesion: 1.0
Nodes (2): Perez & Ribeiro Prompt Injection [2], Prompt Injection Attack

### Community 22 - "Dashboard PostCSS Config"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Dashboard Tailwind Config"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Dashboard Vite Config"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Dashboard App Root"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Dashboard Entry Point"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Dashboard Theme"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Disagreement Scatter Plot"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Escalation Funnel Chart"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Family Breakdown Chart"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Prompt Detail View"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Dashboard Stat Cards"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Threshold Playground"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Tests Root Init"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Adversarial Tests Init"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Integration Tests Init"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Unit Tests Init"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **71 isolated node(s):** `Generate the DGAD literature review deliverables: Excel table + Word document.`, `0001: initial audit_log table.  Revision ID: 0001_initial Revises: Create Date:`, `Load a persisted calibrator.`, `Canary tripwire for indirect prompt injection (final_plan.md Phase 9).  When unt`, `Outcome of checking one response against its canary.` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Dashboard Hooks`** (2 nodes): `useCountUp()`, `hooks.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prompt Injection Literature`** (2 nodes): `Perez & Ribeiro Prompt Injection [2]`, `Prompt Injection Attack`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard PostCSS Config`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard Tailwind Config`** (1 nodes): `tailwind.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard Vite Config`** (1 nodes): `vite.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard App Root`** (1 nodes): `App.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard Entry Point`** (1 nodes): `main.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard Theme`** (1 nodes): `theme.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Disagreement Scatter Plot`** (1 nodes): `DisagreementScatter.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Escalation Funnel Chart`** (1 nodes): `EscalationFunnel.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Family Breakdown Chart`** (1 nodes): `FamilyBreakdown.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prompt Detail View`** (1 nodes): `PromptDetail.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Dashboard Stat Cards`** (1 nodes): `StatCards.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Threshold Playground`** (1 nodes): `ThresholdPlayground.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tests Root Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Adversarial Tests Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Integration Tests Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Unit Tests Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Channel Base Abstractions` to `Calibration Pipeline`, `Statistical Channel & Adversarial Mutators`, `Alembic Database Migrations`, `Behavioural Probe & Judge Channel`, `Disagreement Gate Logic`, `Canary Tripwire Module`, `Core Schemas & Caching`, `Evaluation Metrics & Reporting`, `Dataset Building & Splitting`, `Offset Channel (Intent Distance)`, `Configuration & Settings`?**
  _High betweenness centrality (0.367) - this node is a cross-community bridge._
- **Why does `summarise()` connect `Evaluation Metrics & Reporting` to `Calibration Pipeline`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `StatisticalChannel` connect `Statistical Channel & Adversarial Mutators` to `Channel Base Abstractions`, `Calibration Pipeline`, `Core Schemas & Caching`, `Evaluation Metrics & Reporting`, `Offset Channel (Intent Distance)`, `Configuration & Settings`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 121 inferred relationships involving `Settings` (e.g. with `Calibrator` and `Score calibration layer (final_plan.md Phase 4).  Raw channel scores live on dif`) actually correct?**
  _`Settings` has 121 INFERRED edges - model-reasoned connections that need verification._
- **Are the 60 inferred relationships involving `ChannelResult` (e.g. with `DetectionPipeline` and `The detection pipeline: one request's journey, end to end.  normalise -> cheap c`) actually correct?**
  _`ChannelResult` has 60 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `Channel` (e.g. with `DetectionPipeline` and `The detection pipeline: one request's journey, end to end.  normalise -> cheap c`) actually correct?**
  _`Channel` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `StatisticalChannel` (e.g. with `DetectionPipeline` and `The detection pipeline: one request's journey, end to end.  normalise -> cheap c`) actually correct?**
  _`StatisticalChannel` has 32 INFERRED edges - model-reasoned connections that need verification._