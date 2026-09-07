---
source: Final_Synopsis.pdf
total_pages: 11
extracted_at: 2026-07-20
extraction_method: vision OCR (PDF is scanned, no text layer)
---

# SVKM's NMIMS
## Mukesh Patel School of Technology Management & Engineering (Mumbai Campus)
### IT DEPARTMENT

# Project Synopsis

**Title of Project:** Adversarial Attack Detection for Large Language Models (LLMs)

**Team Members:** Sumit Pandey | Dhruv Rathod | Rajpreet Khurana

**Under the supervision of:** Dr. Ruchi Sharma

---

## Table of Contents

| # | Section | Page |
|---|---------|------|
| 1 | Title of the Project: Adversarial Attack Detection for Large Language Models (LLMs) | 3 |
| 2 | Team Members | 3 |
| 3 | Introduction | 3 |
| 4 | Literature Survey | 4 |
| 4.1 | Research Gap | 6 |
| 5 | Why are this particular topic chosen? | 6 |
| 6 | Objective and Scope of the project | 7 |
| 6.1 | Evaluation Metrics | 8 |
| 7 | Hardware and Software Requirements | 9 |
| 7.1 | Hardware (Minimum Requirements) | 9 |
| 7.2 | Software | 9 |
| 7.2.1 | Frontend | 9 |
| 7.2.2 | Backend | 9 |
| 7.2.3 | Additional | 9 |
| 8 | Final Deliverables | 10 |
| 9 | References | 10 |

---

## 1. Title of the Project: Adversarial Attack Detection for Large Language Models (LLMs)

## 2. Team Members

1. Rajpreet Singh Khurana (K033)
2. Dhruv Rathod (K055)
3. Sumit Pandey (K044)

## 3. Introduction

The rapid integration of Large Language Models (LLMs) such as GPT-4, Claude, and Ollama into customer support systems, code assistants, healthcare triage tools, and enterprise chatbots has transformed how organisations interact with data and users. However, this widespread deployment has simultaneously exposed a new and rapidly growing attack surface. Unlike traditional software vulnerabilities that are exploited through code injection or buffer overflows, LLMs are vulnerable to adversarial manipulation of natural language itself: inputs that are crafted, often algorithmically, to bypass safety alignment and coerce a model into producing harmful, biased, or unauthorised outputs.

Researchers have demonstrated that carefully optimised adversarial suffixes appended to an otherwise harmless-looking prompt can reliably cause aligned, safety-trained models to comply with harmful requests, and that such suffixes transfer across different model families and vendors, including proprietary systems accessed only through an API [1]. Beyond these gradient-based jailbreaks, a parallel and equally serious class of attack, prompt injection, allows an adversary to hijack the intended behaviour of an LLM-integrated application by embedding malicious instructions inside untrusted data that the model processes, such as a web page, an email, or a retrieved document [2]. As LLMs are increasingly wired with tool access, file systems, and browsing capability, the consequences of an undetected adversarial input escalate from an embarrassing generation to a significant security incident involving data exfiltration, unauthorised transactions, or system compromise.

Despite the seriousness of this threat, most production deployments still rely on ad-hoc, static keyword filters or the base alignment of the underlying model, both of which have been repeatedly shown to be brittle and easily evaded through paraphrasing, encoding tricks, role-play framing, and optimisation-based search. Recognising this gap, we propose the development of an Adversarial Attack Detection tool for LLMs: a model-agnostic, pluggable security layer capable of identifying jailbreak attempts, prompt injection payloads, and other adversarially perturbed inputs before they reach a production LLM, and of flagging anomalous or unsafe outputs before they reach an end user. By combining statistical signal analysis (such as perplexity and token-distribution anomalies), embedding-based semantic classifiers, and lightweight guard models, our solution aims to give developers and organisations a practical, low-latency way to harden their LLM-integrated applications against an evolving and increasingly automated class of attacks, without needing to retrain or fine-tune the underlying foundation model itself.

## 4. Literature Survey

