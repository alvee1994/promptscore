#!/usr/bin/env python3
"""
Prompt Score — Create all 3 Tally forms via direct API
Run: python create_promptscore_forms.py
Requires: pip install requests
"""

import requests
import uuid
import json

API_KEY = "YOUR_TALLY_API_KEY"  # Replace with your key
BASE_URL = "https://api.tally.so/forms"
HEADERS = {
    "Authorization": f"Bearer tly-10bPCAzs1AlQLuS4rZXq5RNNazoetbYG",
    "Content-Type": "application/json"
}

def uid():
    return str(uuid.uuid4())

# ─────────────────────────────────────────────
# HELPER: build a simple text question group
# ─────────────────────────────────────────────
def text_question(label, placeholder="", required=False, input_type="INPUT_TEXT"):
    group_uuid = uid()
    blocks = [
        {
            "uuid": uid(),
            "type": "TITLE",
            "groupUuid": uid(),
            "groupType": "TITLE",
            "payload": {"html": label}
        },
        {
            "uuid": uid(),
            "type": input_type,
            "groupUuid": group_uuid,
            "groupType": input_type,
            "payload": {
                "isRequired": required,
                "placeholder": placeholder
            }
        }
    ]
    return blocks

def dropdown_question(label, options, required=False):
    group_uuid = uid()
    blocks = [
        {
            "uuid": uid(),
            "type": "TITLE",
            "groupUuid": uid(),
            "groupType": "TITLE",
            "payload": {"html": label}
        }
    ]
    for i, opt in enumerate(options):
        blocks.append({
            "uuid": uid(),
            "type": "DROPDOWN_OPTION",
            "groupUuid": group_uuid,
            "groupType": "DROPDOWN",
            "payload": {"text": opt, "index": i, "isFirst": i == 0, "isLast": i == len(options) - 1, "isRequired": required}
        })
    return blocks

def multiselect_question(label, options, required=False):
    group_uuid = uid()
    blocks = [
        {
            "uuid": uid(),
            "type": "TITLE",
            "groupUuid": uid(),
            "groupType": "TITLE",
            "payload": {"html": label}
        }
    ]
    for i, opt in enumerate(options):
        blocks.append({
            "uuid": uid(),
            "type": "MULTIPLE_CHOICE_OPTION",
            "groupUuid": group_uuid,
            "groupType": "MULTIPLE_CHOICE",
            "payload": {"text": opt, "index": i, "isFirst": i == 0, "isLast": i == len(options) - 1, "isRequired": required}
        })
    return blocks

def text_block(html):
    return [{
        "uuid": uid(),
        "type": "TEXT",
        "groupUuid": uid(),
        "groupType": "TEXT",
        "payload": {"html": html}
    }]

def hidden_fields(*names):
    fields = [{"uuid": uid(), "name": n} for n in names]
    return [{
        "uuid": uid(),
        "type": "HIDDEN_FIELDS",
        "groupUuid": uid(),
        "groupType": "HIDDEN_FIELDS",
        "payload": {"hiddenFields": fields}
    }]

def page_break(thank_you=False):
    return [{
        "uuid": uid(),
        "type": "PAGE_BREAK",
        "groupUuid": uid(),
        "groupType": "PAGE_BREAK",
        "payload": {"isThankYouPage": thank_you}
    }]

def heading(html, level=2):
    t = f"HEADING_{level}"
    return [{
        "uuid": uid(),
        "type": t,
        "groupUuid": uid(),
        "groupType": t,
        "payload": {"html": html}
    }]

PROMPT_INSTRUCTIONS = (
    f"Each prompt must be <strong>at least 10 characters</strong> and written as a real buyer search "
    f"(e.g. <em>\"best cloud consultant Rotterdam\"</em>).<br><br>"
    f"💡 <strong>Already a customer?</strong> "
    f"<a href=\"https://promptscore.io/my-prompts?cid={{customer_id}}\">View &amp; copy your current prompts here</a> "
    f"— then leave fields below <strong>blank</strong> to keep them unchanged."
)

