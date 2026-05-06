def senior_dev_parser_instructions():
    return [
        'Extract structured data from the Senior Dev Agent conversation.',
        'Do not call tools in this parser step.',
        'Return a single JSON object and nothing else.',
        'JSON keys must be: assistant_message, check_in_question, choices, allow_free_text, conversation_summary, claims, findings.',
        'Use claims for user-stated implementation claims.',
        'Use findings for verified or likely technical issues.',
        'Every finding should include type, title, category, severity, confidence_score, confidence_reason, and evidence when available.',
        "If the assistant states a confidence percentage (e.g., 'I'm 30% confident'), use that value for any finding missing confidence_score.",
        'If confidence_score is missing, choose a reasonable integer (e.g., 75 with code/file evidence, 50 otherwise) and explain the default in confidence_reason.',
        'Do not create, recommend, or assign tasks. The PM agent derives tasks from findings later.',
    ]
