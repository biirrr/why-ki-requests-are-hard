import json
import os
from time import localtime, strftime, sleep
from typing import Dict, List

import pandas as pd
from openai import OpenAI

from process_answer import answer_is_correct
from process_answer import generate_json_answers


def create_request(all_posts, thread_id: int):
    # Extract the raw post text.
    post_title = all_posts.loc[all_posts['thread_id'] == thread_id, 'title'].item()
    post_text = all_posts.loc[all_posts['thread_id'] == thread_id, 'text'].item()
    return f"{post_title}. {post_text}"


def get_domain_info(first_posts_file: str, model: str):
    """"Extract domain info from the first posts filename and the model."""
    # Extract the metadata from the filename.
    _, data_type, domain, source, extension = first_posts_file.split(".")
    metadata_string = f"{model}.{domain}.{data_type}.{source}"
    return domain, domain, metadata_string


def generate_completion(model: str, prompt_repeats: int, prompt_text: str):
    client = OpenAI()
    return client.chat.completions.create(
        model=f"{model}",
        n=prompt_repeats,
        # api_key=api_key,
        messages=[{"role": "user", "content": prompt_text}]
    )


def write_prompt_response(output_file, generated_answer: List[Dict[str, any]]):
    # Save to file.
    with open(output_file, "w") as fh:
        generated_answer = json.dumps(generated_answer)
        fh.write(generated_answer)


def run_prompt_repeats(model, thread_id, prompt_text: str, prompt_repeats: int,
                       results_dir_path, silent: bool = False):
    completion = generate_completion(model, prompt_repeats, prompt_text)
    # Process the response(s) and save to file(s).
    no_of_responses = len(completion.choices)
    now = strftime("%Y-%m-%d %H:%M:%S", localtime())  # Outside the IF-statement, cause we log this separately.
    if silent is False:
        print(f"{now}\t  * Saving {no_of_responses} response(s) to file")
    for k in range(0, no_of_responses):
        output_file = os.path.join(results_dir_path, f"{thread_id}.{model}.v{k + 1}.json")
        if silent is False:
            print(f"{now}\t    - {thread_id}.{model}.v{k + 1}.json")
        choice = completion.choices[k]  # Get the current response of K total responses
        generated_answers = generate_json_answers(choice)
        write_prompt_response(output_file, generated_answers)


def run_prompt_turn_based(model, thread_id, correct_answer: str, domain: str,
                          prompt_text: str, prompt_repeats: int,
                          max_tries: int, results_dir_path, silent: bool = False):
    completion = generate_completion(model, 1, prompt_text)
    # Process the response(s) and save to file(s).
    no_of_responses = len(completion.choices)
    now = strftime("%Y-%m-%d %H:%M:%S", localtime())  # Outside the IF-statement, cause we log this separately.
    if silent is False:
        print(f"{now}\t  * Saving {no_of_responses} response(s) to file")
    generated_answers = []
    for k in range(prompt_repeats):
        output_file = os.path.join(results_dir_path, f"{thread_id}.{model}.v{k + 1}.json")
        if silent is False:
            print(f"{now}\t    - {thread_id}.{model}.v{k + 1}.json")
        choice = completion.choices[k]  # Get the current response of K total responses
        generated_answer = generate_json_answers(choice)
        generated_answers.extend(generated_answer)
        if answer_is_correct(generated_answer[0], correct_answer, domain):
            break
        else:
            prompt_text =
            completion = generate_completion(model, 1, prompt_text)
    write_prompt_response(output_file, generated_answers)


def prep_output_files(metadata_string: str, silent: bool = False):
    """Prepare output directory, output file and logging file"""
    # Where are we going to save the API responses?
    # Make sure this results directory exists before saving to it.
    results_dir_path = os.path.join(os.getcwd(), metadata_string)
    if not os.path.exists(results_dir_path):
        if silent is False:
            now = strftime("%Y-%m-%d %H:%M:%S", localtime())
            print(f"{now}\t{results_dir_path} does not exist!")
        os.makedirs(results_dir_path)

    # Also create an empty version of the timestamp log file, if it does not exist yet.
    timestamp_log_path = os.path.join(os.getcwd(), "timestamp-log.tsv")
    if not os.path.exists(timestamp_log_path):
        timestamp_header = f"domain\tthread_id\tmodel\ttimestamp_processed\n"
        with open(timestamp_log_path, 'a') as f:
            f.write(timestamp_header)
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"Creating timestamp log file {timestamp_log_path} at {now}")

    # Print out the selected model.
    if silent is False:
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"{now}\tRunning against OpenAI API ({metadata_string})")
    return results_dir_path, timestamp_log_path


