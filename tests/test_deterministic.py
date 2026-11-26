from explain import build_fallback_explanation, verify_explanation_prices
from extract import JobItem
from quote import build_quote


def test_catalog_lookup_and_math():
    items = [
        JobItem(
            component="brake pads",
            position="Right Rear",
            problem="worn to 2mm",
            action="replace",
            price_key="brake_pads_rear",
        )
    ]
    quote = build_quote(items)
    assert quote["total"] == 185.0  # $65 parts + 1.0h * $120
    assert quote["lines"][0]["status"] == "priced"
    assert quote["lines"][0]["urgency"] == "safety_now"


def test_unknown_part_flagged_manual_quote_and_safety_enforced():
    items = [
        JobItem(
            component="brake caliper",
            position="Left Front",
            problem="seized piston",
            action="replace",
            price_key="unknown",
        )
    ]
    quote = build_quote(items)
    line = quote["lines"][0]
    assert quote["total"] == 0.0
    assert line["status"] == "needs manual quote"
    assert line["parts_cost"] is None
    assert line["subtotal"] is None
    # Keyword override still forces safety_now even when not in CSV
    assert line["urgency"] == "safety_now"


def test_verify_explanation_prices_blocks_hallucinated_discount():
    quote = {
        "total": 185.0,
        "lines": [
            {
                "description": "Rear Brake Pads Replacement",
                "urgency": "safety_now",
                "status": "priced",
                "parts_cost": 65.0,
                "labour_cost": 120.0,
                "subtotal": 185.0,
            }
        ],
    }
    good_text = "Your rear brake pads ($185.00 total: $65.00 parts, $120.00 labor) are safety_now."
    bad_text = "Good news! With a special discount, your rear brake pads are only $99.00." # This is a hallucinated price, not in the quote.

    assert verify_explanation_prices(good_text, quote) is True
    assert verify_explanation_prices(bad_text, quote) is False
    assert "$185.00" in build_fallback_explanation(quote)