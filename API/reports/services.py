"""
Service for generating Smart Insights using Google AI Studio (Gemini API).
Uses the same Gemini setup as bank statement processing for consistent behavior.
"""
import json
import re
import logging
from typing import Any

from django.conf import settings
from google import genai as google_genai

logger = logging.getLogger(__name__)


def _get_gemini_client() -> Any | None:
    """Create a Google GenAI client if the API key is configured."""
    api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
    if not api_key:
        return None

    return google_genai.Client(api_key=api_key)


def _get_model_names_to_try() -> list[str]:
    """Current Gemini text models, with optional env override first."""
    configured_model = getattr(settings, "GOOGLE_AI_MODEL", None)
    model_names = [
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
        'gemini-1.5-pro',
    ]
    if configured_model:
        return [configured_model, *[name for name in model_names if name != configured_model]]
    return model_names


def generate_smart_insights_with_ai(
    start_date: str,
    end_date: str,
    prev_start_date: str,
    prev_end_date: str,
    current_period: dict[str, Any],
    previous_period: dict[str, Any],
    top_categories: list[dict[str, Any]],
    net_worth: float,
    net_worth_change: float,
) -> dict[str, Any] | None:
    """
    Generate Smart Insights using Gemini API. Acts as a genuine financial advisor.

    Args:
        start_date: Start of selected date range (YYYY-MM-DD)
        end_date: End of selected date range (YYYY-MM-DD)
        prev_start_date: Start of previous period for comparison
        prev_end_date: End of previous period
        current_period: Dict with total_income, total_expenses, net_savings, savings_rate
        previous_period: Same structure for previous period
        top_categories: List of {category, amount}
        net_worth: Current net worth
        net_worth_change: Change in net worth this period

    Returns:
        Dict with "message" (str) and "tags" (list of str), or None if AI unavailable.
    """
    client = _get_gemini_client()
    if client is None:
        logger.warning("GOOGLE_AI_API_KEY not configured. Skipping AI insights.")
        return None

    # Build data payload scoped to the selected date range
    data_payload = {
        "selected_period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "previous_period": {
            "start_date": prev_start_date,
            "end_date": prev_end_date,
        },
        "current_period": {
            "total_income": round(current_period.get("total_income", 0), 2),
            "total_expenses": round(current_period.get("total_expenses", 0), 2),
            "net_savings": round(current_period.get("net_savings", 0), 2),
            "savings_rate_pct": round(current_period.get("savings_rate", 0), 1),
        },
        "previous_period_metrics": {
            "total_income": round(previous_period.get("total_income", 0), 2),
            "total_expenses": round(previous_period.get("total_expenses", 0), 2),
            "net_savings": round(previous_period.get("net_savings", 0), 2),
            "savings_rate_pct": round(previous_period.get("savings_rate", 0), 1),
        },
        "top_spending_categories": top_categories[:10],
        "net_worth": round(net_worth, 2),
        "net_worth_change_this_period": round(net_worth_change, 2),
    }

    prompt = f"""You are an experienced, empathetic financial advisor. A client has shared their financial data for the period {start_date} to {end_date}. Your job is to provide genuine, personalized insights—the kind a real advisor would give after reviewing their numbers. Do NOT give generic platitudes or filler. Be specific, actionable, and speak to their actual situation.

Here is the client's data (all figures are in their local currency):

{json.dumps(data_payload, indent=2, default=str)}

Based on this data, write a brief financial insight (2–4 sentences) as if you were their advisor. Focus on:
- What stands out (good or concerning) given the comparison to the previous period
- One concrete, actionable suggestion if appropriate
- A genuine observation about their spending, savings, or financial habits based on the numbers

Also suggest 1–3 short hashtag-style tags (e.g., #SavingMaster, #BelowBudget, #SpendingAlert) that capture the main takeaway. Use tags like #OnTrack, #NeedsAttention, #GreatProgress, #BelowBudget, #AboveAverage, etc.

Respond with ONLY a valid JSON object in this exact format, no other text:
{{
  "message": "Your insight text here.",
  "tags": ["#Tag1", "#Tag2"]
}}
"""

    last_error = None
    for model_name in _get_model_names_to_try():
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            response_text = (getattr(response, 'text', None) or '').strip()
            if not response_text:
                raise ValueError("Gemini returned an empty insights response")

            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                parsed = json.loads(json_match.group())
                message = parsed.get("message", "").strip()
                tags = parsed.get("tags", [])
                if isinstance(tags, list):
                    tags = [str(t).strip() for t in tags if t][:3]
                else:
                    tags = []
                return {
                    "message": message or "Review your spending and savings to stay on track.",
                    "tags": tags,
                }
            raise ValueError("Gemini response did not contain a JSON object")
        except json.JSONDecodeError as e:
            logger.warning(f"Gemini insights: failed to parse JSON from {model_name} - {e}")
            return None
        except Exception as e:
            last_error = e
            logger.warning(f"Gemini insights: API error with {model_name} - {e}")
            continue

    if last_error:
        logger.warning(f"Gemini insights unavailable after trying all models: {last_error}")

    return None