def process_first_posts_with_turn_based_prompt(first_posts_file: str, model: str,
                                               correct_answers: Dict[str, any], max_tries: int = 20,
                                               silent: bool = False):
    """Run requests against OpenAI API with specified model and ask for a single suggestion
    until the correct answer is given or the maximum number of retries is reached.

    :param first_posts_file:
    :param model:
    :param correct_answers: dictionary with correct answer per thread ID.
    :param max_tries:
    :param silent:
    :return:
    """
    # Keep stats on current call of this method.
    n_requests_processed_all = 0
    n_requests_processed_new = 0
    n_json_files_created = 0

    domain, domain_singular, metadata_string = get_domain_info(first_posts_file, model)
    results_dir_path, timestamp_log_path = prep_output_files(metadata_string, silent=silent)

    # Read in all first posts from file into a Pandas dataframe. Then extract a list of all thread IDs to crawl.
    all_posts = pd.read_table(first_posts_file, header=0)
    thread_id_list = all_posts['thread_id'].tolist()

    # For each post, transform the request into a prompt and run it.
    # for thread_id in thread_id_list[0:5]:
    for thread_id in thread_id_list:

        request = create_request(all_posts, thread_id)
        prompt_text = create_prompt(domain_singular, request, prompt_type='single_guess')

        # Save the prompt to file (so we can easily run it manually if we wish).
        prompt_file = os.path.join(results_dir_path, f"prompt.{thread_id}.txt")
        f = open(prompt_file, "w")
        f.write(prompt_text)
        f.close()

        # Update the stats.
        n_requests_processed_all += 1

        # Have we already processed this one? If not, skip to the next one (just check the v1 of this).
        # Defining this v1 is just to check whether they've been generated already.
        # prompt_repeats is used later on to create separate JSON files.
        output_file = os.path.join(results_dir_path,
                                   f"{thread_id}.{model}.v1.json")
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        if os.path.exists(output_file):
            if silent is False:
                print(f"{now}\tAlready processed {domain} thread '{thread_id}'")
            continue

        # Run the prompt against OpenAI's API.
        sleep(1)
        if silent is False:
            print(f"{now}\tProcessing of {domain} thread '{thread_id}'")

        run_prompt_repeats(model, thread_id, prompt_text, prompt_repeats,
                           results_dir_path, silent=False)
        # Update the stats.
        n_requests_processed_new += 1
        n_json_files_created += prompt_repeats

        # Record the current timestamp for this response in a separate file.
        timestamp_entry = f"{domain}\t{thread_id}\t{model}\t{now}\n"
        with open(timestamp_log_path, 'a') as f:
            f.write(timestamp_entry)

    if silent is False:
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"{now}\tDone with current crawl call")
        print(f"{now}\t  * Total requests processed: {n_requests_processed_all}")
        print(f"{now}\t  * New requests processed: {n_requests_processed_new}")
        print(f"{now}\t  * New JSON files created: {n_json_files_created}")


def process_first_posts_with_prompt_repeats(first_posts_file: str, model: str, top_n: int = 20,
                                            prompt_repeats: int = 1, silent: bool = False):
    """Take all the first posts, convert them into the right prompts
    and run them against the OpenAI API using the specified model. Threads already processed
    will be skipped. By default, progress is printed, but this can be disabled
    by setting the 'silent' parameter to 'True'.

    :param first_posts_file:
    :param model:
    :param top_n:
    :param prompt_repeats:
    :param silent:
    :return:
    """
    # Keep stats on current call of this method.
    n_requests_processed_all = 0
    n_requests_processed_new = 0
    n_json_files_created = 0

    domain, domain_singular, metadata_string = get_domain_info(first_posts_file, model)
    results_dir_path, timestamp_log_path = prep_output_files(metadata_string, silent=silent)

    # Read in all first posts from file into a Pandas dataframe. Then extract a list of all thread IDs to crawl.
    all_posts = pd.read_table(first_posts_file, header=0)
    thread_id_list = all_posts['thread_id'].tolist()

    # For each post, transform the request into a prompt and run it.
    # for thread_id in thread_id_list[0:5]:
    for thread_id in thread_id_list:

        request = create_request(all_posts, thread_id)
        prompt_text = create_prompt(domain_singular, request, prompt_type='top_n', top_n=top_n)

        # Save the prompt to file (so we can easily run it manually if we wish).
        prompt_file = os.path.join(results_dir_path, f"prompt.{thread_id}.txt")
        f = open(prompt_file, "w")
        f.write(prompt_text)
        f.close()

        # Update the stats.
        n_requests_processed_all += 1

        # Have we already processed this one? If not, skip to the next one (just check the v1 of this).
        # Defining this v1 is just to check whether they've been generated already.
        # prompt_repeats is used later on to create separate JSON files.
        output_file = os.path.join(results_dir_path,
                                   f"{thread_id}.{model}.v1.json")
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        if os.path.exists(output_file):
            if silent is False:
                print(f"{now}\tAlready processed {domain} thread '{thread_id}'")
            continue
        else:

            # Run the prompt against OpenAI's API.
            sleep(1)
            if silent is False:
                print(f"{now}\tProcessing of {domain} thread '{thread_id}'")

            run_prompt_repeats(model, thread_id, prompt_text, prompt_repeats,
                               results_dir_path, silent=False)
            # Update the stats.
            n_requests_processed_new += 1
            n_json_files_created += prompt_repeats

            # Record the current timestamp for this response in a separate file.
            timestamp_entry = f"{domain}\t{thread_id}\t{model}\t{now}\n"
            with open(timestamp_log_path, 'a') as f:
                f.write(timestamp_entry)

    if silent is False:
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(f"{now}\tDone with current crawl call")
        print(f"{now}\t  * Total requests processed: {n_requests_processed_all}")
        print(f"{now}\t  * New requests processed: {n_requests_processed_new}")
        print(f"{now}\t  * New JSON files created: {n_json_files_created}")
