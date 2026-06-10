from typing import List, Optional, Tuple

import numpy as np

from .embeddings import embed_texts
from .geometry import shock


def token_shock_map(
    text: str,
    *,
    max_samples: Optional[int] = None,
    top_k: Optional[int] = None,
    order: str = "token",
) -> List[Tuple[str, float]]:
    """
    Compute leave-one-out token shock scores.

    This mirrors the notebook logic of removing words individually, embedding
    the modified text, and measuring squared deviation from the original
    embedding.

    Parameters:
      max_samples: Optional token subset cap to reduce expensive recomputation.
      top_k: Optional count for returning highest-shock tokens by score.
      order: ``"token"`` for original token-order output, ``"score"`` for score order.

    No calibration semantics were changed, only batching/sampling and ordering
    controls.
    """

    if max_samples is not None and max_samples <= 0:
        max_samples = None
    if top_k is not None and top_k <= 0:
        return []
    if order not in {"token", "score"}:
        raise ValueError("order must be 'token' or 'score'")

    tokens = text.split()
    if not tokens:
        return []

    baseline_embedding = embed_texts([text])[0]
    indices = _select_token_indices(len(tokens), max_samples)

    if not indices:
        return []

    variants = [" ".join(tokens[:i] + tokens[i + 1 :]) for i in indices]
    embeddings = embed_texts(variants)

    scored = [
        (index, tokens[index], shock(embedding, baseline_embedding))
        for index, embedding in zip(indices, embeddings)
    ]

    if order == "score":
        ordered = sorted(scored, key=lambda item: item[2], reverse=True)
    else:
        ordered = sorted(scored, key=lambda item: item[0])

    if top_k is not None and top_k > 0:
        if order == "score":
            ordered = ordered[:top_k]
        else:
            top_indices = {
                index for index, _, _ in sorted(scored, key=lambda item: item[2], reverse=True)[:top_k]
            }
            ordered = [entry for entry in ordered if entry[0] in top_indices]

    return [(token, score) for _, token, score in ordered]


def _select_token_indices(length: int, max_samples: Optional[int]) -> List[int]:
    if max_samples is None or max_samples >= length:
        return list(range(length))

    if max_samples == 1:
        return [length // 2]

    return sorted({int(round(i * (length - 1) / (max_samples - 1))) for i in range(max_samples)})
