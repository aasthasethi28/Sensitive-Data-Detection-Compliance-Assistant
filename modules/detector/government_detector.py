import re


class GovernmentDetector:

    @staticmethod
    def detect_pan(text):

        pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }

    @staticmethod
    def detect_aadhaar(text):

        pattern = r"\b\d{4}\s?\d{4}\s?\d{4}\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }