from textwrap import wrap


def create_prompt(domain: str, request: str, prompt_type: str, top_n: int = None):
    # Create the appropriate prompt.
    domain_singular = domain[:-1]
    prompt_start = (f"Identify the {domain_singular} the user is looking for as "
                    f"described in the request below:")
    prompt_middle = f"Request: \"{request}\""
    prompt_start = "\n".join(wrap(prompt_start))
    prompt_middle = "\n".join(wrap(prompt_middle))
    prompt_end = create_prompt_end(domain, prompt_type, top_n=top_n)
    prompt_end = "\n".join(wrap(prompt_end))
    if prompt_type == 'next_guess':
        return prompt_end
    return f"{prompt_start}\n\n{prompt_middle}\n\n{prompt_end}"


def create_prompt_end(domain: str, prompt_type: str, top_n: int = None):
    """Create a prompt for requesting a ranked list of top N results."""
    domain_singular = domain[:-1]
    field_elements = "title and author" if domain == "books" else "title and release year"
    if prompt_type == "top_n":
        if top_n is None:
            raise ValueError(f"No value passed for 'top_n'.")
        return (f"Please provide a ranked list of your {top_n} best guesses for "
                f"the correct answer. Please answer in a JSON object that contains "
                f"a ranked list of suggestions. Each suggestion should contain a field "
                f"called 'answer' containing the suggestion ({field_elements}), "
                f"a field 'explanation' containing an explanation of why these "
                f"{domain_singular}s could be the correct answer, and a 'confidence' "
                f"score that represents how confident you are of your suggestion.")
    elif prompt_type == "single_guess":
        return (f"Please provide your best guess for the correct answer. "
                f"Please answer in a JSON object that contains a field "
                f"called 'answer' containing the suggestion ({field_elements}), "
                f"a field 'explanation' containing an explanation of why this "
                f"{domain_singular} could be the correct answer, and a 'confidence' "
                f"score that represents how confident you are of your suggestion.")
    elif prompt_type == "next_guess":
        return (f"Your previous suggestion is not the {domain_singular} the user is "
                f"looking for. Please provide your next best guess,"
                f"and again answer in a JSON object that contains a field "
                f"called 'answer' containing the suggestion ({field_elements}), "
                f"a field 'explanation' containing an explanation of why this "
                f"{domain_singular} could be the correct answer, and a 'confidence' "
                f"score that represents how confident you are of your suggestion.")
    else:
        raise ValueError(f"invalid prompt_type '{prompt_type}', must be 'top_n' or 'single_guess'.")

