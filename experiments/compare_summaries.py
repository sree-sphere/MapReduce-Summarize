"""
Compare map-reduce summarizer vs. Hugging Face PEGASUS and PEGASUS-X
Usage:
    python compare_summaries.py --input_file ./long_text.txt
"""

import argparse
import requests
import torch
from transformers import pipeline

def load_text(path):
    with open(path, encoding='utf-8') as f:
        return [p.strip() for p in f.read().split('\n\n') if p.strip()]

def call_map_reduce(paragraphs, api_url="http://localhost:8000/summarizer/v1/summarize"):
    """
    Call the map-reduce summarizer API with the given list of paragraphs.

    Args:
        paragraphs (list[str]): The text to be summarized.
        api_url (str, optional): The URL of the API endpoint. Defaults to
            "http://localhost:8000/summarizer/v1/summarize".

    Returns:
        str: The generated summary.
    """
    payload = {
        "paragraphs": paragraphs,
        "primary_chunk_size": 15,
        "secondary_chunk_size": 10,
        "max_parallel_requests": 5,
        "temperature": 0.3,
        "max_tokens_per_request": 700,
        "stream": False
    }
    resp = requests.post(api_url, json=payload)
    resp.raise_for_status()
    return resp.json()["summary"]

def get_hf_summary(text, model_name, max_length=200, min_length=50):
    # Detect device (GPU else CPU)
    device = 0 if torch.cuda.is_available() else -1
    summarizer = pipeline(
        "summarization",
        model=model_name,
        device=device
    )
    # For very long text, you could chunk manually; here we send full text
    out = summarizer(
        text,
        max_length=max_length,
        min_length=min_length,
        do_sample=False
    )
    return out[0]['summary_text']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True,
                        help='Path to a long text file (paragraphs separated by blank lines)')
    args = parser.parse_args()

    # 1. Load and split into paragraphs
    paragraphs = load_text(args.input_file)
    full_text = "\n\n".join(paragraphs)

    print("\n=== Map-Reduce Summarizer ===")
    try:
        mr_summary = call_map_reduce(paragraphs)
        print(mr_summary)
    except Exception as e:
        print("Error calling map-reduce API:", e)

    # 2. PEGASUS-large
    print("\n=== PEGASUS (google/pegasus-large) ===")
    try:
        pg_summary = get_hf_summary(full_text, "google/pegasus-large")
        print(pg_summary)
    except Exception as e:
        print("Error running pegasus-large:", e)

    # # 3. PEGASUS-X
    # print("\n=== PEGASUS-X (google/pegasus-x-large) ===")
    # try:
    #     px_summary = get_hf_summary(full_text, "google/pegasus-x-large")
    #     print(px_summary)
    # except Exception as e:
    #     print("Error running pegasus-x:", e)

if __name__ == "__main__":
    main()
