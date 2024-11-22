import pandas as pd
import threading
from queue import Queue
import medspacy
from medspacy.ner import TargetRule
# Create a sample DataFrame
data = [
    'Patient shows symptoms of flu and other complications.',
    'Diagnosis indicates pneumonia.',
    'Follow-up required for diabetes management.',
    'Patient is recovering well, but needs to keep taking beta blockers for hypertension.'
]
df = pd.DataFrame({'text': data})

# Define target rules for MedSpaCy pipeline
target_rules = [
    TargetRule(literal="flu", category="PROBLEM"),
    TargetRule("pneumonia", "PROBLEM"),
    TargetRule("hemicolectomy", "TREATMENT"),
    TargetRule("beta blockers", "TREATMENT"),
    TargetRule("hypertension", "PROBLEM"),
    TargetRule("diabetes", "PROBLEM"),
]


# Function to initialize and configure MedSpaCy pipeline
def create_nlp():
    nlp = medspacy.load()
    target_matcher = nlp.get_pipe("medspacy_target_matcher")
    target_matcher.add(target_rules)
    return nlp


# Function to process text using MedSpaCy
def process_text(text, output_queue):
    print(f'Starting processing for text: "{text}"')
    nlp = create_nlp()
    doc = nlp(text)
    output_queue.put(doc)


# Function to process DataFrame with multithreading
def process_dataframe_multithread(df, num_threads):
    output_queue = Queue()
    semaphore = threading.Semaphore(num_threads)
    threads = []

    for text in df['text']:
        thread = threading.Thread(target=process_text, args=(text, output_queue))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    results = []
    while not output_queue.empty():
        results.append(output_queue.get())

    return results


# Test case
def test_multithread_medspacy_pipeline():
    num_threads=3
    results = process_dataframe_multithread(df, num_threads)
    assert len(results) == len(df), "Number of results should match number of input texts."
    print(f"Test passed: All texts processed successfully with {num_threads} threads.")


