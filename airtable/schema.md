# Shave Of Voice, Checked! — Airtable Base Schema

Three tables. All linked. No extra fields.

---

## Table 1: Clients

The master record for each paying customer.

| Field | Type | Notes |
|---|---|---|
| `name` | Single line text | Brand name |
| `website` | URL | Brand website |
| `email` | Email | Primary contact |
| `plan` | Single select | `starter`, `pro`, `agency` |
| `status` | Single select | `active`, `trialing`, `past_due`, `canceled` |
| `stripe_customer_id` | Single line text | Stripe customer ID |
| `stripe_subscription_id` | Single line text | Stripe subscription ID |
| `competitor_1` | Single line text | First named competitor |
| `competitor_2` | Single line text | Optional second competitor |
| `market` | Single line text | Primary geographic market |
| `language` | Single select | `english`, `dutch`, `both` |
| `engines` | Multiple select | `chatgpt`, `perplexity`, `gemini` |
| `max_prompts` | Number | Max prompts per week (plan limit) |
| `sheet_url` | URL | Google Sheet URL (Agency tier only) |
| `report_header` | Single line text | White-label report header name |
| `logo_url` | URL | White-label logo (Agency tier only) |
| `free_check_count` | Number | Count of free check requests (anti-abuse) |
| `free_check_blocked` | Checkbox | Flagged for abuse |
| `free_check_hashes` | Long text | JSON array of hashed IPs/devices |
| `created_at` | Date | ISO timestamp |
| `notes` | Long text | Internal notes |

---

## Table 2: Prompts

One row per tracked prompt, linked to a client.

| Field | Type | Notes |
|---|---|---|
| `client` | Link → Clients | Links to parent client |
| `text` | Long text | The actual prompt string |
| `language` | Single select | `english`, `dutch` |
| `topic` | Single select | Optional cluster tag (e.g. `pricing`, `comparison`, `features`) |
| `active` | Checkbox | Include in weekly run |
| `created_at` | Date | ISO timestamp |

---

## Table 3: Results

Weekly mention data per prompt per engine.

| Field | Type | Notes |
|---|---|---|
| `client` | Link → Clients | Links to parent client |
| `prompt` | Link → Prompts | Links to prompt row |
| `week_of` | Date | Monday of the reporting week |
| `engine` | Single select | `chatgpt`, `perplexity`, `gemini` |
| `brand_mentioned` | Checkbox | Did client brand appear? |
| `brand_sentiment` | Single select | `positive`, `neutral`, `negative` |
| `hallucination_flag` | Checkbox | Mentioned but description looks wrong |
| `competitor_1_mentioned` | Checkbox | Competitor #1 appeared? |
| `competitor_2_mentioned` | Checkbox | Competitor #2 appeared? |
| `raw_response` | Long text | Raw AI response text (keep for debugging) |
| `tokens_used` | Number | Approximate token count |
| `run_at` | Date | ISO timestamp of the run |

---

## Calculated Fields (Views / Formulas)

In the **Results** view, add these formula fields to the Clients table for reporting:

```
mention_rate = SUM(Results.brand_mentioned) / COUNT(Results)  [per client, per week]
competitor_gap = competitor_1_mention_rate - brand_mention_rate
```

---

## View Strategy

### Clients table views:
- **Active** — filter `status` is `active` OR `trialing`
- **Needs Attention** — filter `status` is `past_due` OR `free_check_blocked` is checked
- **Canceled** — filter `status` is `canceled`

### Results table views:
- **Latest Week** — sort by `week_of` descending, grouped by client
- **Trending Down** — filter `brand_mentioned` is empty + previous week was checked

---

## Import Instructions

1. Create a new Airtable base named **Shave Of Voice, Checked!**
2. Create three tables: **Clients**, **Prompts**, **Results**
3. Add fields per the schema above
4. Set up linked fields:
   - Prompts `client` → Links to Clients
   - Results `client` → Links to Clients
   - Results `prompt` → Links to Prompts
5. Set up the **Active** view filter in Clients
6. Copy the Base ID from the Airtable URL: `airtable.com/{BASE_ID}/...`
7. Add `AIRTABLE_BASE_ID` to your `.env`
