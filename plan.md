
## 1. AgentoAssistant Template

### UI Layout (Initial State)
- Large, centered rectangular prompt field.
- Icons in the prompt:
  - 📎 File Upload
  - 🔍 Web Search (Tavily)
  - ⬆️ Send Button

### Prompt Field Behavior
- On initial prompt submission:
  - The prompt box disappears.
  - A new prompt field appears at the bottom like a chat window.

### Web Search Icon Logic
- If web search icon is clicked:
  - `web_search_enabled = true`
  - Use **Tavily API** for response.
- If web search not enabled:
  - Use **Groq API** via **Langchain**.
  - Integrate **BufferMemory** to retain context.

### API Behavior
- API endpoints written in Django views.
- File uploads processed using Django’s `request.FILES`.
- No duplicate requests or messages should be generated.

---

## 2. Configuration Template

### Access
- Navigable from the navbar under `/config` route.

### MCP Tools with Icons and Options:
| Tool     | Action                        |
|----------|-------------------------------|
| Gmail    | Upload credentials (JSON file) |
| Drive    | Upload credentials (JSON file) |
| Bravo    | Input API Key                  |
| GitHub   | Input Personal Access Token    |

- Icons to be placed inside the `static/icons/` directory.
- Bootstrap grid system to layout tool cards with:
  - Icon
  - Label
  - Input (upload or text)
  - Save button

### Storage
- Files stored via Django's `MEDIA` folder.
- Tokens/keys optionally stored in a secure Django model.

---

## 3. Technical Stack

| Feature        | Stack                         |
|----------------|-------------------------------|
| UI             | HTML + CSS + JS + Bootstrap   |
| Backend        | Django Views & URLs           |
| LLM Integration| Groq + Langchain + BufferMemory |
| Search         | Tavily API                    |
| File Handling  | Django `FileField`            |
| API Calls      | JS Fetch / AJAX               |

---

## 4. Development Notes

- Start by analyzing working Flask code and isolate reusable functions.
- Convert those into Django services or views.
- Focus first on building the static UI templates (HTML + Bootstrap).
- Make sure API calls are handled via JS fetch with clean success/error handling.
- Ensure prompt re-rendering logic doesn’t create multiple input bars.

---

## 5. Next Steps

1. Convert Flask code into Django-compatible logic (views/services).
2. Build `agento.html` with prompt box UI and input behavior.
3. Build `config.html` with MCP cards and save actions.
4. Wire both templates to Django views and connect Tavily/Groq APIs.
5. Add file upload and token/key storage logic.

---

