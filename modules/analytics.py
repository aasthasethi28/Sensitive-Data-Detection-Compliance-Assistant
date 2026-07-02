"""
analytics.py

Enterprise Dashboard Analytics
"""

import pandas as pd
import plotly.express as px


class Analytics:

    @staticmethod
    def risk_distribution(stats):

        df = pd.DataFrame({
            "Risk": ["High", "Medium", "Low"],
            "Count": [
                stats.get("high_risk", 0),
                stats.get("medium_risk", 0),
                stats.get("low_risk", 0)
            ]
        })

        fig = px.pie(
            df,
            names="Risk",
            values="Count",
            title="Risk Distribution",
            hole=0.4
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20)
        )

        return fig

    @staticmethod
    def sensitive_data_distribution(stats):

        data = {
            "Emails": stats.get("emails", 0),
            "Phones": stats.get("phones", 0),
            "PAN": stats.get("pan", 0),
            "Aadhaar": stats.get("aadhaar", 0),
            "Credit Cards": stats.get("credit_cards", 0),
            "Bank Accounts": stats.get("bank_accounts", 0),
            "API Keys": stats.get("api_keys", 0),
            "Passwords": stats.get("passwords", 0),
            "Employee IDs": stats.get("employee_ids", 0),
        }

        df = pd.DataFrame(
            {
                "Sensitive Data": list(data.keys()),
                "Count": list(data.values())
            }
        )

        fig = px.bar(
            df,
            x="Sensitive Data",
            y="Count",
            title="Sensitive Data Distribution",
            text="Count"
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis_title="Sensitive Data Type",
            yaxis_title="Count"
        )

        return fig