# ─────────────────────────────────────────────
# FORM 1: STARTER
# ─────────────────────────────────────────────
def build_starter():
    blocks = []
    blocks += [{
        "uuid": uid(), "type": "FORM_TITLE",
        "groupUuid": uid(), "groupType": "TEXT",
        "payload": {"html": "Prompt Score — Starter Setup"}
    }]
    blocks += hidden_fields("customer_id", "email", "plan")
    blocks += text_question("Brand name", "e.g. Prompt Score", required=True)
    blocks += text_question("Brand website", "e.g. https://promptscore.io", required=True, input_type="INPUT_LINK")
    blocks += dropdown_question("Industry", ["B2B SaaS", "Digital Agency", "Consulting", "E-commerce", "Other"], required=True)
    blocks += text_question("Primary market", "e.g. Rotterdam, Netherlands", required=True)
    blocks += heading("Your 10 buyer-intent prompts")
    blocks += text_block(PROMPT_INSTRUCTIONS)
    for i in range(1, 11):
        blocks += text_question(f"Prompt {i}", "Leave blank to keep existing", required=False)
    blocks += page_break(thank_you=True)
    blocks += heading("You're all set! 🎉")
    blocks += text_block(
        "Your settings have been saved. Prompt Score will run your prompts through ChatGPT this week "
        "and send your first report to your inbox.<br><br>"
        "Want competitor tracking + 3 AI engines? <a href=\"https://promptscore.io/upgrade\">Upgrade to Pro →</a>"
    )
    return {
        "status": "PUBLISHED",
        "blocks": blocks,
        "settings": {
            "styles": {
                "theme": "CUSTOM",
                "color": {
                    "background": "#ffffff", "text": "#1a1a1a",
                    "accent": "#6366f1", "buttonBackground": "#6366f1", "buttonText": "#ffffff"
                }
            }
        }
    }

# ─────────────────────────────────────────────
# FORM 2: PRO
# ─────────────────────────────────────────────
def build_pro():
    blocks = []
    blocks += [{
        "uuid": uid(), "type": "FORM_TITLE",
        "groupUuid": uid(), "groupType": "TEXT",
        "payload": {"html": "Prompt Score — Pro Setup"}
    }]
    blocks += hidden_fields("customer_id", "email", "plan")
    blocks += text_question("Brand name", "e.g. Prompt Score", required=True)
    blocks += text_question("Brand website", "e.g. https://promptscore.io", required=True, input_type="INPUT_LINK")
    blocks += text_question("Competitor #1", "e.g. BrandRadar", required=True)
    blocks += text_question("Competitor #2", "e.g. Mention.com (optional)", required=False)
    blocks += dropdown_question("Industry", ["B2B SaaS", "Digital Agency", "Consulting", "E-commerce", "Other"], required=True)
    blocks += text_question("Primary market", "e.g. Netherlands", required=True)
    blocks += dropdown_question("Prompt language", ["English only", "Dutch only", "Both English and Dutch"], required=True)
    blocks += multiselect_question("AI engines to monitor", ["ChatGPT", "Perplexity", "Gemini"], required=True)
    blocks += heading("Your 50 buyer-intent prompts")
    blocks += text_block(
        PROMPT_INSTRUCTIONS + "<br><br>"
        "For 50 prompts, paste one per line in the field below. "
        "<strong>Leave blank to keep your existing prompts unchanged.</strong>"
    )
    blocks += [{
        "uuid": uid(), "type": "TITLE",
        "groupUuid": uid(), "groupType": "TITLE",
        "payload": {"html": "Your prompts (one per line, max 50)"}
    },
    {
        "uuid": uid(), "type": "TEXTAREA",
        "groupUuid": uid(), "groupType": "TEXTAREA",
        "payload": {
            "isRequired": False,
            "placeholder": "Leave blank to keep your existing prompts unchanged.\n\nIf replacing, paste up to 50 prompts here, one per line.\nEach must be at least 10 characters."
        }
    }]
    blocks += page_break(thank_you=True)
    blocks += heading("You're all set! 🎉")
    blocks += text_block(
        "Your settings have been saved. Prompt Score will monitor your brand and 2 competitors "
        "across 3 AI engines and deliver your weekly report.<br><br>"
        "Running an agency? <a href=\"https://promptscore.io/upgrade\">See Agency plan →</a>"
    )
    return {
        "status": "PUBLISHED",
        "blocks": blocks,
        "settings": {
            "styles": {
                "theme": "CUSTOM",
                "color": {
                    "background": "#ffffff", "text": "#1a1a1a",
                    "accent": "#6366f1", "buttonBackground": "#6366f1", "buttonText": "#ffffff"
                }
            }
        }
    }

