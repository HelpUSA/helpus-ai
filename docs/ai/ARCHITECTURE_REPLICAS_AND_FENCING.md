# Arquitetura de Réplicas, Fencing e Limite Operacional Multi-Worker

## 1. Contexto e Invariante de Concorrência
O backend do **HelpUS-AI** implementa controle estrito de concorrência e idempotência por turno (`turn_idempotency_key`), projetado para mitigar condições de corrida (TOCTOU), respostas duplicadas de assistente e corrupção de sessão.

Enquanto a coordenação de ciclo de vida (`claim_or_get_idempotent_request`, `release_idempotent_request` e heartbeat em memória) operar localmente no processo, a execução operacional está estritamente restrita a **exatamente 1 worker / 1 réplica operacional** (`MAX_OPERATIONAL_WORKERS = 1`).

## 2. Bloqueio no Startup (Fail-Closed)
O startup em `backend/main.py` e `api/main.py` inspeciona de forma independente as seguintes variáveis de ambiente:
- `WORKERS`
- `WEB_CONCURRENCY`
- `SERVER_REPLICAS`

Qualquer configuração diferente de 1 (seja menor que 1, como 0 ou números negativos, ou maior que 1) é **sumariamente rejeitada no startup com RuntimeError**:
```python
for var_name in ("WORKERS", "WEB_CONCURRENCY", "SERVER_REPLICAS"):
    raw_val = os.getenv(var_name)
    if raw_val is not None and str(raw_val).strip() != "":
        val = int(str(raw_val).strip())
        if val != 1:
            raise RuntimeError(f"Incompatibilidade operacional critica: {var_name}={val}...")
```

## 3. Limite de Múltiplas Réplicas Externas
Em orquestradores de contêineres (como Kubernetes, Docker Swarm ou Railway com autoscaling horizontal), a subida de múltiplas réplicas externas independentes é **terminantemente proibida** enquanto o fencing distribuído completo não for homologado.

### Razões Técnicas:
1. **Fencing em Memória Local**: Se uma requisição cliente for balanceada para a Réplica A e uma repetição for balanceada para a Réplica B, ambas poderiam iniciar inferência concorrente se não houver trava distribuída imediata.
2. **Lease e CAS no PostgreSQL**: A Migration 005 introduziu `turn_idempotency_ledger` com `owner_token`, `lease_seconds` e `SELECT ... FOR UPDATE` para prover atomicidade transacional e fencing relacional no PostgreSQL.
3. **Pré-requisito para Escala Horizontal**:
   - PostgreSQL centralizado de alta performance configurado com pool durável;
   - Todas as réplicas configuradas com `WORKERS=1` por processo;
   - Fencing distribuído via `claim_turn_ledger` exclusivamente gerenciado pelo PostgreSQL, com timeout de lease e heartbeat remoto ativo.

## 4. Política em Ambientes de Deploy (Produção e Staging)
- `HELPUS_TEST_MODE=1` é **terminantemente bloqueado** em ambientes de deploy (`VERCEL`, `RAILWAY_ENVIRONMENT`, `ENVIRONMENT=production/staging`).
- Em ambientes gerenciados, a ausência de pool PostgreSQL funcional resulta em parada total do serviço (fail-closed), protegendo a integridade dos dados e garantindo persistência estrita.