The vulnerability of aligned language models to automated adversarial jailbreak attacks was demonstrated most prominently by Zou et al., who introduced the Greedy Coordinate Gradient (GCG) attack [1]. GCG automatically searches for a short adversarial suffix that, when appended to a harmful query, maximises the probability that the model responds with an affirmative completion rather than a refusal. The attack combines greedy and gradient-based token search over a white-box surrogate model, and the resulting suffixes were shown to transfer with high success rates not only across open-source models such as Vicuna and LLaMA-2-Chat, but also to public interfaces of closed, proprietary systems including ChatGPT, Bard, and Claude, despite none of these systems being directly optimised against during the attack [1]. This transferability result was significant because it demonstrated that an attacker with no access to a target model's weights could still mount an effective, automated jailbreak, fundamentally challenging the assumption that black-box deployment alone provides meaningful protection.

Follow-up work has continued to refine both the offensive and interpretability aspects of these attacks. AutoDAN, for instance, uses a hierarchical genetic algorithm to generate adversarial prompts that remain fluent and human-readable, allowing them to bypass simple perplexity-based filters that flag the low-fluency suffixes typical of GCG [3]. More recent work on Chain-of-Thought-guided gradient search (CoT-GCG) explores the integration of reasoning-based triggers with GCG attacks and demonstrates improved transferability and universality compared to baseline approaches [4], and that evaluations using safety classifiers such as Llama Guard [5] reveal systematic weaknesses in current alignment pipelines for specific categories of harmful content. Collectively, this body of work establishes that jailbreak generation is no longer a manual, ad-hoc process reliant on human ingenuity, but an increasingly automated optimisation problem, raising the urgency for equally automated, generalisable detection mechanisms.

A second major thread of research addresses prompt injection, a distinct but related threat first formally characterised by Perez and Ribeiro, who showed that LLMs can be misled by simple, crafted inputs embedded within otherwise legitimate data, resulting in goal hijacking and system prompt leakage [2]. Because LLM-integrated applications frequently concatenate trusted developer instructions with untrusted third-party content (web pages, documents, emails, tool outputs), an attacker can smuggle instructions directly into the data channel, a problem that has no direct analogue in traditional software security and is difficult to fully resolve through input sanitisation alone [6].

