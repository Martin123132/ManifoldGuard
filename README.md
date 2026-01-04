# MBT-5 Semantic Regulator

## Geometry-Only Control of LLM Output at Inference Time

This repository implements **MBT-5**, a lightweight inference-time regulator that constrains LLM outputs using **embedding-space geometry**, not training, fine-tuning, or reward models.

The system treats semantic drift as **geometric curvature**, detects violations as **energy spikes**, and enforces correction through a **surgical feedback loop**.

No gradients.  
No retraining.  
No classifiers.

---

## Core Idea

1. Text → embedding space  
2. Define a **target manifold** from exemplar statements  
3. Compute a **robust geometric center** (Weiszfeld median)  
4. Measure deviation as:

\[
\text{Shock} = \Gamma \|\mathbf{x} - \mathbf{x}_{\text{manifold}}\|^2
\]

5. If shock exceeds threshold → force rewrite  
6. Repeat until stable or budget exhausted  

This is **semantic confinement**, not fact-checking.

---

## What This Is (and Isn’t)

### ✔️ Is
- Inference-time regulator
- Geometry-based
- Model-agnostic
- Works with OpenAI / Anthropic / local LLMs
- Detects and localises hallucinations
- Enforces topical fidelity

### ❌ Is Not
- Training
- Fine-tuning
- RAG
- Safety alignment
- Truth oracle

---

## Components

### Geometric Median
Robust against outliers and adversarial drift.

### Curvature Shock
Squared distance acts as an energy penalty for semantic escape.

### Leave-One-Out Token Analysis
Identifies *which word* causes instability.

### Surgical Rewrite Loop
Hard constraint enforcement — no polite nudging.

---

## Demos

| Demo | Description |
|----|----|
| `time_series_mbt5.py` | MBT-5 as geometric shock absorber |
| `embedding_outliers.py` | Hallucination detection via curvature |
| `token_self_repair.py` | Token-level fault isolation |
| `council_consensus.py` | Multi-agent semantic consensus |
| `ui/mbt5_pilot.ipynb` | Interactive “LOCK REALITY” pilot |

---

## Why This Works

LLMs do not reason symbolically — they move through **embedding space**.

MBT-5 does not tell the model *what* to say.  
It tells the model *where it is allowed to exist*.

---

## Status

Experimental but functional.  
Geometry-first by design.  
No claims beyond demonstrated behaviour.
