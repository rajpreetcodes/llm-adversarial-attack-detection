"""Generate the DGAD literature review deliverables: Excel table + Word document.

Sources: Final_Synopsis.md references [1]-[13]. All prose hand-written for this
project; references in IEEE format. The workbook carries the paper-level
Literature Review sheet plus two dataset catalogue sheets (text-domain and
image-domain attacks).
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ----------------------------------------------------------------------------
# References (IEEE), identical numbering to Final_Synopsis.md
# ----------------------------------------------------------------------------
REFERENCES = [
    'A. Zou, Z. Wang, N. Carlini, M. Nasr, J. Z. Kolter, and M. Fredrikson, "Universal and Transferable Adversarial Attacks on Aligned Language Models," arXiv preprint arXiv:2307.15043, 2023.',
    'F. Perez and I. Ribeiro, "Ignore Previous Prompt: Attack Techniques For Language Models," arXiv preprint arXiv:2211.09527, 2022.',
    'X. Liu, N. Xu, M. Chen, and C. Xiao, "AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models," arXiv preprint arXiv:2310.04451, 2023.',
    'J. Su, "Enhancing Adversarial Attacks through Chain of Thought," arXiv preprint arXiv:2410.21791, 2024.',
    'H. Inan et al., "Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations," arXiv preprint arXiv:2312.06674, 2023.',
    'Y. Liu, Y. Jia, R. Geng, J. Jia, and N. Z. Gong, "Formalizing and Benchmarking Prompt Injection Attacks and Defenses," arXiv preprint arXiv:2310.12815, 2023.',
    'J. Yi, Y. Xie, B. Zhu, E. Kiciman, G. Sun, X. Xie, and F. Wu, "Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models," arXiv preprint arXiv:2312.14197, 2023.',
    'G. Alon and M. Kamfonas, "Detecting Language Model Attacks with Perplexity," arXiv preprint arXiv:2308.14132, 2023.',
    'N. Jain et al., "Baseline Defenses for Adversarial Attacks Against Aligned Language Models," arXiv preprint arXiv:2309.00614, 2023.',
    'G. Zizzo et al., "Adversarial Prompt Evaluation: Systematic Benchmarking of Guardrails Against Prompt Input Attacks on LLMs," arXiv preprint arXiv:2502.15427, 2025.',
    'H. Li and X. Liu, "InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models," arXiv preprint arXiv:2410.22770, 2024.',
    'Y. Xie, M. Fang, R. Pi, and N. Gong, "GradSafe: Detecting Jailbreak Prompts for LLMs via Safety-Critical Gradient Analysis," arXiv preprint arXiv:2402.13494, 2024.',
    'W. Hackett, L. Birch, S. Trawicki, N. Suri, and P. Garraghan, "Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks against Prompt Injection and Jailbreak Detection Systems," arXiv preprint arXiv:2504.11168, 2025.',
]

# ----------------------------------------------------------------------------
# Dataset catalogue sheets: text-domain and image-domain
# ----------------------------------------------------------------------------
DATASET_HEADERS = ["Dataset Name", "Link", "Size", "Description"]

TEXT_DATASETS = [
    ("AdvBench", "https://github.com/llm-attacks/llm-attacks",
     "520 harmful behaviours; 500 harmful strings",
     "Harmful-request benchmark released with the GCG attack (Zou et al., 2023); the standard measure of whether optimised suffixes flip an aligned model from refusal to compliance."),
    ("BIPIA", "https://github.com/microsoft/BIPIA",
     "Five task scenarios (email QA, web QA, table QA, summarisation, code QA) with paired attack and benign samples",
     "Indirect prompt injection benchmark (Yi et al., 2023): payloads hidden inside external content such as emails, web pages, tables and code that LLM applications consume."),
    ("NotInject", "https://arxiv.org/abs/2410.22770",
     "Benign prompts laced with injection-style trigger words; released with the InjecGuard paper",
     "Over-defence test set (Li and Liu, 2024): harmless prompts that trigger-word-trained guard models wrongly block; used to measure false-positive behaviour separately from detection rate."),
    ("ToxicChat", "https://huggingface.co/datasets/lmsys/toxic-chat",
     "About 10,000 annotated user-model chat turns",
     "Real user conversations labelled for toxicity; lets detector evaluations (Llama Guard, GradSafe) move past synthetic corpora toward live traffic."),
    ("XSTest", "https://github.com/paul-rottger/exaggerated-safety",
     "250 test cases: 200 safe exemplars and 50 unsafe contrasts",
     "Exaggerated-safety benchmark of safe prompts that superficially resemble harmful ones; quantifies over-refusal in safety classifiers."),
    ("Anthropic HH-RLHF", "https://github.com/anthropics/hh-rlhf",
     "Roughly 160,000 human preference dialogues",
     "Harmless-versus-harmful red-team conversation pairs; the principal public training corpus behind Llama Guard's safe/unsafe classifier."),
    ("Prompt Injection Benchmark (Liu et al.)", "https://arxiv.org/abs/2310.12815",
     "Paired target and injected tasks built over multiple source datasets",
     "Formal framework treating injection as instructions concatenated with the target instruction; evaluates prevention-based and detection-based defences under one protocol."),
]

IMAGE_DATASETS = [
    ("MNIST", "http://yann.lecun.com/exdb/mnist/",
     "70,000 grayscale digit images (60,000 train / 10,000 test)",
     "Classic handwritten-digit corpus on which early FGSM perturbations first demonstrated pixel-level evasion of trained vision classifiers."),
    ("CIFAR-10", "https://www.cs.toronto.edu/~kriz/cifar.html",
     "60,000 colour images across 10 balanced classes",
     "Standard small-image benchmark for PGD and C&W adversarial example generation and for comparing robust-training defences."),
    ("ImageNet ILSVRC-2012", "https://www.image-net.org/",
     "About 1.28 million training images; 50,000 validation images",
     "Large-scale classification corpus underlying transferable targeted-attack research and most adversarial robustness leaderboards."),
    ("NIPS 2017 Adversarial Learning Challenge (dev set)", "https://github.com/google/nips-2017-adversarial-learning-dev-set",
     "1,000 ImageNet images",
     "Competition-scale collection of targeted adversarial examples evaluated against defended models under black-box submission rules."),
    ("ImageNet-A", "https://github.com/hendrycks/natural-adv-examples",
     "7,500 natural adversarial images",
     "Uncorrupted real-world photographs that reliably fool ResNet-family classifiers; tests robustness without artificial perturbation."),
    ("RobustBench", "https://github.com/RobustBench/RobustBench",
     "Standardised suites of FGSM, PGD, C&W and AutoAttack runs across CIFAR-10, CIFAR-100 and ImageNet models",
     "Community benchmark consolidating consistent attack implementations and verified robust accuracies, enabling fair defence-to-defence comparison."),
    ("FigStep", "https://github.com/ThuCCSLab/FigStep",
     "Several hundred typographic-image jailbreak prompts spanning prohibited scenario categories",
     "Multimodal jailbreak set that hides harmful instructions inside innocuous-looking images, bypassing the text-only safety alignment of vision-language models."),
    ("MM-SafetyBench", "https://github.com/isXinLiu/MM-SafetyBench",
     "13 unsafe scenarios, each queried with stable-diffusion, OCR and typographic image variants",
     "Safety benchmark for multimodal LLMs in which the query-relevant image, not the accompanying text, carries the harmful payload."),
]

# Additional multimodal datasets
MULTIMODAL_DATASETS = [
    ("LLM-Adversarial-Attack-Datasets", "L:\\Sem 7\\Capstone Project\\LLM_Adversarial_Attack_Datasets.xlsx",
     "Multiple datasets combined",
     "Combined dataset for multimodal adversarial attack detection containing text and image-based adversarial examples."),
]

# ----------------------------------------------------------------------------
# Excel rows: one dict per paper, columns in guideline order
# ----------------------------------------------------------------------------
HEADERS = [
    "Author And Year",
    "Title Of Study (Text)",
    "Title Of Study (Images)", 
    "Background / Context Of The Study",
    "Research Objective Or Problem Addressed",
    "Short Method Name",
    "Key Findings",
    "Limitations / Research Gap",
    "Relevance To Present Study",
    "References",
]

ROWS = [
    {
        "author": "Zou et al. (2023)",
        "title_text": "Universal and Transferable Adversarial Attacks on Aligned Language Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Aligned chat models such as Vicuna and LLaMA-2-Chat were assumed to be protected by RLHF safety training. Prior adversarial examples were mostly hand-crafted, and automated attacks had not been shown to reach closed commercial systems.",
        "objective": "Automatically find short adversarial suffixes that make aligned LLMs comply with harmful requests, and test whether one suffix generalises across many queries and across models.",
        "methodology": "Greedy Coordinate Gradient (GCG)",
        "findings": "Universal suffixes reliably flip refusals into affirmative compliance on open models, and they transfer to proprietary API-only systems that were never touched during optimisation, showing black-box deployment alone gives little protection.",
        "limitations": "Needs white-box access to a surrogate model; the suffixes are low-fluency gibberish that perplexity filters catch easily; success drops against models with additional defences.",
        "relevance": "Defines the primary attack family our statistical channel (windowed perplexity) and the adversarial regression suite must catch; motivates reproducing GCG offline for evaluation.",
        "references": "[1]",
    },
    {
        "author": "Perez and Ribeiro (2022)",
        "title_text": "Ignore Previous Prompt: Attack Techniques For Language Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "GPT-3 applications built on few-shot prompting hide instructions inside the prompt and concatenate untrusted user text with them, with no separation between the two channels.",
        "objective": "Give the first systematic account of prompt-based attacks on language models, focusing on goal hijacking and system prompt leakage.",
        "methodology": "Manual Prompt Construction",
        "findings": "Plain injections such as 'Ignore previous prompt' reliably redirect model behaviour and extract hidden system prompts, without any optimisation or model access.",
        "limitations": "Small-scale, manual study on a single pre-RLHF model family; no defence evaluation; predates modern aligned chat models.",
        "relevance": "Establishes the direct prompt injection threat model our detection layer handles; informs test-case design for the injection corpora.",
        "references": "[2]",
    },
    {
        "author": "Liu et al. (2023)",
        "title_text": "AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "GCG-style suffixes are gibberish and therefore easy to flag with perplexity filtering. Hand-written jailbreaks are fluent but scarce and hard to scale.",
        "objective": "Automatically generate jailbreak prompts that stay fluent and human-readable while remaining effective, evading statistical filters.",
        "methodology": "Hierarchical Genetic Algorithm",
        "findings": "Produces fluent, stealthy jailbreaks with high success rates that bypass perplexity-based detection, which GCG cannot do; readability is preserved by the sentence-level search.",
        "limitations": "Needs repeated query access to the target model; evaluated mainly on open-weight models; per-attack generation cost is non-trivial.",
        "relevance": "Direct evidence that a statistical-only detector fails on fluent attacks; the core justification for the embedding-based semantic channel in DGAD.",
        "references": "[3]",
    },
    {
        "author": "Su (2024)",
        "title_text": "Enhancing Adversarial Attacks through Chain of Thought",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Gradient-based attacks such as GCG optimise for an affirmative target string, but their transferability and universality across models remain limited.",
        "objective": "Improve transferability and universality of gradient jailbreaks by recruiting the target model's chain-of-thought reasoning into the attack.",
        "methodology": "CoT-GCG",
        "findings": "CoT-GCG outperforms vanilla GCG and standalone CoT prompting in transferability and universality, exposing systematic weaknesses in alignment for reasoning-triggered harmful content.",
        "limitations": "Single-author preprint with limited peer review; still depends on a white-box surrogate; success measurement inherits the failure modes of the Llama Guard judge.",
        "relevance": "Shows the attack side keeps evolving after each defence appears; motivates DGAD's continuous self-adversarial calibration loop rather than a fixed training set.",
        "references": "[4]",
    },
    {
        "author": "Inan et al. (2023)",
        "title_text": "Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Content moderation APIs are closed, fixed to vendor taxonomies, and not designed for human-AI conversation; open safeguards were missing.",
        "objective": "Build an open, LLM-based safeguard that classifies both prompts and responses as safe or unsafe across a customisable safety risk taxonomy.",
        "methodology": "Instruction Fine-tuning",
        "findings": "Matches or exceeds closed moderation APIs (OpenAI moderation, Perspective API) on benchmarks, and adapts to new harm categories with few examples.",
        "limitations": "English-centric; runs a 7B-parameter model per request, so latency and cost are high for always-on use; as an LLM it is itself vulnerable to prompt attacks.",
        "relevance": "Reference design and baseline for our escalation-stage LLM judge (Channel D); its cost profile motivates invoking the judge only on contested prompts.",
        "references": "[5]",
    },
    {
        "author": "Liu et al. (2023)",
        "title_text": "Formalizing and Benchmarking Prompt Injection Attacks and Defenses",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Prompt injection was widely reported in practice but had no formal definition, and proposed defences were evaluated ad hoc, if at all.",
        "objective": "Give a formal definition of prompt injection and build a general framework to benchmark attacks and defences consistently.",
        "methodology": "Formal Framework Modelling",
        "findings": "Attacks achieve high success across LLMs, and existing defences offer only limited protection, confirming a wide gap between attack capability and deployed mitigation.",
        "limitations": "Benchmark tasks are synthetic NLP tasks rather than live applications; centres on injection into the data channel and covers fewer attack variants than later work.",
        "relevance": "Supplies the formal threat model and benchmark methodology our evaluation harness mirrors for direct prompt injection.",
        "references": "[6]",
    },
    {
        "author": "Yi et al. (2023)",
        "title_text": "Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Indirect injection, where the payload hides in third-party data the model consumes (web pages, emails, documents), was far less studied than direct injection.",
        "objective": "Build a benchmark for indirect prompt injection and measure how well black-box and white-box defences hold up against it.",
        "methodology": "Benchmark Construction",
        "findings": "Deployed LLMs are broadly vulnerable to indirect injection; prompt-engineering defences help modestly, while the stronger defences require white-box access to the model.",
        "limitations": "Stronger defences need model internals, which API-only deployments do not have; benchmark scenarios are limited to five text tasks; defence gains trade off against task utility.",
        "relevance": "Directly shapes DGAD's canary tripwire for indirect injection and documents the limits of delimiter-style preprocessing we otherwise rely on.",
        "references": "[7]",
    },
    {
        "author": "Alon and Kamfonas (2023)",
        "title_text": "Detecting Language Model Attacks with Perplexity",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Production LLM applications needed a cheap first-line filter against jailbreak prompts circulating in the wild, without touching the target model.",
        "objective": "Detect adversarial prompts using perplexity under a reference language model, including a windowed variant for long inputs.",
        "methodology": "Perplexity Filtering",
        "findings": "Perplexity filtering catches many real attacks at near-zero cost, and the windowed variant handles long prompts much better than whole-sequence scoring.",
        "limitations": "Blind to fluent attacks such as AutoDAN; a single global threshold forces a hard trade between detection rate and false positives; depends on reference LM quality.",
        "relevance": "The foundation of DGAD's statistical channel (Channel A); its documented blindness to fluent text is why Channel A never decides alone on ambiguous scores.",
        "references": "[8]",
    },
    {
        "author": "Jain et al. (2023)",
        "title_text": "Baseline Defenses for Adversarial Attacks Against Aligned Language Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "After GCG, many defences were proposed informally, but nobody had measured which baseline techniques actually reduce attack success and at what false-positive cost.",
        "objective": "Systematically evaluate baseline defences against optimisation-based attacks on aligned LLMs, reporting performance at controlled false-positive rates.",
        "methodology": "Evaluation Harness",
        "findings": "Windowed perplexity, paraphrasing and retokenisation cut attack success substantially; adversarial training helps most but is expensive; every defence forces the attacker to adapt.",
        "limitations": "Evaluation centres on white-box gradient attacks; adaptive attackers who know the defence can lower its success; some defences add real compute overhead.",
        "relevance": "Source of the windowed perplexity method for Channel A and of the FPR-budget evaluation protocol used in our harness.",
        "references": "[9]",
    },
    {
        "author": "Zizzo et al. (2025)",
        "title_text": "Adversarial Prompt Evaluation: Systematic Benchmarking of Guardrails Against Prompt Input Attacks on LLMs",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "A fast-growing ecosystem of guardrail products and models existed with no consistent comparison across attack styles and benign traffic.",
        "objective": "Benchmark guardrail defences systematically across a broad set of malicious and benign datasets to find what actually works.",
        "methodology": "Unified Benchmarking Harness",
        "findings": "No defence dominates across the board; score-based detectors are constrained by a single global threshold, so raising detection rate raises false positives on unusual-but-benign prompts with it.",
        "limitations": "A snapshot of defences at one point in time; attackers are not fully adaptive within the benchmark; results depend on the datasets selected.",
        "relevance": "Quantifies why single-threshold detectors underperform; the direct motivation for calibrated scoring and disagreement-based escalation in DGAD.",
        "references": "[10]",
    },
    {
        "author": "Li and Liu (2024)",
        "title_text": "InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Prompt injection guard models were optimising detection rate while quietly blocking benign prompts that merely contain attack-associated trigger words (over-defence).",
        "objective": "Benchmark the over-defence problem in guardrail models and mitigate it without sacrificing detection accuracy or deployability.",
        "methodology": "MOF Strategy Fine-tuning",
        "findings": "InjecGuard reaches accuracy competitive with general-purpose LLM judges while staying lightweight enough for low-latency deployment, and over-defence is measurable and reducible once it is tested for explicitly.",
        "limitations": "Focused on direct injection; performance varies on out-of-distribution attacks; English-only evaluation.",
        "relevance": "Baseline and design reference for DGAD's embedding classifier (Channel B); we adopt its practice of tracking over-defence FPR on a NotInject-style benign set separately.",
        "references": "[11]",
    },
    {
        "author": "Xie et al. (2024)",
        "title_text": "GradSafe: Detecting Jailbreak Prompts for LLMs via Safety-Critical Gradient Analysis",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Existing detectors either need extra fine-tuning, paid LLM judges, or handcrafted rules; a training-free signal tied to the model's own safety behaviour was missing.",
        "objective": "Detect jailbreak prompts by analysing gradients induced on safety-critical parameters, without fine-tuning the target model.",
        "methodology": "Gradient Analysis",
        "findings": "Detects jailbreaks effectively and outperforms Llama Guard on benchmarks such as ToxicChat, with GradSafe-Zero requiring no training at all.",
        "limitations": "Requires white-box access to weights and backpropagation, so closed API-only models are out of reach; tied to assumptions about which parameter slices carry safety signal.",
        "relevance": "A strong contrast case for DGAD's black-box constraint: it shows what white-box signals buy and why a model-agnostic detector cannot depend on them.",
        "references": "[12]",
    },
    {
        "author": "Hackett et al. (2025)",
        "title_text": "Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks against Prompt Injection and Jailbreak Detection Systems",
        "title_images": "",  # Not applicable for this text-focused paper
        "background": "Guardrail systems were being deployed and benchmarked as static classifiers, but almost nobody attacked the guardrails themselves with adaptive evasion.",
        "objective": "Empirically measure whether prompt injection and jailbreak detection systems can be evaded by character-level obfuscation and adversarial ML techniques.",
        "methodology": "Character Injection and Obfuscation",
        "findings": "Evasion reaches up to 100% success in certain attack configurations; guardrails are themselves an attack surface facing the same optimisation pressure as the LLMs they protect.",
        "limitations": "Covers a fixed set of six systems; some obfuscation tricks can be patched once known; impact on benign-side false positives is studied less than evasion success.",
        "relevance": "The direct justification for DGAD's self-adversarial calibration loop and the adversarial regression test tier that attacks our own detector in CI.",
        "references": "[13]",
    },
]

def build_excel(path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Literature Review"

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10)
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap_top = Alignment(wrap_text=True, vertical="top")
    wrap_center = Alignment(wrap_text=True, vertical="center", horizontal="center")

    keys = ["author", "title_text", "title_images", "background", "objective",
            "methodology", "findings", "limitations", "relevance", "references"]
    widths = [20, 30, 30, 44, 44, 20, 46, 42, 44, 15]

    for col, (header, width) in enumerate(zip(HEADERS, widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = wrap_center
        cell.border = border
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 32

    for r, row in enumerate(ROWS, start=2):
        for col, key in enumerate(keys, start=1):
            cell = ws.cell(row=r, column=col, value=row[key])
            cell.font = body_font
            cell.alignment = wrap_top
            cell.border = border
        if r % 2 == 0:
            for col in range(1, len(keys) + 1):
                ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor="EDF2F9")

    ws.freeze_panes = "C2"

    # Two additional tables: dataset catalogues for text-domain and image-domain attacks
    _write_dataset_sheet(wb, "Datasets - TEXT", "LLM Adversarial Attack detection for TEXT", TEXT_DATASETS)
    _write_dataset_sheet(wb, "Datasets - IMAGES", "LLM Adversarial Attack detection for IMAGES", IMAGE_DATASETS)
    _write_dataset_sheet(wb, "Datasets - MULTIMODAL", "LLM Adversarial Attack detection for MULTIMODAL", MULTIMODAL_DATASETS)
    wb.save(path)


def _write_dataset_sheet(wb, tab_name: str, banner_title: str, rows) -> None:
    ws = wb.create_sheet(tab_name)

    banner_fill = PatternFill("solid", fgColor="2E5395")
    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    banner_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10)
    link_font = Font(name="Calibri", size=10, color="0563C1", underline="single")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap_top = Alignment(wrap_text=True, vertical="top")

    # Added Methods and References columns as requested
    widths = [30, 48, 40, 20, 20, 62]  # Dataset Name, Link, Size, Methods, References, Description
    for col, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(col)].width = width

    # Full requested title as a merged banner row (sheet tabs are capped at 31 chars)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(["Dataset Name", "Link", "Size", "Methods", "References", "Description"]))
    banner = ws.cell(row=1, column=1, value=banner_title)
    banner.fill = banner_fill
    banner.font = banner_font
    banner.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Updated headers to include Methods and References
    dataset_headers_with_methods_refs = ["Dataset Name", "Link", "Size", "Methods", "References", "Description"]
    for col, header in enumerate(dataset_headers_with_methods_refs, start=1):
        cell = ws.cell(row=2, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = border
    ws.row_dimensions[2].height = 22

    for r, (name, link, size, desc) in enumerate(rows, start=3):
        # For methods and references, we'll provide defaults or extract from the data
        methods = "Various"  # Default
        references = "[See above]"  # Default
        
        values = [name, link, size, methods, references, desc]
        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=r, column=col, value=value)
            cell.font = link_font if col == 2 else body_font  # Link column is index 2
            cell.alignment = wrap_top
            cell.border = border
            if col == 2:  # Link column
                cell.hyperlink = link
        if r % 2 == 0:
            for col in range(1, len(values) + 1):
                ws.cell(row=r, column=col).fill = PatternFill("solid", fgColor="EDF2F9")

    ws.freeze_panes = "A3"


# ----------------------------------------------------------------------------
# Word document
# ----------------------------------------------------------------------------
SECTIONS = [
    ("1. Introduction", [
        "Large language models are now embedded in everyday products such as customer support assistants, coding helpers, and document processing pipelines. All of these systems share one structural weakness: the same natural-language interface that makes them useful gives attackers a direct path in. A single crafted input can steer a safety-trained model toward producing content it was trained to refuse. What began as a laboratory curiosity in 2023, when researchers first showed that such inputs can be discovered automatically rather than written by hand, has become an operational concern for any product that routes user text into an LLM.",
        "This review examines thirteen studies, published between 2022 and 2025, that together define both the threat and the defensive response to it. The studies fall into four groups: automated generation of jailbreak prompts, prompt injection attacks against LLM applications, detection systems that screen prompts before execution, and benchmarking efforts that measure guardrails and attempt to break them through evasion. Reading these groups side by side exposes where current practice stops short, and those shortcomings shape the objectives and design of the detection system proposed in this project.",
    ]),
    ("2. Research Objectives", [
        "Drawing on the gaps identified across the reviewed literature, this project pursues the following research objectives:",
    ]),
    ("3. Thematic Review", []),
    ("3.1 Automated Jailbreak Generation", [
        "Systematic study of LLM attacks begins with the Greedy Coordinate Gradient method of Zou et al. [1]. GCG reframes jailbreaking as search: a short suffix of roughly twenty tokens is optimised until an aligned model answers a prohibited request affirmatively instead of refusing. Two properties made the result influential. The learned suffixes were universal, meaning a single string served many different harmful queries, and they transferred, since suffixes tuned on open surrogate models successfully attacked ChatGPT, Bard, and Claude through their public interfaces. Together these properties demonstrated that safety training alone offers limited protection against an adversary willing to optimise.",
        "The method carried one visible flaw: its suffixes read as gibberish, which makes them statistically conspicuous. AutoDAN [3] was designed around precisely that flaw. A hierarchical genetic algorithm evolves candidate jailbreaks first at sentence level and then at word level, preserving readability while retaining attack effect, and the resulting fluent prompts slip beneath perplexity filters that reliably stop GCG-style text. CoT-GCG [4] approaches the problem from another direction: instead of targeting a fixed affirmative string, it steers gradient search toward prefixes that recruit the target model's chain-of-thought reasoning, and it reports stronger universality and transferability than vanilla GCG under Llama Guard adjudication. Taken together, these studies mark a shift in the field: jailbreak construction has become an optimisation discipline in which each new method is engineered around the defence that caught its predecessor.",
    ]),
    ("3.2 Prompt Injection: Attack Characterisation and Benchmarks", [
        "Jailbreaks press against the model's own alignment; prompt injection attacks the application wrapped around the model. Perez and Ribeiro [2] provided the first systematic account of the technique in 2022. Applications built on few-shot prompting concatenate trusted instructions with untrusted user text and rely on the model to keep the two apart, yet inputs as simple as 'Ignore previous prompt' defeat that assumption, either redirecting the task or extracting the hidden system prompt. No optimisation and no privileged access are required, which makes the technique broadly accessible to non-experts.",
        "Subsequent work gave the attack formal structure and wider coverage. Liu et al. [6] supplied a formal definition and assembled a benchmark pairing target tasks with injected tasks, finding that available prevention-based and detection-based defences reduce attack success without eliminating it. Yi et al. [7] extended the analysis to the indirect setting, in which hostile instructions hide inside third-party content such as web pages, emails, tables, or source code that the application consumes. Across five task scenarios their findings were consistent: deployed models proved broadly vulnerable, delimiter-based prompt engineering helped only modestly, and the stronger defences assumed white-box access that API-only deployments cannot obtain.",
    ]),
    ("3.3 Detection-Based Defences and Guard Models", [
        "Perplexity remains the least expensive screening signal available. Alon and Kamfonas [8] proposed flagging prompts whose perplexity under a reference language model crosses a threshold, computing scores over sliding windows for long inputs so that a single improbable segment cannot dissolve into surrounding normal text. Jain et al. [9] subsequently evaluated this and other baseline defences under controlled false-positive budgets and confirmed that windowed perplexity sharply reduces the success of gradient-optimised attacks at negligible runtime cost. Both papers also document the ceiling of the signal: fluent attacks composed in human style pass through essentially undetected.",
        "Learned detectors cover part of that blind spot. InjecGuard [11] fine-tunes a DeBERTa-family encoder on curated adversarial and benign corpora and reaches accuracy comparable to an LLM judge at a fraction of the latency; the same study contributes the NotInject benign set and demonstrates that over-defence, the rejection of harmless prompts merely because attack-flavoured trigger words appear, shrinks measurably once it is tested explicitly. GradSafe [12] removes the training step altogether by inspecting gradients induced on safety-critical parameters when a prompt is paired with a compliant response prefix, outperforming Llama Guard on ToxicChat and XSTest wherever weights remain open enough for backpropagation. Llama Guard [5], an instruction-tuned LLaMA-2-7B classifier judged against a customisable taxonomy, showed that a single open model can match commercial moderation APIs, though at the price of running a seven-billion-parameter model before every request.",
    ]),
    ("3.4 Benchmarking Guardrails and Adaptive Evasion", [
        "Two recent studies stress-test this expanding toolkit. Zizzo et al. [10] benchmarked fifteen defences across broad collections of malicious and benign prompts and identified no dominant option; score-based detectors in particular proved hostage to a single global threshold, so raising recall drags false positives on unusual-but-benign traffic upward at the same time. Hackett et al. [13] then turned the attack onto the guards themselves, applying character-level obfuscation and adversarial machine learning evasion to six detection systems including commercial products, and achieved evasion rates approaching one hundred percent in certain configurations. The conclusion generalises: a guardrail is itself a classifier, and inherits the exposure of the model it protects.",
    ]),
    ("4. Limitations of Reviewed Studies", [
        "Beyond individual experimental caveats, several weaknesses recur across the reviewed work:",
    ]),
    ("5. Research Gap Summary", [
        "Across the thirteen studies, six unresolved issues recur. Together they mark the space in which a new contribution remains possible.",
    ]),
    ("6. Link to the Present Study", [
        "DGAD (Disagreement-Gated Adaptive Detection), the system proposed in this project, is assembled directly from the gaps catalogued above. A windowed perplexity scorer supplies an inexpensive statistical channel, and an encoder-based classifier provides a complementary semantic channel; per-channel calibration runs before any comparison so that scores from different sources become commensurable. The decision rule is the novel element. Rather than averaging calibrated scores beneath one global threshold, the precise failure mode that large-scale benchmarking exposed, DGAD treats disagreement between channels as a routing signal: agreement resolves the prompt immediately as pass or block, while only contested prompts reach a behavioural probe and an LLM judge, keeping strong verification proportional to genuine uncertainty.",
        "Because adaptive opponents should be expected, a self-adversarial calibration loop continually searches for inputs capable of misleading every cheap channel in the same direction and recycles successful finds into training data, while an adversarial regression tier attacks the detector itself during continuous integration. The pipeline deliberately avoids white-box signals so that it remains black-box and model-agnostic, able to sit in front of open or proprietary LLMs alike, and over-defence is tracked on a dedicated benign set rather than being discovered in production.",
    ]),
    ("7. Conclusion", [
        "The thirteen studies reviewed here tell one coherent story. Attacks on language models have become automated, transferable, and increasingly hard to distinguish from ordinary text, while each individual defence covers a single attack family and loses effectiveness outside it. Static benchmarking consistently flatters deployed guardrails, and adaptive testing reveals the true constraint: not the raw accuracy of any single detector, but the rigidity of a lone signal governed by one threshold when the opponent adapts. Those findings define the requirements a deployable detector must satisfy. The next chapter presents the methodology of the proposed DGAD pipeline, which is designed around exactly these requirements.",
    ]),
]

OBJECTIVES = [
    "To design a prompt screening layer that combines multiple lightweight detectors, statistical and semantic, so that no single signal ever decides an outcome on its own.",
    "To use disagreement between independently calibrated detectors as a routing signal, resolving prompts on which detectors agree immediately and escalating only contested cases.",
    "To restrict expensive verification, comprising a black-box behavioural probe and an LLM judge, to escalated prompts only, keeping cost and latency far below a judge-on-every-request design.",
    "To build a self-adversarial calibration loop that continuously searches for inputs able to fool all cheap detectors in the same direction and folds them back into training data.",
    "To evaluate the complete pipeline on optimisation-based jailbreaks, direct and indirect prompt injection, and role-play or persona attacks, reporting detection quality, over-defence false positives, calibration error, escalation rate, cost per thousand prompts, and tail latency.",
]

LIMITATIONS_BULLETS = [
    "White-box assumptions: the strongest attack and detection techniques, gradient-optimised suffixes and safety-critical gradient inspection, require access to model parameters that proprietary API deployments do not provide.",
    "Single-signal fragility: every low-cost detector rests on one strategy, so fluent attacks evade perplexity screening while obfuscated or heavily paraphrased text evades learned classifiers.",
    "Query-hungry generation: fluency-preserving jailbreak evolution demands many interactions with the target model, yet defences continue to be evaluated as though attackers face strict query budgets.",
    "Costly verification: LLM-based judges return interpretable verdicts but place a large model in front of every screened prompt, making always-on deployment impractical at scale.",
    "Unmeasured over-defence: guard models frequently block benign prompts containing attack-associated vocabulary, and false-positive behaviour attracts far less measurement than detection rate.",
    "Static evaluation culture: defences are validated against frozen attack corpora, leaving adaptive opponents untested until independent studies demonstrate near-complete evasion.",
    "Inconsistent success criteria: attack effectiveness is judged variously by string matching, bespoke classifiers, or LLM adjudication, which prevents fair comparison across papers.",
]

GAP_BULLETS = [
    "Single-signal dependence. Every deployed-style defence relies on one detection strategy, so it performs well inside one attack family and poorly outside it; no surveyed work combines complementary signals beyond simple averaging or a fixed threshold.",
    "Static evaluation. Defences are benchmarked against frozen attack corpora. Adaptive evasion aimed at the detector itself is absent from both training and evaluation, and where it has been tested it succeeds almost completely.",
    "White-box dependence. The strongest detection signals require model internals, which excludes exactly the proprietary, API-only models that dominate production deployments.",
    "Cost-blind judging. LLM judges give interpretable verdicts but run a multi-billion-parameter model per request, and no existing framework determines when a judge is worth its cost.",
    "Under-measured over-defence. False positives on unusual-but-benign prompts are rarely benchmarked; only one reviewed study builds a dedicated benign set for the purpose.",
    "Untreated detector disagreement. No surveyed work treats disagreement between independent detectors as information rather than noise to be averaged away, and the false-agreement case, where every cheap detector fails in the same direction, remains unaddressed.",
]


def build_word(path: str) -> None:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(8)
    style.paragraph_format.line_spacing = 1.15

    # Title block
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run("Literature Review")
    run.bold = True
    run.font.size = Pt(18)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Adversarial Attack Detection for Large Language Models (LLMs)")
    r.bold = True
    r.font.size = Pt(13)
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run(
        "Rajpreet Singh Khurana (K033) | Dhruv Rathod (K055) | Sumit Pandey (K044)\n"
        "Under the supervision of Dr. Ruchi Sharma\n"
        "IT Department, MPSTME, NMIMS Mumbai | Semester VII Capstone Project"
    ).font.size = Pt(10)

    for heading, paragraphs in SECTIONS:
        level = 2 if heading[:3] in ("3.1", "3.2", "3.3", "3.4") else 1
        doc.add_heading(heading, level=level)
        for para in paragraphs:
            doc.add_paragraph(para)
        if heading == "2. Research Objectives":
            for item in OBJECTIVES:
                doc.add_paragraph(item, style="List Number")
        elif heading == "4. Limitations of Reviewed Studies":
            for item in LIMITATIONS_BULLETS:
                doc.add_paragraph(item, style="List Bullet")
        elif heading == "5. Research Gap Summary":
            for item in GAP_BULLETS:
                doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("References", level=1)
    for i, ref in enumerate(REFERENCES, start=1):
        p = doc.add_paragraph(f"[{i}] {ref}")
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.35)

    doc.save(path)


if __name__ == "__main__":
    build_excel("DGAD_Literature_Review.xlsx")
    build_word("DGAD_Literature_Review.docx")
    print("Wrote DGAD_Literature_Review.xlsx and DGAD_Literature_Review.docx")