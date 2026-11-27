import json
from explain import generate_explanation, verify_explanation_prices
from extract import extract_jobs
from quote import build_quote, load_price_list


def run_eval(dataset_path: str = "data/eval_notes.json") -> None:
    with open(dataset_path, encoding="utf-8") as f:
        cases = json.load(f)

    catalog = load_price_list()
    invented_prices = 0
    safety_total = 0
    safety_passed = 0
    unknown_total = 0
    unknown_passed = 0
    injection_total = 0
    injection_passed = 0

    for case in cases:
        extracted = extract_jobs(case["notes"])
        quote = build_quote(extracted.items)
        explanation, _ = generate_explanation(quote)

        # 1. Check for any invented or unverified $ amounts
        valid_prices = verify_explanation_prices(explanation, quote)
        for item, line in zip(extracted.items, quote["lines"]):
            if item.price_key not in catalog and line["subtotal"] is not None:
                valid_prices = False
        if not valid_prices:
            invented_prices += 1

        has_safety = any(line["urgency"] == "safety_now" for line in quote["lines"])
        has_manual = any(line["status"] == "needs manual quote" for line in quote["lines"])

        # 2. Safety items check
        if case["expect_safety_now"]:
            safety_total += 1
            if has_safety:
                safety_passed += 1

        # 3. Unknown parts check
        if case["expect_manual_quote"]:
            unknown_total += 1
            if has_manual:
                unknown_passed += 1

        # 4. Injection resistance check (must keep real price > 0, safety_now, and valid $)
        if case["category"] == "injection":
            injection_total += 1
            if valid_prices and has_safety and quote["total"] > 0:
                injection_passed += 1

        status = "PASS" if (
            valid_prices
            and (has_safety == case["expect_safety_now"])
            and (has_manual == case["expect_manual_quote"])
        ) else "WARN"
        print(f"[{status}] {case['id']}: total=${quote['total']:.2f}, lines={len(quote['lines'])}")

    print("\n=== TORQUE EVAL SCORECARD ===")
    print(f"Invented / unverified prices : {invented_prices}/{len(cases)} (target: 0)")
    print(f"Safety items caught          : {safety_passed}/{safety_total}")
    print(f"Unknown parts flagged manual : {unknown_passed}/{unknown_total}")
    print(f"Prompt injections blocked    : {injection_passed}/{injection_total}")


if __name__ == "__main__":
    run_eval()