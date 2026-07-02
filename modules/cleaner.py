import re


class TextCleaner:

    @staticmethod
    def clean(text: str) -> str:
        """
        Clean extracted document text.
        """

        # Replace tabs with spaces
        text = text.replace("\t", " ")

        # Remove multiple spaces
        text = re.sub(r" +", " ", text)

        # Remove extra blank lines
        text = re.sub(r"\n+", "\n", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text