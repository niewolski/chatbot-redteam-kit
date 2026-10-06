# Integracje zewnętrzne (własne systemy)

Ten katalog (`chatbot/`) to lekki agent red-team pod **Twój** lokalny bot na
`http://localhost:8080`. Poniżej — jak spiąć go z popularnymi narzędziami.

## garak (skaner podatności LLM)

```bash
pip install garak
garak --target_type rest.RestGenerator \
  --target_name pancake_bot \
  --target_uri http://localhost:8080/chat \
  --probes promptinject,encoding,dan \
  --generations 5
```

Dostosuj mapping body (`{"message": "..."}`) w konfiguracji REST garaka do API bota.

## PyRIT (Microsoft)

```bash
pip install pyrit
```

Użyj `PromptSendingOrchestrator` / `RedTeamingOrchestrator` z custom
`PromptTarget`, który POSTuje na `/chat` (jak `target_client.py`).
Attacker LLM = `GEMINI-MODEL-ATTACKER`, scoring = ten sam judge co w `judges.py`.

## promptfoo (CI)

```bash
cd chatbot/promptfoo
npm i -g promptfoo
promptfoo eval
promptfoo view
```

Konfig: `promptfoo/promptfooconfig.yaml`.

## HarmBench / podobne benchmarki

HarmBench jest pod treści szkodliwe ogólnego bezpieczeństwa. Tutaj scope jest
węższy: **ucieczka z domeny „tylko naleśniki”** + wyciek system promptu.
Promptów jailbreak możesz dalej brać z HF (`HF_DATASET`), a cel ataku
przepisywać modelem attacker (`adapt_prompt_for_pancake_bot`).

Przydatne datasety HF:
- `deepset/prompt-injections` (domyślny)
- `PointGuardAI/Prompt-Injection-OWASP-Benchmark-V2`
- `allenai/wildjailbreak` (większy, wolniejszy)

## OWASP LLM Top 10

```bash
python app.py --mode checklist
```

Priorytet w tym kicie: **LLM01 Prompt Injection** (+ powiązany leakage).
