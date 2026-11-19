class TenQFinancialSchema:
    """JSON schema for 10-Q quarterly report financial extraction."""

    SCHEMA = {
        "type": "object",
        "description": "Extract financial data from an SEC 10-Q quarterly report. "
        "Focus only on revenue, net income, and EPS for both the current three-month period "
        "and the prior year's corresponding three-month period. Null if not present.",
        "properties": {
            "meta": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "company_name": {"type": ["string", "null"]},
                    "ticker": {"type": ["string", "null"]},
                    "fiscal_year": {"type": ["integer", "null"]},
                    "fiscal_quarter": {"type": ["integer", "null"]},
                    "period_end_date": {"type": ["string", "null"]},
                    "reporting_currency": {"type": ["string", "null"]},
                    "unit": {"type": ["string", "null"], "enum": ["millions", "thousands", None]},
                },
                "required": [
                    "company_name",
                    "ticker",
                    "fiscal_year",
                    "fiscal_quarter",
                    "period_end_date",
                    "reporting_currency",
                    "unit",
                ],
            },
            "current_period": {
                "type": ["object", "null"],
                "description": "Financials for the most recent Three Months Ended period reported in the 10-Q.",
                "additionalProperties": False,
                "properties": {
                    "revenue": {
                        "type": ["number", "null"],
                        "description": "Top-line revenue, net sales, or total sales.",
                    },
                    "net_income": {"type": ["number", "null"], "description": "Bottom-line net income or loss."},
                    "eps_basic": {"type": ["number", "null"], "description": "Basic earnings per share."},
                    "eps_diluted": {"type": ["number", "null"], "description": "Diluted earnings per share."},
                },
                "required": ["revenue", "net_income", "eps_basic", "eps_diluted"],
            },
            "prior_year_period": {
                "type": ["object", "null"],
                "description": "Financials for the prior year's corresponding Three Months Ended period.",
                "additionalProperties": False,
                "properties": {
                    "revenue": {"type": ["number", "null"]},
                    "net_income": {"type": ["number", "null"]},
                    "eps_basic": {"type": ["number", "null"]},
                    "eps_diluted": {"type": ["number", "null"]},
                },
                "required": ["revenue", "net_income", "eps_basic", "eps_diluted"],
            },
        },
        "required": ["meta", "current_period", "prior_year_period"],
        "additionalProperties": False,
    }


class TenQPromptConfig:
    SYSTEM_PROMPT = (
        "You are a financial-data extraction engine. Your only job is to read a single SEC 10-Q quarterly "
        "report and return a valid JSON object that conforms exactly to the schema provided.\n"
        "You must never hallucinate, estimate, interpolate, or perform arithmetic on any value.\n"
        "Extract the revenue, net income, and EPS for the 'Three Months Ended' current period and "
        "the prior year comparison period from the Consolidated Statements of Operations/Income."
    )

    USER_PROMPT_TEMPLATE = """Extract financial data from the following SEC 10-Q quarterly report.

REPORT:
\"\"\"
{document_text}
\"\"\"

JSON output only:"""

    def __init__(self, document_text: str, use_json_schema: bool = True, temperature: float = 0.0):
        self.system_prompt = self.SYSTEM_PROMPT
        self.user_prompt = self.USER_PROMPT_TEMPLATE.format(document_text=document_text)
        self.with_json_schema = use_json_schema
        self.temperature = temperature
        self.schema = TenQFinancialSchema.SCHEMA
