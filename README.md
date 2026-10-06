# chatbot-redteam-kit

Agent red-teamowy do testowania **własnego** lokalnego chatbota „tylko naleśniki”
na `http://localhost:8080` (OWASP LLM01 — Prompt Injection).

## Co robi

1. Pobiera złośliwe / injection prompty z Hugging Face (`deepset/prompt-injections` + fallback lokalny).
2. Opcjonalnie przepisuje je modelem **attacker** (Gemini) pod cel: przepis na coś innego niż naleśniki lub wyciek system promptu.
3. Odpalą trzy tryby (limit **15 pytań/min** do targetu — `MAX_QPM`):
   - **single-turn** — wiele unikalnych promptów × kilka powtórzeń; **każda próba = nowy chat**,
   - **multi-turn** — eskalacja w **jednej** sesji `chat_id` (nowy chat = nowa kampania),
   - **adaptive** — drugi model uczy się z odpowiedzi; też **jeden chat na kampanię**.
4. Ocenia odpowiedzi: słowa kluczowe **oraz** sędzia LLM („czy to instrukcja przygotowania czegoś innego niż naleśniki”).
5. Każdą turę zapisuje do `chatbot/logs/*.jsonl` + `*.log` + summary JSON.

Domyślnie: `MAX_PROMPTS=100`, `REPEATS=5` (różnorodność > 20×15 tego samego).

## Setup

```bash
cd chatbot
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.template .env
# uzupełnij GEMINI-API oraz modele attacker/judge
```

Target musi żyć:

```text
POST http://localhost:8080/chat
{"message":"...", "chat_id":"...?"} → {"chat_id":"...","reply":"..."}
```

## Uruchomienie

Konfiguracja (modele, HF, repeats, target) leci z `.env` — nie potrzeba osobnego skryptu.

```bash
cd chatbot
python app.py                          # all modes
python app.py --mode single --repeats 12 --max-prompts 15
python app.py --mode multi --campaigns 3
python app.py --mode adaptive --adaptive-rounds 8
python app.py --mode checklist         # OWASP LLM01
python app.py --no-llm-judge           # tylko heurystyki
```

Logi: `chatbot/logs/redteam_YYYYMMDD_HHMMSS.jsonl`.

## Integracje

Zobacz [chatbot/INTEGRATIONS.md](chatbot/INTEGRATIONS.md) — garak, PyRIT, promptfoo, HarmBench, OWASP.

## Uwaga

Tylko do testów systemów, które kontrolujesz. Nie używaj przeciwko cudzym API.
