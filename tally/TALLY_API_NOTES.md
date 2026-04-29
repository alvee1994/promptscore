# Tally API — Findings & Gotchas

Discovered through live iteration against `https://api.tally.so`.

---

## Block types

### `groupType` must match `type`
- `TITLE` blocks → `groupType: "TITLE"` (not `"TEXT"`)
- `HEADING_1/2/3` blocks → `groupType: "HEADING_1/2/3"` (not `"TEXT"`)
- `TEXT` blocks → `groupType: "TEXT"` ✅
- `INPUT_TEXT`, `INPUT_LINK`, `TEXTAREA`, etc. → `groupType` must equal `type`

### `STATEMENT` does not exist
Use `TEXT` instead.

### Dropdown / multiselect options
Each option block payload requires:
```json
{
  "index": 0,
  "isFirst": true,
  "isLast": false,
  "text": "Option label"
}
```
Missing any of these returns a 400.

### `HIDDEN_FIELDS` payload key
```json
"payload": { "hiddenFields": [...] }   ✅
"payload": { "fields": [...] }          ❌
```

### `minCharacters` is not a valid field
Sending it in an `INPUT_TEXT` payload returns a 400.

---

## HTTP

- `POST /forms` returns **201**, not 200. Accept both.
- Auth: `Authorization: Bearer <token>`

---

## Styling

Only these fields are safe in `settings.styles`:
```json
"styles": {
  "theme": "CUSTOM",
  "color": {
    "background": "#ffffff",
    "text": "#1a1a1a",
    "accent": "#6366f1",
    "buttonBackground": "#6366f1",
    "buttonText": "#ffffff"
  }
}
```

**These fields break the form renderer (forms show "Oops, something is off!"):**
- `font`
- `roundness`
- `width`
- `hasProgressBar` (top-level in settings)
- `showTallyBranding`
- `showProgressBar`

The API accepts them without error but the frontend crashes on render.
