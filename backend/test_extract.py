from app.tools.extract_interaction import extract_interaction

result = extract_interaction(
    """
    I met Dr Rajesh Sharma yesterday
    for around 30 minutes.

    We discussed Ozempic.

    The doctor was interested.
    """
)

print(result)