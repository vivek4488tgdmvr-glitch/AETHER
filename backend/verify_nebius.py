import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("NEBIUS_API_KEY")
base_url = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
requested_model = os.getenv("NEBIUS_MODEL", "").strip()

if not api_key:
    sys.exit("ERROR: Set NEBIUS_API_KEY in backend/.env")

client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0, max_retries=1)

print("Step 1/2: requesting live Token Factory model catalog...")
try:
    models = [item.id for item in client.models.list().data]
except Exception as exc:
    sys.exit(f"Catalog request failed ({type(exc).__name__}): {exc}")

nemotron = [m for m in models if "nemotron" in m.lower()]
print(f"Catalog returned {len(models)} model(s).")
print("Nemotron model IDs visible to this account:")
for model in nemotron:
    print(" -", model)

if not requested_model:
    sys.exit(
        "\nSet NEBIUS_MODEL to an exact model ID from the list, then rerun. "
        "No model has been assumed."
    )

match = next((m for m in models if m.lower() == requested_model.lower()), None)
if not match:
    sys.exit(f"\nConfigured model {requested_model!r} was not in the live catalog.")

if "nemotron" not in match.lower():
    sys.exit("The configured model ID does not appear to be a Nemotron model.")

print(f"\nStep 2/2: sending real inference request to {match}...")
try:
    response = client.chat.completions.create(
        model=match,
        messages=[
            {"role": "system", "content": "You are Aether Code, a concise coding assistant."},
            {"role": "user", "content": "Write a Python function that returns duplicate integers in a list and one small assert test."},
        ],
        max_tokens=350,
    )
    content = response.choices[0].message.content
    if not content:
        sys.exit("Inference returned an empty response.")
    print("\nSUCCESS: real inference completed.")
    print("Model:", match)
    print("Response ID:", response.id)
    print("\n--- Model response ---\n")
    print(content)
except Exception as exc:
    sys.exit(f"Inference failed ({type(exc).__name__}): {exc}")
