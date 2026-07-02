import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension):

        self.index = faiss.IndexFlatL2(dimension)

        self.documents = []

    def add(self, embeddings, chunks):

        self.index.add(
            np.array(
                embeddings,
                dtype="float32"
            )
        )

        self.documents.extend(chunks)

    def search(self, query_embedding, k=3):

        distances, indices = self.index.search(
            np.array(
                [query_embedding],
                dtype="float32"
            ),
            k
        )

        return [

            self.documents[i]

            for i in indices[0]

        ]