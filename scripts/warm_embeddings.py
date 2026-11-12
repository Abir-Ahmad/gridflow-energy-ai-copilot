from energy_copilot.retrieval import Retriever

r = Retriever()
print(f"Loaded {len(r.chunks)} chunks; embedding dimensions={r.vectors.shape[1]}")
print([s.id for s in r.search("What does embedded wind generation mean?")])
