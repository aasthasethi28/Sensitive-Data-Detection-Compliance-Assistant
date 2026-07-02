import re


class FinancialDetector:

    @staticmethod
    def detect_credit_card(text):

        pattern = r"\b(?:\d[ -]*?){13,16}\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }

    @staticmethod
    def detect_ifsc(text):

        pattern = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }

    @staticmethod
    def detect_bank_account(text):

        pattern = r"\b\d{9,18}\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }