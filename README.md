# Artemis
 Um Assistente virtual adaptada para a Versão da Artemis em Python

 Foco:
    Teste de ML na ferramenta adaptada

Técnologias:
    Reconhecimento de voz: (Google para reconhecimento online, Vosk para reconhecimento offline)
    Síntese de voz: (pyttsx3)
    Algum de tipo IA: Commands, NLU (classificação de texto)

## Apoio à decisão

Módulo que faz a Artemis atuar como uma segunda opinião estruturada sobre
decisões de projetos (ex.: Tyto Club, EngScan, LZ Informática): identifica
o projeto envolvido, puxa contexto salvo (estado, restrições, pessoas e
decisões anteriores), conversa por perguntas para esclarecer trade-offs e
registra a decisão final com a justificativa.

Estrutura:
- `core/llm/` — abstração de LLM (`LLMProvider`). Provedores prontos:
  `claude` (API da Anthropic), `local` (qualquer endpoint compatível com a
  API da OpenAI, ex.: Ollama rodando Llama) e `mock` (offline, usado em
  testes). Selecionado via `get_llm_provider()` / variável de ambiente
  `ARTEMIS_LLM_PROVIDER`.
- `core/memory/database.py` — banco SQLite local com projetos, restrições,
  pessoas envolvidas e histórico de decisões.
- `core/decision_support/` — motor da conversa (`DecisionSupportEngine`),
  agnóstico de LLM: troca de provedor não muda a lógica de raciocínio nem
  o acesso ao banco.

Para testar por texto:

```
python decision_support_cli.py
```

Variáveis de ambiente relevantes:
- `ARTEMIS_LLM_PROVIDER`: `mock` (padrão), `claude` ou `local`
- `ANTHROPIC_API_KEY`: necessária apenas com `ARTEMIS_LLM_PROVIDER=claude`
- `ARTEMIS_LLM_BASE_URL` / `ARTEMIS_LLM_MODEL`: usadas apenas com
  `ARTEMIS_LLM_PROVIDER=local`
