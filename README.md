# MBT-5 Semantic Regulator  
### Geometry-Based Confidence & Hallucination Detection for LLMs (Inference-Time)

**MBT-5** is a geometry-only, inference-time regulator for large language models that estimates **output confidence and hallucination risk without training, fine-tuning, classifiers, or content inspection**.

It works by measuring **semantic stability** and **geometric drift** in embedding space.

No gradients.  
No retraining.  
No moderation rules.  
No keyword filters.

---

## Why This Exists

LLMs do not “know” when they are wrong.  
They produce fluent text even when internal consistency collapses.

Current approaches try to fix this by:
- Aligning behavior during training  
- Blocking topics  
- Inspecting content  
- Forcing refusals  

These methods are brittle, invasive, and increasingly counter-productive.

**MBT-5 takes a different approach**:

> Instead of asking *“Is this answer allowed?”*  
> MBT-5 asks *“Is this answer geometrically stable?”*

---

## Core Insight

LLMs move through **semantic space**, not logic trees.

When an answer is:
- factual → embeddings cluster tightly  
- uncertain → embeddings spread  
- hallucinated → embeddings fracture  

MBT-5 measures this **fracture** directly.

---

## System Overview

MBT-5 consists of **three composable layers**, all inference-time:

### 1. Geometric Stability (Zero-Box Mode)
**No manifold. No setup. Just ask questions.**

- Generate multiple answer variants  
- Embed them  
- Measure internal disagreement (“entropy”)  
- Return a confidence score alongside the response  

This is the **Zero-Box Stability Pilot** — the MVP most people will use.

**Result:**  
> “Here is the answer — and here is how confident the model is.”

---

### 2. Manifold Confinement (Optional)
For domain-specific control:

- Define a semantic manifold (e.g. law, physics, medicine)  
- Compute a robust geometric center (Weiszfeld median)  
- Penalize radial escape from that manifold  
- Force rewrite if deviation exceeds threshold  

This is **semantic confinement**, not fact-checking.

---

### 3. Token-Level Fault Localization
When instability is detected:

- Perform leave-one-out token analysis  
- Identify which word causes geometric shock  
- Optionally trigger self-repair or re-prompting  

This allows **local explanation without inspecting meaning**.

---

## What MBT-5 Is (and Isn’t)

### ✔️ Is
- Inference-time  
- Geometry-based  
- Model-agnostic (OpenAI, Anthropic, local LLMs)  
- Privacy-preserving  
- External confidence signal  
- Hallucination *risk* detector  
- Domain-aware (if desired)  

### ❌ Is Not
- Training  
- Fine-tuning  
- RAG  
- Safety alignment  
- Keyword filtering  
- A “truth oracle”  

MBT-5 does **not** decide truth.  
It estimates **epistemic stability**.

---

## Key Mechanisms (Mapped to Code)

### Geometric Median (Weiszfeld)
Robust semantic center resistant to outliers.

Used in:
- Embedding consensus  
- Leave-one-out tests  
- Stability baselines  

---

### Curvature / Shock
Semantic deviation measured as energy:

\[
\text{Shock} = \Gamma \lVert \mathbf{x} - \mathbf{x}_{center} \rVert^2
\]

High shock ⇒ semantic escape.

---

### Internal Entropy (Zero-Box)
Measures **self-disagreement** across multiple model answers.

Low entropy ⇒ high confidence  
High entropy ⇒ hallucination risk

---

### Token-Level Shock Mapping
Removes words one-by-one to identify instability sources.

Used for:
- Debugging  
- Visualization  
- Self-repair experiments  

---

## Demos Included

| Demo | Description |
|----|----|
| `time_series_mbt5.py` | MBT-5 as geometric shock absorber |
| `embedding_outliers.py` | Hallucination detection via curvature |
| `token_self_repair.py` | Token-level fault isolation |
| `council_consensus.py` | Multi-agent semantic consensus |
| `mts_leave_one_out.py` | Robust hallucination detection |
| `ui/zero_box_pilot.ipynb` | **Zero-Box Stability UI (MVP)** |
| `ui/mbt5_pilot.ipynb` | Manifold-constrained pilot |

---

## The Zero-Box Stability Pilot (MVP)

The Zero-Box Pilot is the **recommended entry point**.

**User flow:**
1. Paste API key  
2. Ask a question normally  
3. Receive:  
   - Answer  
   - Confidence label  
   - Internal entropy score  

No configuration.  
No manifolds.  
No expertise required.

Suitable for:
- Red-team evaluation  
- Internal tooling  
- Product demos  
- Risk assessment layers  

---

## Why This Matters (Product View)

MBT-5 enables a **new safety primitive**:

> *Warn users when the model is unstable instead of pretending certainty.*

Analogous to:
- Credit risk scores  
- Weather confidence bands  
- Vehicle stability control  

This avoids:
- Over-moderation  
- User frustration  
- Privacy invasion  
- Alignment failure cascades  

---

## Status

- Experimental  
- Functional  
- Geometry-first  
- Demonstrated in notebooks  
- Designed for external integration  

No claims beyond observed behavior.

---

## One-Sentence Summary

> **MBT-5 adds an external, privacy-preserving confidence signal to LLM outputs using semantic geometry — entirely at inference time.**
