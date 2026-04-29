# PromptScore — AI Brand Visibility Monitor
> **⚠️ Name TBD — confirm domain availability before finalising**

> *"Is your business invisible to AI? Find out in 60 seconds."*
>
> PromptScore runs weekly prompts through ChatGPT, Perplexity, and Gemini, tracks whether your brand appears vs. competitors, and delivers a plain email report every Monday. No dashboard. No onboarding. Just a score in your inbox.

---

## Positioning

**Target customer:** B2B SaaS marketers, digital agencies, CMOs who need to show AI search performance — and have no current tool that does it.

**Core message:** Your SEO dashboard has a blind spot. AI is recommending vendors in your category right now — find out if it's you or your competitors.

**Differentiation vs. competitors (VisibleByAI, Visby, BeAIVisible):**
- They are dashboards, audits, or consultancy (£500–2,500+)
- We are a dead-simple weekly email for EUR 9–29/month
- No login required to get a free first result
- The hero metric is the **competitor gap** — not your score alone, but the delta between you and a named competitor

---

## What It Does

- **Free AI Visibility Check (lead magnet):** User enters brand name → we run 5 prompts against ChatGPT → returns instant score (e.g. "You appeared in 2/5 prompts") + competitor comparison — no login required
- Accepts a brand name, competitor names, and a set of buyer-intent prompts from a paying client
- Runs those prompts against configured AI engines on a weekly schedule
- Detects brand mentions in AI responses (binary yes/no + sentiment)
- Calculates **competitor gap** — how often competitors appear vs. the client brand
- Delivers a plain HTML email report every Monday: mention rate, competitor share of voice, week-on-week trend, which prompts are missing

---

## Project Structure

```
promptscore/
├── web/
│   ├── index.html              # Public landing page — deploy via Netlify
│   ├── robots.txt              # AI crawler permissions
│   └── sitemap.xml             # SEO sitemap
├── netlify.toml                # Netlify build config (publish = web/)
├── tally/
│   └── create_promptscore_forms.py  # Generates Tally.so onboarding forms
│                                      # See this file for form schema
├── n8n/
│   ├── workflow.json           # Weekly automation loop
│   ├── workflow_stripe_webhook.json  # Stripe → Airtable status sync
│   └── workflow_free_check.json       # Free visibility check lead magnet
├── templates/
│   └── report_email.html       # Resend-compatible HTML email report template
├── airtable/
│   └── schema.md               # Airtable base schema
├── scripts/
│   └── check_mentions.py       # Core prompt runner via OpenRouter (all engines)
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
└── README.md
```

---

## Tech Stack

| Layer | Tool | Cost |
|---|---|---|
| Landing page | `web/index.html` via Netlify | Free |
| Free visibility check (lead magnet) | Embedded form + n8n instant trigger | Free |
| Onboarding forms | Tally.so | Free |
| Client + results DB | Airtable | Free tier |
| Automation orchestration | n8n (cloud free or self-hosted on Railway) | Free |
| AI API — all engines | OpenRouter (`openrouter.ai`) — one key, all models | ~€0.05–0.15/client/week |
| Email delivery | Resend.com | Free (3,000 emails/month) |
| Payments | Stripe (payment link) | 1.4% + €0.25/tx |
| Domain | groundform.com (umbrella) | ~€11/year |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/alvee1994/promptscore.git
cd promptscore
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required variables:

```env
OPENROUTER_API_KEY=sk-or-your-openrouter-key   # openrouter.ai — single key, all engines
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
RESEND_API_KEY=
TALLY_API_KEY=
STRIPE_WEBHOOK_SECRET=
```

### 4. Deploy the landing page

The public landing page lives at `web/index.html`.

