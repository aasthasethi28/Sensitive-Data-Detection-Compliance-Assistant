"""
Generates an AI Compliance Report using Google Gemini.
"""

import os
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


class ComplianceGenerator:

    """
    Generates a professional compliance report
    for uploaded documents.
    """

    model = genai.GenerativeModel(
        "gemini-2.5-flash"
    )

    @staticmethod
    def generate(document, detection, risk):

        prompt = f"""
You are an Enterprise Cybersecurity Compliance Officer and Data Privacy Auditor.

Your responsibility is to analyze the uploaded document and generate a detailed compliance report.

=========================================================
DOCUMENT
=========================================================

{document[:7000]}

=========================================================
DETECTED SENSITIVE INFORMATION
=========================================================

{detection}

=========================================================
RISK CLASSIFICATION
=========================================================

{risk}

=========================================================

Generate the report using the EXACT structure below.

# 📄 Document Summary

Provide a concise summary (4–6 lines) explaining:
- What the document is about
- The purpose of the document
- The type of information it contains

---

# 📋 Executive Summary

Provide an executive overview of the security posture.

Mention:
- Whether confidential data exists
- Whether Personally Identifiable Information (PII) exists
- Whether financial information exists
- Overall security concerns

---

# ⚠ Overall Risk Assessment

State the overall risk level:

• Low Risk
• Medium Risk
• High Risk

Explain WHY this risk level was assigned.

---

# 🔍 Sensitive Information Detected

Create a bullet list.

For every detected category explain why it is sensitive.

Examples:

• Email Addresses

• Phone Numbers

• Aadhaar Numbers

• PAN Numbers

• Credit Card Numbers

• Bank Account Numbers

• API Keys

• Passwords

• Employee IDs

• Business Confidential Information

---

# 📚 Applicable Compliance Standards

Mention applicable standards only if relevant.

Possible standards include:

• DPDP Act (India)

• GDPR

• ISO 27001

• PCI DSS

• HIPAA

Briefly explain why each applies.

---

# 🚨 Security Risks

Explain possible consequences if this document is exposed.

Examples:

• Identity Theft

• Financial Fraud

• Privacy Violation

• Insider Threat

• Credential Leakage

• Data Breach

• Regulatory Penalties

---

# ✅ Recommendations

Provide at least 6 professional recommendations.

Examples:

• Mask sensitive information.

• Encrypt documents before storage.

• Restrict access using Role-Based Access Control (RBAC).

• Enable Audit Logging.

• Remove hardcoded credentials.

• Rotate exposed API Keys.

• Apply Data Loss Prevention (DLP).

• Store documents securely.

• Apply document classification labels.

---

# 🏁 Final Verdict

Give a final conclusion in 3–4 sentences explaining whether the document is safe to share publicly and what precautions should be taken.

Use professional markdown formatting with headings and bullet points.
"""

        try:

            response = ComplianceGenerator.model.generate_content(
                prompt
            )

            return response.text

        except Exception as e:

            return f"""
# ❌ Compliance Report Generation Failed

Error:

{str(e)}

Please verify:

- Gemini API Key
- Internet Connection
- API Quota
"""