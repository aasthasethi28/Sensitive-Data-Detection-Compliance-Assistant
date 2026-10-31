
"""
compliance.py

Generates AI-powered compliance reports using
a locally running Ollama model.
"""

from modules.llm import LocalLLM


class ComplianceGenerator:

    """
    Generates professional compliance reports
    for uploaded documents using a local LLM.
    """

    # =====================================================
    # GENERATE COMPLIANCE REPORT
    # =====================================================

    @staticmethod
    def generate(
        document,
        detection,
        risk
    ):

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

Use the supplied risk classification as the authoritative risk level.
Do not independently invent or change the calculated risk score.

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

If no sensitive information was detected, explicitly state that.

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

Do not claim that a regulation applies merely because it appears in this list.

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

Distinguish actual detected risks from hypothetical risks.

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

Make recommendations relevant to the actual document findings.

---

# 🏁 Final Verdict

Give a final conclusion in 3–4 sentences explaining whether the document is safe to share publicly and what precautions should be taken.

Use professional markdown formatting with headings and bullet points.

STRICT RULES:

1. Base the report on the supplied document, detections and risk classification.
2. Do not invent sensitive information or detection results.
3. Do not change the supplied risk level.
4. Distinguish detected facts from general recommendations.
5. If information is unavailable, state that it was not established.
"""


        # =================================================
        # LOCAL LLM GENERATION
        # =================================================

        try:

            report = LocalLLM.generate(
                prompt,
                temperature=0.2,
                num_ctx=8192
            )

            return report


        except Exception as e:

            return f"""
# ❌ Compliance Report Generation Failed

Error:

{str(e)}

Please verify:

- Ollama is running.
- The configured local model is installed.
- The model name in the .env file is correct.
- The local Ollama API is accessible.
- Sufficient system memory is available.
"""


