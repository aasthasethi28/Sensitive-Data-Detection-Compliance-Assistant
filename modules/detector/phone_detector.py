import re


class PhoneDetector:

    @staticmethod
    def detect(text):

        pattern = r"\b[6-9]\d{9}\b"

        phones = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(phones),

            "values": phones

        }