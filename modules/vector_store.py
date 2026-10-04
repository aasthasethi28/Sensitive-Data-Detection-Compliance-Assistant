"""
vector_store.py

FAISS Vector Store
"""

import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension):

        self.index = faiss.IndexFlatL2(
            dimension
        )

        self.documents = []


    def add(self, embeddings, chunks):

        embeddings = np.array(
            embeddings,
            dtype="float32"
        )

        self.index.add(
            embeddings
        )

        self.documents.extend(
            chunks
        )


    def search(self, query_embedding, k=6):

        # Prevent requesting more results
        # than the number of stored chunks

        if not self.documents:

            return []

        k = min(
            k,
            len(self.documents)
        )

        query_embedding = np.array(
            [query_embedding],
            dtype="float32"
        )

        distances, indices = self.index.search(
            query_embedding,
            k
        )

        results = []

        for distance, index in zip(
            distances[0],
            indices[0]
        ):

            if index < 0:
                continue

            results.append(

                {
                    "chunk": self.documents[index],

                    "distance": float(distance)

                }

            )

        return results