import csv
import json
from extract import JobItem, extract_jobs

LABOUR_RATE = 120.0  # Shop rate: $120/hour
# ADDED: Safety keywords enforced in code even if a part isn't in price_list.csv
SAFETY_KEYWORDS = ("brake", "pad", "rotor", "steer", "tie rod", "tire", "suspension", "strut", "shock", "ball joint")


def load_price_list(path: str = "data/price_list.csv") -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        return {row["price_key"]: row for row in csv.DictReader(f)}


# ADDED: Deterministic urgency rule — safety items are ALWAYS "safety_now"
def determine_urgency(item: JobItem, row: dict | None) -> str:
    if row is not None and row["safety"].strip().lower() == "true":
        return "safety_now"
    text = f"{item.component} {item.problem}".lower()
    if any(word in text for word in SAFETY_KEYWORDS):
        return "safety_now"
    if any(word in text for word in ("torn", "leak", "worn", "crack")):
        return "soon"
    return "can_wait"


def build_quote(items: list[JobItem]) -> dict:
    catalog = load_price_list()
    lines = []
    total = 0.0

    for item in items:
        row = catalog.get(item.price_key)
        urgency = determine_urgency(item, row)  # ADDED: compute urgency in code

        # ADDED: Unknown or made-up key -> flag for human review, never guess a price
        if row is None:
            lines.append(
                {
                    "component": item.component,
                    "position": item.position,
                    "description": f"{item.action.capitalize()} {item.component}",
                    "urgency": urgency,
                    "status": "needs manual quote",
                    "parts_cost": None,
                    "labour_cost": None,
                    "subtotal": None,
                }
            )
            continue

        parts = float(row["parts_cost"])
        labour = round(float(row["labour_hours"]) * LABOUR_RATE, 2)
        subtotal = round(parts + labour, 2)
        total = round(total + subtotal, 2)

        lines.append(
            {
                "component": item.component,
                "position": item.position,
                "description": row["description"],
                "urgency": urgency,  # ADDED
                "status": "priced",  # ADDED
                "parts_cost": parts,
                "labour_cost": labour,
                "subtotal": subtotal,
            }
        )

    return {"lines": lines, "total": total}


if __name__ == "__main__":
    sample = input("Paste mechanic notes: ")
    extracted = extract_jobs(sample)
    quote = build_quote(extracted.items)
    print(json.dumps(quote, indent=2))