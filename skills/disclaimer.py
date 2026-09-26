"""
Disclaimer Skill for Samata Legal Assistant.
Provides standardized, legally responsible disclaimers for all agent outputs.
"""

STANDARD_DISCLAIMER = (
    "This information is provided for educational purposes only and does not constitute legal advice. "
    "Please review any documents or information with a qualified legal professional before taking any action."
)

DOCUMENT_DISCLAIMER = (
    "This is a template document generated for reference purposes only. It is not a legally binding instrument. "
    "Review this document with your lawyer or legal counsel before use or execution."
)

SENSITIVITY_DISCLAIMER = (
    "If you or someone you know is experiencing distress, please reach out to iCall (9152987821) or SNEHI (011-65978181) for support."
)

DISCLAIMER_VERSION = "1.0.0"


def get_disclaimer(output_type: str = "standard") -> str:
    """
    Returns the appropriate disclaimer string based on output_type.
    Types: 'standard', 'document', 'sensitivity', 'all'
    """
    if output_type == "document":
        return f"{STANDARD_DISCLAIMER}\n\n{DOCUMENT_DISCLAIMER}"
    elif output_type == "sensitivity":
        return f"{STANDARD_DISCLAIMER}\n\n{SENSITIVITY_DISCLAIMER}"
    elif output_type == "all":
        return f"{STANDARD_DISCLAIMER}\n\n{DOCUMENT_DISCLAIMER}\n\n{SENSITIVITY_DISCLAIMER}"
    return STANDARD_DISCLAIMER
