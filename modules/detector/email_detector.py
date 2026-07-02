import re


class EmailDetector:

    @staticmethod
    def detect(text):

        pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

        emails = sorted(list(set(re.findall(pattern, text))))

        return {

            "count": len(emails),

            "values": emails

        }