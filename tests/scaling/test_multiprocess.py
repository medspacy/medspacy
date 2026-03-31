import pandas as pd
import multiprocessing as mp
import medspacy
from medspacy.ner import TargetRule
import json
import os

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
    target_matcher.result_type = 'group'
    target_matcher.add(target_rules)
    return nlp


# Function to process text using MedSpaCy
def process_text(text):
    print(f"Process ID: {os.getpid()} | Processing text: {text}")
    nlp = create_nlp()
    doc = nlp(text)
    return doc


# Function to process DataFrame with multiprocessing
def process_dataframe_multiprocess(df, num_processes):
    with mp.Pool(num_processes) as pool:
        results = pool.map(process_text, df['text'])

    return results


# Test case
def test_multiprocess_medspacy_pipeline():
    num_processes=3
    results = process_dataframe_multiprocess(df, num_processes)
    assert len(results) == len(df), "Number of results should match number of input texts."
    print(f"Test passed: All texts processed successfully with {num_processes} processes.")


