"""Embedding model abstraction — the only place a model name is hardcoded.

Swapping the underlying model means changing `_MODEL_NAME` (or passing a
different provider into `get_default_provider`), never touching ledger.py,
vector_store.py, or service.py. All three only know "a provider embeds text
into a list of floats of a known length."
"""

from abc import ABC, abstractmethod
from pathlib import Path


class EmbeddingProvider(ABC):
    """Anything that turns text into fixed-length vectors, locally."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier stored alongside each memory (e.g. 'fastembed:BAAI/bge-small-en-v1.5').

        Recorded per-row so that if the model is ever swapped, old rows are
        distinguishable from new ones and rebuild_index() knows every row it
        re-embeds will get the *current* provider's vector.
        """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector length this provider produces. Fixed for the provider's lifetime."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Provider/weights revision, stored per-row alongside name and dimension.

        Bumped when the *same* model name is re-trained or its preprocessing
        changes in a way that shifts the vector space — so rebuild_index() can
        tell a stale row apart from a current one even when the name is identical.
        """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings. Order-preserving, one vector per input string."""


_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_MODEL_VERSION = "1"
_DIMENSIONS = 384
_CACHE_DIR = Path.home() / ".cache" / "rai" / "fastembed"


class LocalEmbeddingProvider(EmbeddingProvider):
    """CPU-only, ONNX-backed embedding model — no torch, no network calls after first download.

    The model loads lazily on first `embed()` call (not at construction) so
    importing memory/ never pays ONNX-session startup cost for processes that
    never call remember()/recall() (e.g. dashboard.py's read-only views).
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None

    @property
    def name(self) -> str:
        return f"fastembed:{self._model_name}"

    @property
    def dimensions(self) -> int:
        return _DIMENSIONS

    @property
    def version(self) -> str:
        return _MODEL_VERSION

    def _ensure_loaded(self):
        if self._model is None:
            from fastembed import TextEmbedding

            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self._model = TextEmbedding(model_name=self._model_name, cache_dir=str(_CACHE_DIR))
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._ensure_loaded()
        return [vec.tolist() for vec in model.embed(texts)]


_default_provider: EmbeddingProvider | None = None


def get_default_provider() -> EmbeddingProvider:
    """Process-wide singleton so the ONNX model loads at most once per process."""
    global _default_provider
    if _default_provider is None:
        _default_provider = LocalEmbeddingProvider()
    return _default_provider
