import os

import tiktoken

MODEL = os.getenv("OPENAI_MODEL")
encoding = tiktoken.encoding_for_model(MODEL)


def count_tokens(text):
    return len(encoding.encode(text))
