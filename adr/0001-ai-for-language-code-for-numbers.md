# ADR 0001: AI for Language, Code for Numbers (v1 Pipeline)

## Status
Accepted

## Context
Mechanics write shorthand inspection notes that service writers must turn into itemized customer quotes. LLMs are strong at parsing messy shorthand and drafting plain-English explanations, but unreliable at arithmetic, strict rule enforcement, and resisting prompt injection. Additionally, Groq's `openai/gpt-oss-120b` does not support parallel tool calls and cannot combine `strict: true` structured outputs with tool calling in the same request.

## Decision
We adopt a 5-stage deterministic pipeline (`v1`) governed by the rule **"AI for language, code for numbers"**:
1. LLM extracts structured job items (`price_key`) using `strict: true` JSON schema.
2. Python looks up exact prices in `data/price_list.csv` (unknown keys -> `"needs manual quote"`).
3. Python forces safety-critical categories (brakes, steering, tires, suspension) to `safety_now`.
4. LLM drafts a customer-facing explanation from the finalized quote.
5. Python verifies every `$` figure in the explanation matches the quote, falling back to a template on mismatch.

## Options Considered
* **Single-Pass Prompt:** Fast (1 call), but lets the LLM compute prices and urgencies probabilistically, risking silent financial or safety errors.
* **Tool-Calling Agent Loop (`v2`):** Scales to large catalogs, but sequential tool calls on Groq add latency ($N + 1$ round-trips) and lose `strict: true` schema guarantees.

## Trade-offs
* **Pros:** Zero invented prices, 100% deterministic safety tagging, predictable 2-call latency, and defense in depth.
* **Cons:** Requires the valid `price_key` list to fit in the extraction prompt/schema.

## When We Would Revisit
When the shop's price catalog grows beyond ~200 items or requires dynamic multi-step database search (evaluated via `v2` agent benchmark in Phase 8).