class RiskClassifier:

    # Score assigned to each entity
    WEIGHTS = {

        "emails": 1,

        "phones": 1,

        "employee_ids": 2,

        "ifsc": 3,

        "pan": 4,

        "aadhaar": 5,

        "bank_accounts": 5,

        "credit_cards": 7,

        "passwords": 8,

        "api_keys": 10,

        "business_information": 8

    }

    @staticmethod
    def calculate_score(results):

        total_score = 0

        for entity, weight in RiskClassifier.WEIGHTS.items():

            count = results.get(entity, {}).get("count", 0)

            total_score += count * weight

        return total_score

    @staticmethod
    def classify(score):

        if score <= 5:

            return "LOW"

        elif score <= 15:

            return "MEDIUM"

        else:

            return "HIGH"

    @staticmethod
    def classify_document(results):

        score = RiskClassifier.calculate_score(results)

        risk = RiskClassifier.classify(score)

        return {

            "score": score,

            "risk_level": risk

        }