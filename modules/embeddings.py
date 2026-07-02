from sentence_transformers import SentenceTransformer

# Singleton model
_model = None


class EmbeddingModel:

    @staticmethod
    def get_model():

        global _model

        if _model is None:

            print("Loading embedding model...")

            _model = SentenceTransformer(
                "BAAI/bge-small-en-v1.5"
            )

        return _model

    @staticmethod
    def encode(chunks):

        model = EmbeddingModel.get_model()

        return model.encode(
            chunks,
            convert_to_numpy=True,
            normalize_embeddings=True
        )