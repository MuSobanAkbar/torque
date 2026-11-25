import json
import os
import re
from dotenv import load_dotenv
from groq import Groq
from extract import extract_jobs
from quote import build_quote

load_dotenv()


def verify_explanation_prices(text: str, quote: dict) -> bool:
    """Verify every $ amount in the LLM explanation matches a real number in the quote."""
    allowed_amounts = {round(float(quote["total"]), 2)}
    for line in quote["lines"]:
        for field in ("parts_cost", "labour_cost", "subtotal"):
            if line[field] is not None:
                allowed_amounts.add(round(float(line[field]), 2))

    # Find every $123 or $123.45 in the AI's generated text
    found_strings = re.findall(r"\$([0-9]+(?:\.[0-9]{1,2})?)", text)
    for raw in found_strings:
        if round(float(raw), 2) not in allowed_amounts:
            return False
    return True


def build_fallback_explanation(quote: dict) -> str:
    """Deterministic safe template used if the LLM invents or misstates any $ amount."""
    parts = ["Here is a summary of your vehicle inspection:"]
    for line in quote["lines"]:
        if line["status"] == "needs manual quote":
            parts.append(f"- {line['description']} ({line['urgency']}): needs manual quote.")
        else:
            parts.append(f"- {line['description']} ({line['urgency']}): ${line['subtotal']:.2f}.")
    parts.append(f"Estimated total for priced items: ${quote['total']:.2f}.")
    return "\n".join(parts)


def generate_explanation(quote: dict) -> tuple[str, bool]:
    """Returns (explanation_text, used_fallback)."""
    prompt = f"""Write a short, friendly, plain-English summary for a car owner based ONLY on this quote JSON.
Explain what needs immediate attention (safety_now) vs what can wait.
Every dollar amount you write MUST match the exact numbers in the JSON. Do not invent prices or discounts.

<quote>
{json.dumps(quote, indent=2)}
</quote>"""

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    draft = response.choices[0].message.content.strip()

    if verify_explanation_prices(draft, quote):
        return draft, False
    return build_fallback_explanation(quote), True


if __name__ == "__main__":
    sample = input("Paste mechanic notes: ")
    extracted = extract_jobs(sample)
    quote = build_quote(extracted.items)
    explanation, used_fallback = generate_explanation(quote)

    print("\n--- ITEMIZED QUOTE ---")
    print(json.dumps(quote, indent=2))
    print(f"\n--- CUSTOMER EXPLANATION (fallback={used_fallback}) ---")
    print(explanation)