def senior_dev_parser_instructions():
    return [
        'Extract structured data from the Senior Dev Agent conversation.',
        'Do not call tools in this parser step.',
        'Use claims for user-stated implementation claims.',
        'Use findings for verified or likely technical issues.',
        'Every finding should include type, title, category, severity, confidence_score, confidence_reason, and evidence when available.',
        'Do not create, recommend, or assign tasks. The PM agent derives tasks from findings later.',
    ]