**Quickest option — Netlify Drop:**
1. Go to [netlify.com/drop](https://app.netlify.com/drop)
2. Drag and drop `web/index.html`
3. You get a live URL instantly (e.g. `random-name.netlify.app`)
4. Connect your custom domain in Netlify settings

**From repo — Netlify or Vercel:**
1. Connect your GitHub repo
2. Set the **publish directory** to `web`
3. Deploy — any push to `main` auto-deploys the landing page

### 5. Generate Tally forms

The onboarding form (brand name, competitor names, prompt set, email) is programmatically generated via:

```bash
python tally/create_promptscore_forms.py
```

See `tally/create_visara_forms.py` for form field definitions, question order, and Tally API configuration. Update `TALLY_API_KEY` in your `.env` before running.

### 6. Set up Airtable

Import the schema defined in `airtable/schema.md` into your Airtable base. The base has three tables:
- **Clients** — brand details, tier, status, contact email
- **Prompts** — linked to Clients; one row per tracked prompt
- **Results** — weekly mention data per prompt per client; includes competitor mention count for gap calculation

### 7. Import the n8n workflow

In your n8n instance:
1. Go to **Workflows → Import**
2. Upload each workflow from the `n8n/` directory:
   - `workflow.json` — weekly client run (cron every Monday 07:00)
   - `workflow_stripe_webhook.json` — Stripe → Airtable status sync (activate the webhook trigger)
   - `workflow_free_check.json` — free visibility check lead magnet (activate the webhook trigger)
3. In all workflows, update credentials to use:
   - **OpenRouter** (`OPENROUTER_API_KEY`) — single key for all AI engines
   - **Airtable** (`AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`)
   - **Resend** (`RESEND_API_KEY`)
4. For `workflow_free_check.json`: set the `N8N_FREE_CHECK_URL` env var to your n8n webhook URL, then inject that URL into `web/index.html` (`window.FREE_CHECK_URL`) so the landing page form calls it

---

## How the Weekly Loop Works

```
Every Monday 07:00 (Cron)
→ Fetch all active clients from Airtable
→ For each client: fetch their prompt list + competitor names
→ For each prompt: call OpenAI gpt-4o-mini + Perplexity API
→ Parse response: did brand appear? (yes/no) — sentiment (positive/neutral/negative)
→ Parse response: did each competitor appear? (yes/no)
→ Write results row to Airtable Results table
→ Calculate: mention rate, competitor gap (client % vs. competitor %), week-on-week delta
→ Render report_email.html with dynamic variables
→ Send via Resend to client email
```

---

## Free Visibility Check Flow (Lead Magnet)

```
Visitor enters brand name on landing page
→ n8n instant trigger
→ Run 5 default buyer-intent prompts against OpenAI only (gpt-4o-mini)
→ Return score: "You appeared in X/5 prompts"
→ Show top competitor mention count (if brand name allows inference)
→ Email gate: "Get the full 20-prompt report free" → Tally form
→ Tally → Airtable → manual follow-up for paid conversion
```

---

## Pricing Tiers

PromptPeek is intentionally **not** "just a prompt runner". Each tier includes features that normally require multiple AI visibility and LLM SEO tools combined.[web:558][web:566][web:260][web:565]

| Tier | Price | What you get (beyond raw prompts) |
|---|---|---|
| **Starter** | **€9 / month** | 10 tracked prompts/week across ChatGPT, weekly email report, basic competitor gap for 1 named competitor, English only, 90‑day history, internal dogfooding of all optimizations before they ship to higher tiers. |
| **Pro** | **€29 / month** | 50 prompts/week across ChatGPT + Perplexity + Gemini, up to 2 competitors, Dutch + English variants, trend charts (13‑week history), automatic prompt clustering by topic, source‑hints section suggesting what types of pages and third‑party listings to create next (inspired by leading LLM SEO tools).[web:559][web:563][web:565] |
| **Agency** | **€79 / month** | 200 prompts/week, up to 5 brands and 4 competitors each, all 3 engines, white‑label PDF + shareable link, per‑brand workspace, CSV export, priority report window (earlier in the Monday queue), and quarterly strategy call notes template to turn data into client‑facing recommendations.[web:566][web:564][web:567] |

All tiers include: basic sentiment tagging, hallucination flagging ("mentioned, but description looks wrong"), and an explicit AI visibility checklist so teams know what to change on site and off site — not just that a problem exists.[web:564][web:565][web:569]

---

## Onboarding a New Client (Manual, MVP Phase)

1. Client submits Tally form (generated by `tally/create_visara_forms.py`)
2. Tally → Airtable automation adds client row via Tally's native Airtable integration
3. Send Stripe payment link manually
4. Once payment confirmed, set client `status = active` in Airtable
5. Client is included in next Monday's automation run

---

## Service Flow

### 1. First Report Free (Anti-Abuse Guardrails)

PromptPeek follows a "first report free" model for new brands. To prevent abuse (bots, fake emails, unlimited retries), implement at least these safeguards:[web:543][web:547][web:551][web:555]

- **One free report per brand + email combination**: Airtable stores a unique constraint on `(brand_name, email)` so the same pair cannot trigger another free run without manual override.
- **Disposable-email blocking**: Use an email validation API (or a simple disposable-domain list) in the signup n8n/Tally step to reject burner inboxes before creating a record.[web:543][web:555]
- **Rate limiting by IP / device**: Store a hashed IP or device fingerprint in Airtable for each free report request and block obviously repeated attempts within a short window.[web:543][web:547]
- **Soft friction instead of hard walls**: If a user hits the limit, the UI offers "Talk to us for a custom audit" rather than silently failing, following best-practice guidance for reducing free-trial abuse while keeping high-intent leads.[web:555][web:551]

### 2. Normal Weekly Monitoring (Paid Plans)

1. User upgrades via Stripe Checkout (Starter/Pro/Agency).
2. Stripe emits `checkout.session.completed` and `customer.subscription.created` events.
3. n8n (or a no-code connector) listens to these webhooks and updates the corresponding Airtable **Clients** record with:
   - `plan` (starter/pro/agency)
   - `stripe_customer_id`
   - `stripe_subscription_id`
   - `status` (active/trialing/past_due/canceled).[web:545][web:552][web:553]
4. The weekly Cron workflow filters only `status in (active, trialing)`; canceled or past-due subscriptions are automatically excluded from runs.

### 3. Plan Changes and Cancellations

Stripe is the source of truth for billing. Airtable mirrors subscription state via automation:[web:545][web:548][web:552][web:553][web:556][web:557]

- **Upgrade / downgrade**: On `customer.subscription.updated`, n8n fetches the new price ID and updates the `plan` and `max_prompts` fields in Airtable for that client.
- **Cancellation**: On `customer.subscription.deleted` or `checkout.session.completed` with `mode=subscription` and `status=canceled`, Airtable `status` is set to `canceled`, and the weekly Cron job skips that client.
- **Dunning / past-due**: On `invoice.payment_failed` events, status is set to `past_due`; monitoring can be paused after a grace period while keeping historical data intact.

### 4. Internal Analytics and Fair Use

- A separate **Usage** table logs each run: client, prompts executed, tokens consumed, and engine mix.
- Basic anomaly checks (e.g., unusual volume spikes) flag potential abuse or misconfiguration for manual review, consistent with SaaS free-trial and abuse-prevention recommendations.[web:547][web:551][web:555]

---

## Competitive Landscape

| Competitor | Model | Price | Gap we fill |
|---|---|---|---|
| VisibleByAI | SEO consultancy + tools | £500–2,500 | Too expensive for SMEs |
| Visby | Full dashboard + integrations | Enterprise | Too complex, requires setup |
| BeAIVisible | Coaching/community | Subscription | Not a data product |
| SE Visible | Agency platform | $189/month | Not self-serve, no email-first |

**Our lane:** Self-serve, email-first, EUR 9–29/month, no dashboard required.

---

## Development Notes

- The mention detection in `scripts/check_mentions.py` uses a secondary `gpt-4o-mini` call to parse the raw AI response rather than simple string matching — handles brand name variations, abbreviations, and indirect references
- All API calls are wrapped in try/except with exponential backoff to handle rate limits
- Prompt variants (Dutch + English) are stored as separate rows in the Prompts table, linked to the same client
- Competitor gap is calculated as: `(competitor_mentions / total_prompts) - (client_mentions / total_prompts)` — positive = competitor is ahead

---

## Roadmap

- [x] Free AI visibility check (instant, no login) — lead magnet on landing page
- [ ] Airtable Interface for client self-service prompt management
- [x] Automated Stripe webhook → Airtable status update
- [ ] Gemini API integration (available via OpenRouter — enable via model select in workflow)
- [ ] White-label PDF export (Agency tier)
- [ ] Dashboard view (post-validation only)

---


## License

MIT
---

## AI Visibility for PromptPeek

This project will not recommend AI visibility tactics we do not follow ourselves. The live PromptPeek site is configured according to current LLM SEO / AI visibility best practices:

- **Crawlable for AI bots**: `robots.txt` explicitly allows GPTBot, OAI-SearchBot, ClaudeBot, Claude-SearchBot, PerplexityBot and Google-Extended so major LLMs can index our content.[web:531][web:536]
- **Structured, answer-first content**: The landing page and docs are written in clear Q&A style with sections that directly answer the kinds of questions AI systems summarize ("what is", "how to", "best tools for...").[web:528][web:534][web:536]
- **Schema markup**: Organization, Product, FAQ and Article schema are applied to core pages to clarify entities, offerings and relationships for retrieval-augmented generation systems.[web:529][web:530][web:538]
- **Authority seeding**: We actively pursue citations on high-trust domains and review sites (e.g., Reddit threads, LinkedIn posts, YouTube descriptions, and niche SaaS directories) because these sources strongly correlate with ChatGPT and Gemini recommendations.[web:529][web:532][web:538]
- **Comparison and alternative pages**: Content such as "PromptPeek vs. [Competitor]" and "Best AI visibility tools for SMEs" places PromptPeek alongside brands LLMs already know, improving inclusion in "alternatives to" queries.[web:529][web:531]
- **Freshness and updates**: Key pages include visible "last updated" dates and are revised as AI search behavior and best practices evolve; freshness is a direct ranking and citation signal for LLMs.[web:531][web:534]
- **Monitoring loop**: PromptPeek dogfoods its own monitoring workflows to track how often it appears in ChatGPT, Gemini and Perplexity answers. Gaps discovered in our own visibility drive the product roadmap and content updates.[web:531][web:532][web:541]

If PromptPeek cannot reliably appear in AI answers for queries it is built to serve, the product roadmap is adjusted before giving customers prescriptive advice.
