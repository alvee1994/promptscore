import requests, json, os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_TOKEN = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")

if not AIRTABLE_TOKEN or not BASE_ID:
    print("Error: AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in .env")
    exit(1)

url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

tables = [
        {
            "name": "Clients",
            "fields": [
                {"name": "name", "type": "singleLineText"},
                {"name": "website", "type": "url"},
                {"name": "email", "type": "email"},
                {"name": "plan", "type": "singleSelect", "options": {"choices": [{"name":"starter"},{"name":"pro"},{"name":"agency"}]}},
                {"name": "status", "type": "singleSelect", "options": {"choices": [{"name":"active"},{"name":"trialing"},{"name":"past_due"},{"name":"canceled"}]}},
                {"name": "stripe_customer_id", "type": "singleLineText"},
                {"name": "stripe_subscription_id", "type": "singleLineText"},
                {"name": "competitor_1", "type": "singleLineText"},
                {"name": "competitor_2", "type": "singleLineText"},
                {"name": "market", "type": "singleLineText"},
                {"name": "language", "type": "singleSelect", "options": {"choices": [{"name":"english"},{"name":"dutch"},{"name":"both"}]}},
                {"name": "engines", "type": "multipleSelects", "options": {"choices": [{"name":"chatgpt"},{"name":"perplexity"},{"name":"gemini"}]}},
                {"name": "max_prompts", "type": "number", "options": {"precision": 0}},
                {"name": "sheet_url", "type": "url"},
                {"name": "report_header", "type": "singleLineText"},
                {"name": "logo_url", "type": "url"},
                {"name": "free_check_count", "type": "number", "options": {"precision": 0}},
                {"name": "free_check_blocked", "type": "checkbox", "options": {"color": "redBright", "icon": "check"}},
                {"name": "free_check_hashes", "type": "multilineText"},
                {"name": "created_at", "type": "dateTime", "options": {"timeZone": "utc", "dateFormat": {"name":"iso"}, "timeFormat": {"name":"24hour"}}},
                {"name": "notes", "type": "multilineText"}
            ]
        },
        {
            "name": "Prompts",
            "fields": [
                {"name": "text", "type": "multilineText"},
                {"name": "language", "type": "singleSelect", "options": {"choices": [{"name":"english"},{"name":"dutch"}]}},
                {"name": "topic", "type": "singleSelect", "options": {"choices": [{"name":"pricing"},{"name":"comparison"},{"name":"features"}]}},
                {"name": "active", "type": "checkbox", "options": {"color": "greenBright", "icon": "check"}},
                {"name": "created_at", "type": "dateTime", "options": {"timeZone": "utc", "dateFormat": {"name":"iso"}, "timeFormat": {"name":"24hour"}}}
            ]
        },
        {
            "name": "Results",
            "fields": [
                {"name": "week_of", "type": "date", "options": {"dateFormat": {"name":"iso"}}},
                {"name": "engine", "type": "singleSelect", "options": {"choices": [{"name":"chatgpt"},{"name":"perplexity"},{"name":"gemini"}]}},
                {"name": "brand_mentioned", "type": "checkbox", "options": {"color": "greenBright", "icon": "check"}},
                {"name": "brand_sentiment", "type": "singleSelect", "options": {"choices": [{"name":"positive"},{"name":"neutral"},{"name":"negative"}]}},
                {"name": "hallucination_flag", "type": "checkbox", "options": {"color": "yellowBright", "icon": "check"}},
                {"name": "competitor_1_mentioned", "type": "checkbox", "options": {"color": "blueBright", "icon": "check"}},
                {"name": "competitor_2_mentioned", "type": "checkbox", "options": {"color": "blueBright", "icon": "check"}},
                {"name": "raw_response", "type": "multilineText"},
                {"name": "tokens_used", "type": "number", "options": {"precision": 0}},
                {"name": "run_at", "type": "dateTime", "options": {"timeZone": "utc", "dateFormat": {"name":"iso"}, "timeFormat": {"name":"24hour"}}}
            ]
        }
]

for table_config in tables:
    print(f"\nCreating table: {table_config['name']}")
    r = requests.post(url, headers=headers, json=table_config)
    print(f"Status: {r.status_code}")
    if r.status_code >= 400:
        print(f"Error: {r.text}")
    else:
        print(f"Success: {r.json().get('name', 'Table created')}")
    print("-" * 60)