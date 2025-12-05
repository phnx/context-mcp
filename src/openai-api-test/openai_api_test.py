import os
from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")

if api_key is None:
    print("Cannot load API key from env, exit")
    exit(1)

client = OpenAI(api_key=api_key)

prompt = "Hello, test successful?"
print("Prompt:", prompt)
resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
)
print("Response:", resp.choices[0].message.content)
