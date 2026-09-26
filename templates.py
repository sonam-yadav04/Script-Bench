
WORD_BUDGETS = {
    30: {"hook": 15, "body": 40, "cta": 10},
    45: {"hook": 20, "body": 65, "cta": 12},
    60: {"hook": 25, "body": 90, "cta": 15},
}

NICHE_STYLES = {
    "fitness":      "energetic, motivational, use power verbs",
    "finance":      "authoritative yet approachable, data-driven",
    "beauty":       "warm, aspirational, sensory language",
    "tech":         "crisp, smart, forward-looking, avoid jargon overload",
    "food":         "mouth-watering, vivid, sensory-rich",
    "education":    "clear, engaging, use curiosity gaps",
    "travel":       "wanderlust-evoking, descriptive, adventurous",
    "gaming":       "fast-paced, enthusiastic, community-aware",
    "mental health":"empathetic, calm, non-preachy",
    "business":     "professional, results-oriented, concise",
    "fashion":      "trendy, aspirational, confident",
    "parenting":    "relatable, warm, practical",
}

DEFAULT_STYLE = "engaging, conversational, direct"

HOOK_ARCHETYPES = [
    "Bold Claim  – State a surprising fact or bold opinion instantly",
    "Pain Point  – Name a struggle your audience knows deeply",
    "Curiosity Gap – Tease what they will learn without giving it away",
    "Pattern Interrupt – Say or ask something unexpected",
    "Story Hook  – Drop mid-action into a micro-story (no slow intro)",
]

CTA_FORMULAS = [
    "Follow for more [niche] tips",
    "Save this so you don not forget",
    "Comment [keyword] and I will DM you the full guide",
    "Share this with someone who needs to hear it",
    "Link in bio for the full breakdown",
]

SYSTEM_PROMPT = """You are ScriptBench, an expert short-form video scriptwriter.
You write punchy, high-retention scripts for TikTok, Instagram Reels, and YouTube Shorts.

Core rules you NEVER break:
1. NO fluff, NO slow intros — hook must grab within 3 words.
2. Every sentence must earn its place; delete anything that does not serve the viewer.
3. Write as SPOKEN WORD — contractions, short sentences, natural pauses (use "..." for breath).
4. Stay within the word budget for each section.
5. The CTA must feel natural, not bolted on.
6. Match tone to the niche perfectly.
7. Output ONLY valid JSON — no markdown fences, no extra keys."""


def build_prompt(niche: str, topic: str, target_seconds: int) -> str:
    budget = WORD_BUDGETS.get(target_seconds, WORD_BUDGETS[60])
    style  = NICHE_STYLES.get(niche.lower().strip(), DEFAULT_STYLE)

    hooks_list  = "\n  ".join(f"- {h}" for h in HOOK_ARCHETYPES)
    cta_list    = "\n  ".join(f"- {c}" for c in CTA_FORMULAS)

    return f"""Generate a {target_seconds}-second short-form video script.

INPUTS:
  Niche:   {niche}
  Topic:   {topic}
  Length:  {target_seconds} seconds

STYLE GUIDE for this niche:
  {style}

WORD BUDGETS (strict):
  hook: ~{budget["hook"]} words
  body: ~{budget["body"]} words
  cta:  ~{budget["cta"]} words

HOOK — pick the strongest archetype:
  {hooks_list}

CTA — choose what fits best:
  {cta_list}

Return ONLY this JSON (no extra text):
{{
  "hook": "<opening line that stops the scroll>",
  "body": "<core content — punchy sentences, natural spoken rhythm>",
  "cta":  "<one clear call-to-action>",
  "style_note": "<one sentence explaining tone/hook choice>",
  "estimated_seconds": {target_seconds}
}}"""
