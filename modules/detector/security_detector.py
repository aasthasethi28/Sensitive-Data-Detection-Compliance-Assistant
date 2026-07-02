import re


class SecurityDetector:

    @staticmethod
    def detect_password(text):

        pattern = r"(?i)(password|passwd|pwd)\s*[:=]\s*(\S+)"

        matches = re.findall(pattern, text)

        values = [m[1] for m in matches]

        return {

            "count": len(values),

            "values": values

        }

    @staticmethod
    def detect_employee_id(text):

        pattern = r"\bEMP[-_]?\d+\b"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }

    @staticmethod
    def detect_api_keys(text):

        pattern = r"(AIza[0-9A-Za-z-_]{20,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})"

        values = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(values),

            "values": values

        }