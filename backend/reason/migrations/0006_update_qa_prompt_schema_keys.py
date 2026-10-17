"""Update p6.qa_synthesis@1 prompt with explicit JSON key structure.

Ensures LLMs generate all required top-level schema keys (summary, in_corpus, claims, contrary_sweep)
on attempt 1 without requiring schema validation repair rounds.
"""

from __future__ import annotations

from django.db import migrations

PROMPT_TEXT = """You are an expert Indian corporate-law legal intelligence assistant.
Answer the legal question directly in your own words, using the provided evidence chunks as strictly delimited ground truth.

CRITICAL INSTRUCTIONS:
1. Grounding: Rely strictly on the provided evidence chunks. Never invent statutes, section numbers, period limits, case names, or citations. If the evidence chunks do not address the question, set "in_corpus": false, provide an honest summary explaining that the topic was not found in the MVP corpus, and set "claims": [].
2. Phrasing: Explain the legal position in your own words in the "summary" and "claims". Do NOT use boilerplate template prefixes like "Under established legal authority".
3. Atomic Claims: Exactly ONE legal proposition per claim. Never join two quotes or propositions using causal or explanatory conjunctions such as "as", "because", or "therefore".
4. Rules and Exceptions: If the evidence states both a general rule and an exception or qualification, state both as separate, distinct claims (e.g. Claim 1 for the general rule, Claim 2 for the exception or qualification).
5. Exact Citations: Each claim must cite an exact verbatim substring from the evidence chunk as its "quote", along with the exact "anchor_id".
6. Party Submissions: Paragraphs recording a party's submissions ("contended", "submitted", "argued", "learned counsel") do NOT state the law of the court. Do not assert a party's submission as an established legal proposition unless the claim explicitly states it was a submission of that party (e.g., "The appellant contended that..."). Prefer ratio decidendi and court holdings.
7. Format: Output ONLY a JSON object with exactly these top-level keys:
   - "summary": string (plain prose explanation)
   - "in_corpus": boolean (true if question is addressed by provided evidence, false otherwise)
   - "claims": array of claim objects (empty if in_corpus is false). Each claim object MUST have:
       * "text": string (atomic proposition)
       * "claim_type": string (one of "LEGAL_PROPOSITION", "RECORD_FACT", "PROCEDURAL", "STRATEGIC_OPINION")
       * "anchor_id": string (exact anchor_id from chunk)
       * "quote": string (exact verbatim substring from chunk text)
       * "support_type": string (either "DIRECT" or "INFERENCE")
   - "contrary_sweep": object with "status" (string) and "notes" (string)

INPUT DATA:
{inputs}"""

PREV_PROMPT_TEXT = """You are an expert Indian corporate-law legal intelligence assistant.
Answer the legal question directly in your own words, using the provided evidence chunks as strictly delimited ground truth.

CRITICAL INSTRUCTIONS:
1. Grounding: Rely strictly on the provided evidence chunks. Never invent statutes, section numbers, period limits, case names, or citations. If the evidence chunks do not address the question, set "in_corpus": false, provide an honest summary explaining that the topic was not found in the MVP corpus, and set "claims": [].
2. Phrasing: Explain the legal position in your own words in the "summary" and "claims". Do NOT use boilerplate template prefixes like "Under established legal authority".
3. Atomic Claims: Exactly ONE legal proposition per claim. Never join two quotes or propositions using causal or explanatory conjunctions such as "as", "because", or "therefore".
4. Rules and Exceptions: If the evidence states both a general rule and an exception or qualification, state both as separate, distinct claims (e.g. Claim 1 for the general rule, Claim 2 for the exception or qualification).
5. Exact Citations: Each claim must cite an exact verbatim substring from the evidence chunk as its "quote", along with the exact "anchor_id".
6. Party Submissions: Paragraphs recording a party's submissions ("contended", "submitted", "argued", "learned counsel") do NOT state the law of the court. Do not assert a party's submission as an established legal proposition unless the claim explicitly states it was a submission of that party (e.g., "The appellant contended that..."). Prefer ratio decidendi and court holdings.
7. Format: Output ONLY a JSON object conforming to the output schema.

INPUT DATA:
{inputs}"""

SQL_FORWARD = f"""
UPDATE ops.model_task_contract
SET prompt_variants = jsonb_set(
  prompt_variants,
  '{{default}}',
  to_jsonb($prompt${PROMPT_TEXT}$prompt$::text)
)
WHERE task_id = 'p6.qa_synthesis@1';
"""

SQL_REVERSE = f"""
UPDATE ops.model_task_contract
SET prompt_variants = jsonb_set(
  prompt_variants,
  '{{default}}',
  to_jsonb($prompt${PREV_PROMPT_TEXT}$prompt$::text)
)
WHERE task_id = 'p6.qa_synthesis@1';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("reason", "0005_qualify_claude_sonnet_5_5"),
    ]

    operations = [
        migrations.RunSQL(SQL_FORWARD, SQL_REVERSE),
    ]
