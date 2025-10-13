import json
import re
from typing import Dict, List

REQUIRED_FIELDS = ['answer', 'explanation', 'confidence']


def check_answer_format(answer: Dict[str, any]):
    missing = [field for field in REQUIRED_FIELDS if field not in answer]
    if len(missing) > 0:
        raise KeyError(f"answer missing required fields {missing}")
    if re.match(r".*? by .*", answer['answer']):
        return None
    elif re.match(r".*? \(\d{4}.*?\)", answer['answer']):
        return None
    else:
        raise ValueError(f"Invalid format of LLM response field 'answer': '{answer['answer']}'")


def check_generated_answers_format(generated_answers: List[Dict[str, any]]):
    for answer in generated_answers:
        check_answer_format(answer)


def answer_is_correct(answer: Dict[str, any], correct_answer: str, domain: str):
    answer_string = None
    if domain == 'books':
        if m := re.match(r"(.*) by .*", answer['answer']):
            answer_string = m.group(1)
    else:
        if m := re.match(r"(.*) \(\d{4}.*?\)", answer['answer']):
            answer_string = m.group(1)
    return answer_string == correct_answer


def generate_json_answers(choice) -> List[Dict[str, any]]:
    response = choice.message  # Extract the full response message that OpenAI returned
    generated_answer = response.content  # Extract the actual JSON-formatted answer.

    # Remove the enclosing ```json and ``` lines.
    generated_answer = generated_answer.replace("```json", "")
    generated_answer = generated_answer.replace("```", "")
    # try to load response as JSON
    try:
        generated_answer = json.loads(generated_answer)
    except json.JSONDecodeError:
        print("response is invalid JSON.")
        raise
    generated_answers = [generated_answer] if isinstance(generated_answer, dict) else generated_answer
    check_generated_answers_format(generated_answers)
    return generated_answers

