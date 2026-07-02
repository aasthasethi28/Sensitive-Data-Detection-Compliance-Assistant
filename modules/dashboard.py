class DashboardManager:

    @staticmethod
    def get_statistics(documents):

        stats = {

            "total_documents": len(documents),

            "high_risk": 0,

            "medium_risk": 0,

            "low_risk": 0,

            "emails": 0,

            "phones": 0,

            "pan": 0,

            "aadhaar": 0,

            "credit_cards": 0,

            "bank_accounts": 0,

            "api_keys": 0,

            "passwords": 0,

            "employee_ids": 0

        }

        for doc in documents:

            risk = doc["risk"]["risk_level"].upper()

            if risk == "HIGH":

                stats["high_risk"] += 1

            elif risk == "MEDIUM":

                stats["medium_risk"] += 1

            else:

                stats["low_risk"] += 1

            # Sensitive Data

            detections = doc["detections"]

            for key in [

                "emails",

                "phones",

                "pan",

                "aadhaar",

                "credit_cards",

                "bank_accounts",

                "api_keys",

                "passwords",

                "employee_ids"

            ]:

                if key in detections:

                    stats[key] += detections[key].get(
                        "count",
                        0
                    )

        return stats