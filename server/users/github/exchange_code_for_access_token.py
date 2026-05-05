from users.github.exchange_code_for_token_data import exchange_code_for_token_data


def exchange_code_for_access_token(*, code):
    return exchange_code_for_token_data(code=code)['access_token']