On the defensive side, the literature broadly separates mitigation strategies into prevention-based and detection-based approaches [6]. Prevention-based defences attempt to pre-process instructions and data, for example through the delimiter-based separation of prompts and data explored by Yi et al. [7], or by fine-tuning the base model to be more resistant to injected instructions, but such techniques have shown only limited effectiveness against adaptive attacks and often degrade general model utility [6][7]. Detection-based defences, which are the primary focus of this project, instead treat the incoming prompt (or the model's response) as a signal to be classified as benign or adversarial. The earliest and most widely studied of these is perplexity-based filtering, proposed by Alon and Kamfonas [8] and extended by Jain et al. through a windowed perplexity approach that computes perplexity over sliding segments of the prompt rather than the sequence as a whole, since optimisation-based suffixes such as those produced by GCG tend to be locally low-probability under a reference language model even when the surrounding prompt is fluent [9].

While effective against gradient-based, low-fluency suffixes, perplexity filtering alone generalises poorly: benchmarking work evaluating guardrails such as Azure Prompt Shield and Meta's Prompt Guard across multiple jailbreak styles has shown that score-based detectors are limited by a single global threshold and struggle to balance true-positive detection against false positives on legitimate, unusual-but-benign prompts [10]. This has motivated a shift towards learned classifiers: embedding-based approaches encode a prompt using a pretrained language model and train a lightweight classifier (e.g., logistic regression, random forest, or a small transformer head) on top of the resulting representation, which has been shown to detect semantically disguised injection attempts that perplexity-based methods miss entirely [10]. Purpose-built guard models such as Meta's Prompt Guard, ProtectAI's DeBERTa-based classifiers, and InjecGuard extend this idea further, fine-tuning encoder models specifically on curated corpora of benign and adversarial prompts; InjecGuard in particular reports accuracy competitive with general-purpose LLM judges while remaining lightweight enough for low-latency deployment, and explicitly addresses the over-defence problem in which guard models misclassify benign prompts that merely contain attack-associated trigger words [11]. A related line of work, GradSafe, analyses the gradients induced by a prompt paired with a compliant response to identify safety-critical patterns without requiring any additional fine-tuning of the target model [12].

Nevertheless, recent adversarial evaluations caution that no single defence is currently robust in isolation. An empirical study testing six prominent guardrail systems, including commercial offerings, found that character-level obfuscation and algorithmic adversarial machine learning evasion techniques achieved up to 100% evasion success in certain attack configurations, demonstrating that existing guardrail systems remain vulnerable to adaptive evasion techniques in some configurations, underscoring that guardrails themselves constitute an attack surface subject to the same optimisation pressures as the underlying LLMs they protect [13].

This finding directly motivates our project's approach of layering multiple complementary detection signals (statistical, embedding-based, and LLM-judge-based) rather than depending on any single detector, and of continuously benchmarking the tool against an evolving adversarial test suite, including evasion attempts directed at the detector itself, rather than treating detection as a solved, static classification problem.

### 4.1. Research Gap

The existing literature demonstrates that Large Language Models (LLMs) are highly susceptible to adversarial attacks such as optimisation-based jailbreaks and prompt injection. While numerous defence mechanisms have been proposed, including perplexity-based filtering, embedding-based classifiers, specialised guard models, and prompt engineering techniques, most existing approaches rely on a single detection strategy and are therefore effective only against specific categories of attacks. Recent studies further show that adaptive adversarial techniques, including paraphrasing, character obfuscation, and fluent jailbreak generation, can successfully evade many current guardrail systems. In addition, several state-of-the-art solutions are proprietary, model-specific, or require white-box access to the target model, limiting their applicability in real-world deployments.

Therefore, there remains a need for a lightweight, model-agnostic detection framework capable of combining multiple complementary detection signals to improve robustness against diverse and evolving adversarial attacks. The proposed project addresses this gap by integrating statistical analysis, embedding-based semantic classification, and an optional LLM-as-a-judge verification stage within a unified detection pipeline. By operating independently of the underlying LLM and evaluating its performance against both established adversarial benchmarks and adaptive evasion techniques, the proposed system aims to provide a practical, scalable, and deployable security layer for modern LLM-powered applications.

## 5. Why are this particular topic chosen?

The past two years have seen an unprecedented rate of LLM adoption across customer-facing products, internal enterprise tools, and increasingly autonomous agentic systems that can browse the web, execute code, and take actions on a user's behalf. This shift dramatically raises the stakes of an undetected adversarial prompt: a jailbreak that once merely produced an inappropriate paragraph of text can now, in an agentic context, translate into an unauthorised file deletion, a leaked API key, or a fraudulent transaction. Security teams and AI safety researchers alike have identified adversarial robustness as one of the most urgent open problems in deploying LLMs responsibly. Yet, unlike traditional cybersecurity domains such as network intrusion detection or malware analysis, tooling for LLM-specific threat detection remains immature, fragmented across research prototypes, and largely inaccessible to small teams without dedicated AI security expertise.

Existing commercial guardrail offerings are typically closed-source, tied to a single cloud vendor, or narrowly scoped to a single attack category such as toxic content moderation rather than the broader spectrum of jailbreaks, prompt injections, and adversarially optimised inputs. Open-source efforts, in turn, tend to implement a single detection technique in isolation and are rarely benchmarked against adaptive evasion attacks. This creates a clear opportunity for a detection tool that is model-agnostic, transparent in its detection logic, and specifically designed to combine multiple complementary techniques so that the weaknesses of one detector (for instance, perplexity filtering's blindness to fluent, semantically disguised attacks) are compensated for by another (such as an embedding-based classifier or an LLM-based judge). Building this tool also allows us to engage directly with an actively evolving research area, working with real adversarial benchmarks and attack reproductions rather than static, historical data, and to produce a system whose core detection techniques generalise well beyond any single LLM vendor or version.

## 6. Objective and Scope of the project

As organisations of every size race to embed LLMs into their products, the gap between the pace of adoption and the maturity of corresponding security tooling continues to widen. Startups and small engineering teams, in particular, often lack the dedicated AI red-teaming or security resources needed to continuously test their LLM-integrated applications against novel jailbreak and prompt injection techniques, leaving them exposed to reputational, financial, and data-privacy risks. Larger enterprises deploying LLMs in regulated or safety-critical contexts face an additional burden of demonstrating due diligence around model robustness as part of emerging AI governance requirements.

The primary objective of this project is to develop a Python-based application that can analyze user prompts and identify potential adversarial inputs targeting Large Language Models (LLMs). The application will evaluate prompts before they are processed by an LLM and, where required, examine generated responses for possible security risks. The system will implement three complementary detection approaches:

1. **Statistical analysis** using windowed perplexity and token-distribution anomaly scoring to catch gradient-optimised, low-fluency suffixes such as those produced by GCG-style attacks.
2. **Embedding-based semantic classifier**, fine-tuned on curated benign and adversarial prompt corpora, to catch fluent, semantically disguised jailbreaks and injection attempts that evade perplexity filtering.
3. **Optional LLM-as-a-judge verification stage**, invoked only for inputs whose scores fall in the ambiguous band between the configured thresholds, providing an interpretable, natural-language rationale for flagged content while keeping the latency and cost of the common path low.

The individual signals are combined through a calibrated scoring layer with configurable thresholds, allowing deployers to tune the trade-off between detection rate and false positives for their own traffic. Detected threats are logged and surfaced through a dashboard so that developers can audit attack patterns over time and continuously refine detection thresholds.

### 6.1. Evaluation Metrics

The effectiveness of the proposed adversarial attack detection framework will be evaluated using standard machine learning and cybersecurity performance metrics. Detection performance will be measured in terms of **accuracy, precision, recall, and F1-score** to assess the system's overall classification capability and its ability to correctly identify adversarial prompts while minimising false alarms. The **False Positive Rate (FPR)** and **False Negative Rate (FNR)** will also be analysed, as excessive false positives can unnecessarily block legitimate user requests, whereas false negatives may allow malicious prompts to reach the underlying LLM. Additionally, the **Receiver Operating Characteristic (ROC)** curve and the corresponding **Area Under the Curve (ROC-AUC)** will be used to evaluate the detector's performance across different decision thresholds.

Beyond classification accuracy, the proposed system will also be assessed on operational performance metrics relevant to real-world deployment. These include **detection latency**, which measures the additional processing time introduced by the detection layer, and **throughput**, measured as the number of prompts processed per second. The system will be benchmarked using publicly available adversarial datasets and benign prompt collections to evaluate its robustness against optimisation-based jailbreaks, prompt injection attacks, role-play jailbreaks, paraphrasing, and character-level obfuscation techniques. The results will be compared with existing baseline approaches to demonstrate the effectiveness, efficiency, and practical applicability of the proposed multi-layered detection framework.

**Scope.** The scope of the project targets three primary attack categories:

- (a) **Optimisation-based jailbreaks**, including gradient-based adversarial suffixes and their more fluent variants;
- (b) **Prompt injection attacks**, both direct (embedded in the user's own prompt) and indirect (embedded in third-party data such as documents, web pages, or tool outputs consumed by the model);
- (c) **Role-play and persona-based social-engineering jailbreaks** that attempt to bypass alignment through fictional framing.

The tool is designed to be evaluated against open adversarial benchmarks and prompt collections such as AdvBench, publicly released in-the-wild jailbreak prompt datasets, and open prompt-injection corpora, alongside benign instruction datasets used to measure false-positive and over-defence rates.

**Out of scope for this phase:** multi-turn conversational attacks, multimodal (image- or audio-borne) injections, non-English prompts, and training-time attacks such as data poisoning or model backdoors. The tool remains model-agnostic by operating purely on text inputs and outputs rather than requiring white-box access to model weights, making it deployable alongside both open-source models and closed, API-only commercial LLMs.

## 7. Hardware and Software Requirements

### 7.1. Hardware (Minimum Requirements)

- Quad-core Intel Core i5 or AMD Ryzen 5 (or equivalent)
- 16 GB RAM (recommended for local embedding/classifier inference)
- 100 GB free disk space
- Debian-based OS (e.g. Ubuntu) or Windows with WSL2
- Stable Internet Connection, 10 Mbps (for LLM API access)

### 7.2. Software

#### 7.2.1. Frontend

- HTML5, CSS3
- React.js for the framework, with Tailwind CSS and Material UI for the dashboard
- Recharts / D3.js for attack analytics visualisation

#### 7.2.2. Backend

- Python (FastAPI) for the detection engine and model-serving layer
- Node.js and Express for the application/API gateway layer
- PostgreSQL / MongoDB for logging detected prompts, scores, and audit trails
- Hugging Face Transformers and PyTorch for embedding models and classifier fine-tuning
- Redis for low-latency caching of detection scores
- Docker and Docker Compose for containerised deployment

#### 7.2.3. Additional

- Visual Studio Code / PyCharm for IDE
- Git and GitHub for version control
- AWS / GCP for cloud deployment and GPU inference
- Weights & Biases (or MLflow) for experiment tracking during classifier training

## 8. Final Deliverables

- A curated **benchmark dataset** of benign, jailbreak, and prompt-injection prompts assembled from open adversarial corpora and reproduced attack generations (e.g., GCG-style suffixes), supplemented with benign instruction data for false-positive measurement, and used for training and evaluating the detection models.
- A **detection engine** that scores incoming prompts (and optionally model outputs) using a combination of perplexity-based, embedding-based, and LLM-judge-based signals, exposed as a lightweight, model-agnostic API.
- A **web-based dashboard** allowing developers to monitor flagged prompts, inspect detection rationale, review false-positive/false-negative trends, and configure detection sensitivity.
- A **server-side application** acting as a middleware/proxy layer between an LLM-integrated application and the underlying LLM provider, routing traffic through the detection engine.
- A detailed **evaluation report** benchmarking the tool's detection accuracy, false-positive rate, and latency overhead against known jailbreak and prompt-injection attack suites, along with an analysis of its robustness to evasion attempts (including character-level obfuscation and paraphrasing attacks directed at the detector itself).

## 9. References

[1] A. Zou, Z. Wang, N. Carlini, M. Nasr, J. Z. Kolter, and M. Fredrikson, "Universal and Transferable Adversarial Attacks on Aligned Language Models," arXiv preprint arXiv:2307.15043, 2023.

[2] F. Perez and I. Ribeiro, "Ignore Previous Prompt: Attack Techniques For Language Models," arXiv preprint arXiv:2211.09527, 2022.

[3] X. Liu, N. Xu, M. Chen, and C. Xiao, "AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models," arXiv preprint arXiv:2310.04451, 2023.

[4] J. Su, "Enhancing Adversarial Attacks through Chain of Thought," arXiv preprint arXiv:2410.21791, 2024.

[5] H. Inan et al., "Llama Guard: LLM-based Input-Output Safeguard for Human-AI Conversations," arXiv preprint arXiv:2312.06674, 2023.

[6] Y. Liu, Y. Jia, R. Geng, J. Jia, and N. Z. Gong, "Formalizing and Benchmarking Prompt Injection Attacks and Defenses," arXiv preprint arXiv:2310.12815, 2023.

[7] J. Yi, Y. Xie, B. Zhu, E. Kiciman, G. Sun, X. Xie, and F. Wu, "Benchmarking and Defending Against Indirect Prompt Injection Attacks on Large Language Models," arXiv preprint arXiv:2312.14197, 2023.

[8] G. Alon and M. Kamfonas, "Detecting Language Model Attacks with Perplexity," arXiv preprint arXiv:2308.14132, 2023.

[9] N. Jain et al., "Baseline Defenses for Adversarial Attacks Against Aligned Language Models," arXiv preprint arXiv:2309.00614, 2023.

[10] G. Zizzo et al., "Adversarial Prompt Evaluation: Systematic Benchmarking of Guardrails Against Prompt Input Attacks on LLMs," arXiv preprint arXiv:2502.15427, 2025.

[11] H. Li and X. Liu, "InjecGuard: Benchmarking and Mitigating Over-defense in Prompt Injection Guardrail Models," arXiv preprint arXiv:2410.22770, 2024.

[12] Y. Xie, M. Fang, R. Pi, and N. Gong, "GradSafe: Detecting Jailbreak Prompts for LLMs via Safety-Critical Gradient Analysis," arXiv preprint arXiv:2402.13494, 2024.

[13] W. Hackett, L. Birch, S. Trawicki, N. Suri, and P. Garraghan, "Bypassing LLM Guardrails: An Empirical Analysis of Evasion Attacks against Prompt Injection and Jailbreak Detection Systems," arXiv preprint arXiv:2504.11168, 2025.

---

*Mentor Signature: Dr. Ruchi Sharma, dated 14/3/26 (academic year 2026-2027)*
