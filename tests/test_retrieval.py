import numpy as np
import pytest

from energy_copilot.retrieval import Retriever, chunk_documents


# Synthetic vectors verify search mechanics, not semantic model quality.
class FakeEmbedder:
    def embed(self, texts):
        return [np.array([1.0, 0.0]) if "wind" in t else np.array([0.0, 1.0]) for t in texts]

    def query_embed(self, text):
        return self.embed([text])


def test_chunk_overlap_and_stable_ids():
    docs = [dict(id="x", title="x", url="https://example.org", text="a b c d e f g")]
    chunks = chunk_documents(docs, words=4, overlap=1)
    assert [c["text"] for c in chunks] == ["a b c d", "d e f g"]
    assert chunks == chunk_documents(docs, words=4, overlap=1)
    assert len(set(c["id"] for c in chunks)) == 2


def test_bad_chunk_config():
    with pytest.raises(ValueError):
        chunk_documents([], words=3, overlap=3)


def test_cosine_rank_sources_and_threshold():
    docs = [dict(id=t, title=t, url="https://example.org/" + t, text=t) for t in ["solar", "wind"]]
    r = Retriever(FakeEmbedder(), docs, threshold=0.9)
    result = r.search("wind")
    assert len(result) == 1 and result[0].title == "wind"
    assert result[0].url.endswith("/wind")
    r.threshold = 1.1
    assert r.search("wind") == []


@pytest.mark.integration
def test_real_local_embeddings():
    r = Retriever()
    assert r.vectors.shape[1] == 384
    assert any(s.id.startswith("neso-wind:") for s in r.search("What does embedded wind generation mean?"))