# ─────────────────────────────────────────────
# FORM 3: AGENCY
# ─────────────────────────────────────────────
def build_agency():
    blocks = []
    blocks += [{
        "uuid": uid(), "type": "FORM_TITLE",
        "groupUuid": uid(), "groupType": "TEXT",
        "payload": {"html": "Prompt Score — Agency Setup"}
    }]
    blocks += hidden_fields("customer_id", "email", "plan")
    blocks += text_block(
        "You can monitor up to <strong>5 brands</strong>. Fill in as many as you need — leave unused slots blank."
    )
    for i in range(1, 6):
        blocks += text_question(f"Brand {i} name", f"e.g. Client {i} (leave blank if unused)", required=(i == 1))
        blocks += text_question(f"Brand {i} website", f"e.g. https://client{i}.com", required=False, input_type="INPUT_LINK")
    blocks += text_question(
        "Competitors to track (all brands)",
        "e.g. HubSpot, Salesforce, Monday.com — comma-separated, max 5",
        required=True
    )
    blocks += text_question("Primary market", "e.g. Netherlands, Germany", required=True)
    blocks += dropdown_question("Prompt language", ["English only", "Dutch only", "Both English and Dutch"], required=True)
    blocks += heading("Your prompts (up to 200)")
    blocks += text_block(
        "For Agency tier, manage your prompts in a <strong>Google Sheet</strong> — one prompt per row in column A, no header.<br><br>"
        "Make the sheet publicly readable (Share → Anyone with the link → Viewer), then paste the URL below.<br><br>"
        "💡 <strong>Already submitted?</strong> Leave blank to keep your existing prompts. "
        "Paste a new URL only if you want to replace the full list."
    )
    blocks += text_question(
        "Google Sheet URL (your prompt list)",
        "e.g. https://docs.google.com/spreadsheets/d/...",
        required=False,
        input_type="INPUT_LINK"
    )
    blocks += heading("White-label report settings")
    blocks += text_question("Agency / report header name", "e.g. Acme Digital — AI Visibility Report", required=True)
    blocks += text_question(
        "Logo URL (direct image link)",
        "e.g. https://yoursite.com/logo.png",
        required=False,
        input_type="INPUT_LINK"
    )
    blocks += page_break(thank_you=True)
    blocks += heading("You're all set! 🎉")
    blocks += text_block(
        "Your agency account is configured. Prompt Score will monitor all your brands across 3 AI engines "
        "and deliver white-label PDF reports every week."
    )
    return {
        "status": "PUBLISHED",
        "blocks": blocks,
        "settings": {
            "styles": {
                "theme": "CUSTOM",
                "color": {
                    "background": "#ffffff", "text": "#1a1a1a",
                    "accent": "#6366f1", "buttonBackground": "#6366f1", "buttonText": "#ffffff"
                }
            }
        }
    }

# ─────────────────────────────────────────────
# CREATE ALL FORMS
# ─────────────────────────────────────────────
forms = [
    ("Starter", build_starter()),
    ("Pro",     build_pro()),
    ("Agency",  build_agency()),
]

results = {}
for name, payload in forms:
    resp = requests.post(BASE_URL, headers=HEADERS, json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        form_id = data.get("id")
        url = f"https://tally.so/r/{form_id}"
        results[name] = {"id": form_id, "url": url}
        print(f"✅ {name} form created: {url}")
    else:
        print(f"❌ {name} failed: {resp.status_code} — {resp.text}")

print("\n--- FORM IDs (save these for n8n) ---")
for name, info in results.items():
    print(f"{name}: {info['id']}  →  {info['url']}")
