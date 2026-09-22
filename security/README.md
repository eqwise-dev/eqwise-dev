# security/

Beveiliging van AI-agenttoegang op de werkplek. Begonnen met de vraag: zorgen dat
de LLM niet overal bij kan.

| Bestand | Wat het is |
|---|---|
| [`llm-toegang-mac.md`](./llm-toegang-mac.md) | Het plan. Drie lagen, met de valkuilen per laag en een startpakket van 30 minuten. **Begin hier.** |
| [`claude-settings-user.json`](./claude-settings-user.json) | Kant-en-klaar sjabloon voor `~/.claude/settings.json`: deny-regels, ask-regels, sandbox. |
| [`check-llm-toegang.sh`](./check-llm-toegang.sh) | Read-only controle van de huidige situatie. Verandert niets. |

```bash
bash security/check-llm-toegang.sh     # nulmeting
cp security/claude-settings-user.json ~/.claude/settings.json
bash security/check-llm-toegang.sh     # verschil
```

Heb je al een `~/.claude/settings.json`? Voeg de blokken samen in plaats van
overschrijven — Claude Code voegt lijsten uit verschillende bestanden vanzelf
bij elkaar.

## Nog niet gedekt

Schijfversleuteling en wachtwoordbeheer staan als losse stap in het plan, maar
zijn niet uitgewerkt. Klantkant (toegangsbeheer op sites, logging,
incidentprocedure, verwerkersovereenkomst) evenmin.
