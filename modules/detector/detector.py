from .email_detector import EmailDetector
from .phone_detector import PhoneDetector
from .government_detector import GovernmentDetector
from .financial_detector import FinancialDetector
from .security_detector import SecurityDetector
from .business_detector import BusinessDetector


class SensitiveDataDetector:

    @staticmethod
    def detect(text):

        return {

            "emails": EmailDetector.detect(text),

            "phones": PhoneDetector.detect(text),

            "pan": GovernmentDetector.detect_pan(text),

            "aadhaar": GovernmentDetector.detect_aadhaar(text),

            "credit_cards": FinancialDetector.detect_credit_card(text),

            "bank_accounts": FinancialDetector.detect_bank_account(text),

            "ifsc": FinancialDetector.detect_ifsc(text),

            "passwords": SecurityDetector.detect_password(text),

            "employee_ids": SecurityDetector.detect_employee_id(text),

            "api_keys": SecurityDetector.detect_api_keys(text),

            "business_information": BusinessDetector.detect(text)

        }