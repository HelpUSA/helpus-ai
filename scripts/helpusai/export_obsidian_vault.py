from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from export_obsidian_operational_lessons import export_operational_lessons


DEFAULT_VAULT_DIR = Path("knowledge/obsidian/HelpUSAI")


@dataclass(frozen=True)
class ObsidianNote:
    filename: str
    title: str
    tags: tuple[str, ...]
    body: str

    def render(self) -> str:
        tag_lines = "\n".join(f"  - {tag}" for tag in self.tags)
        created = datetime.now(timezone.utc).date().isoformat()
        return (
            "---\n"
            f"title: {self.title}\n"
            "source: helpusai\n"
            "kind: obsidian_note\n"
            f"created: {created}\n"
            "tags:\n"
            f"{tag_lines}\n"
            "---\n\n"
            f"# {self.title}\n\n"
            f"{self.body.strip()}\n"
        )


def build_notes() -> list[ObsidianNote]:
    return [
        ObsidianNote(
            filename="Home.md",
            title="HelpUSAI Knowledge Home",
            tags=("helpusai", "index", "knowledge"),
            body="""
## Mapa principal

Este vault é a camada de conhecimento curado da HelpUSAI.

Links principais:

- [[Operational Lessons]]
- [[AI Bridge Local]]
- [[Watcher Protocol]]
- [[HelpUSAI Memory]]

## Objetivo

Organizar decisões, aprendizados, protocolos, erros recorrentes e próximos passos em Markdown local, versionado no Git e navegável pelo Obsidian.

## Regra operacional

A memória automática da HelpUSAI continua no banco e no runtime. Este vault é a camada humana/curada para revisão, auditoria e navegação.
""",
        ),
        ObsidianNote(
            filename="Operational Lessons.md",
            title="Operational Lessons",
            tags=("helpusai", "lessons", "operations"),
            body="""
## Conceito

Operational lessons são lições candidatas extraídas de erros, correções, smokes e uso real.

Fluxo recomendado:

1. evento operacional acontece;
2. HelpUSAI registra o problema;
3. HelpUSAI registra a correção;
4. a lição fica como candidate;
5. após validação, pode virar regra promovida.

## Lições iniciais

### AI Bridge Local inter-chat

Problema: a HelpUSAI confundiu protocolo de mensagem entre chats e misturou explicação com envelope.

Correção: para mensagem entre chats usar `send-chat-message`, `inter_agent_message`, `source_chat_id`, `target_chat_id`, `message` no topo do JSON, `payload_json` vazio e `no_reply` conforme necessário.

Evidência: o envio `send_helpusai_simple_supervisor_test_20260616_009` chegou ao chat da HelpUSAI e ela respondeu `RECEBIDO_HELPUSAI_SUPERVISOR_009` no chat destino.

### Envelope parse error

Problema: o watcher pode tentar interpretar explicações como JSON quando exemplos com marcadores reais aparecem no chat observado.

Correção: quando quiser executar, emitir somente o envelope puro. Quando quiser explicar, evitar marcadores reais e usar nomes substitutos.

### Composer preso

Problema: `submit_not_confirmed_composer_still_has_text` indica que o texto ficou no composer do chat destino.

Correção: abrir a aba destino, limpar ou enviar o texto preso, confirmar a extensão ativa e reenviar com `command_id` novo.
""",
        ),
        ObsidianNote(
            filename="AI Bridge Local.md",
            title="AI Bridge Local",
            tags=("helpusai", "ai_bridge_local", "watcher"),
            body="""
## Papel

AI Bridge Local é a ponte local que permite comunicação entre chats e execução de comandos locais controlados.

Na arquitetura atual:

- HelpUSAI é o cérebro operacional;
- AI Bridge Local é a ponte/executor;
- watcher/extensão observa chats;
- gateway local enfileira comandos;
- worker supervisor executa comandos locais quando aplicável.

## Usos principais

- enviar mensagens entre chats;
- executar comandos locais via `run-command`;
- retornar `AI_LOCAL`, `AI_LOCAL_RUN` ou `AI_LOCAL_ERRO`;
- permitir supervisão entre agentes.

## Diferença crítica

Mensagem entre chats não é comando local.

Mensagem entre chats usa `send-chat-message`.
Comando local usa `run-command`.
""",
        ),
        ObsidianNote(
            filename="Watcher Protocol.md",
            title="Watcher Protocol",
            tags=("helpusai", "watcher", "protocol"),
            body="""
## Mensagem entre chats

Usar quando um chat precisa falar com outro chat.

Campos essenciais:

- `version`
- `command_id`
- `action`: `send-chat-message`
- `type`: `send-chat-message`
- `delivery_kind`: `inter_agent_message`
- `source_chat_id`
- `target_chat_id`
- `conversation_id`
- `from_agent`
- `message`
- `payload_json`
- `no_reply`

## Comando local

Usar quando precisa executar algo no computador local.

Campos essenciais:

- `action`: `run-command`
- `type`: `run-command`
- `delivery_kind`: `local_capability`
- `target_chat_id`: `gateway-brain-supervisor`
- `payload.cwd`
- `payload.timeout_seconds`
- `payload.command` ou `payload.script_ext` e `payload.script_text`

## Regras

- `command_id` deve ser único.
- Não misturar explicação com envelope.
- Para explicações, evitar marcadores reais.
- Para execução, emitir somente envelope puro.
""",
        ),
        ObsidianNote(
            filename="HelpUSAI Memory.md",
            title="HelpUSAI Memory",
            tags=("helpusai", "memory", "learning"),
            body="""
## Camadas de memória

A HelpUSAI tem camadas diferentes:

1. memória de conversa;
2. contexto recuperado;
3. operational lessons;
4. contexto operacional injetado no chat;
5. vault Obsidian curado.

## Função do Obsidian

O Obsidian não substitui o banco da HelpUSAI.

Ele serve como:

- painel de conhecimento humano;
- documentação navegável;
- revisão de lessons;
- mapa de decisões;
- auditoria de aprendizado.

## Próximo passo futuro

Gerar notas automaticamente a partir de lessons reais gravadas no banco e permitir revisão/promote/reject.
""",
        ),
    ]


def export_vault(output_dir: Path = DEFAULT_VAULT_DIR) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for note in build_notes():
        path = output_dir / note.filename
        path.write_text(note.render().rstrip() + "\n", encoding="utf-8")
        written.append(path)

    return written


def main() -> None:
    written = export_vault()
    written.extend(export_operational_lessons())
    print("OBSIDIAN_VAULT_EXPORTED")
    for path in written:
        print(path.as_posix())


if __name__ == "__main__":
    main()
