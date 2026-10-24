# Authorization & RBAC Guide

## 1. Multi-Tenancy Architecture

The platform implements **Strict Tenant Isolation**. All tenant boundaries are mathematically enforced across five distinct layers:

```
[Layer 1: Gateway]    Tenant extracted from verified JWT claims (org_id).
        |
[Layer 2: Database]   SQL WHERE organization_id = :org_id filter injected on every query.
        |
[Layer 3: Vector]     Qdrant collection payload filter: FieldCondition("organization_id", MatchValue(org_id)).
        |
[Layer 4: Storage]    Sandboxed filesystem paths: data/tenants/{org_id}/documents/{doc_id}.
        |
[Layer 5: Memory]     Tenant-scoped caches for model instances, BM25 indices, and session stores.
```

Cross-tenant data access is strictly impossible: even if an attacker guesses another tenant's document ID or knowledge base ID, the query filters mandate `organization_id == current_user.organization_id`, returning `404 Not Found`.

---

## 2. Role-Based Access Control (RBAC) Matrix

The system provides 9 pre-configured enterprise roles:

| Role Identifier | Description | Scope |
| :--- | :--- | :--- |
| `PLATFORM_OWNER` | Root platform administrator | Global system-wide |
| `SYSTEM_ADMIN` | Infrastructure, health, and gateway management | Global system-wide |
| `AI_ADMIN` | Model registry, ML training, evaluation metrics | Global / Tenant |
| `TENANT_ADMIN` | Organization owner, user management, quotas | Tenant-scoped |
| `KNOWLEDGE_MANAGER` | Knowledge base creation, document ingestion, indexing | Tenant-scoped |
| `ANALYST` | RAG queries, trace inspection, analytics reports | Tenant-scoped |
| `STANDARD_USER` | Voice & chat RAG interaction, document viewer | Tenant-scoped |
| `VOICE_ONLY_USER` | Microphone queries & TTS responses only | Tenant-scoped |
| `AUDITOR` | Read-only compliance and immutable audit logs | Tenant / Global |

---

## 3. Fine-Grained Permissions Matrix

| Permission | Platform Owner | System Admin | AI Admin | Tenant Admin | Knowledge Mgr | Analyst | Standard User | Voice User | Auditor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `system:manage` |  |  |  |  |  |  |  |  |  |
| `system:health` |  |  |  |  |  |  |  |  |  |
| `ml:train` |  |  |  |  |  |  |  |  |  |
| `ml:deploy` |  |  |  |  |  |  |  |  |  |
| `tenant:manage` |  |  |  |  |  |  |  |  |  |
| `tenant:users` |  |  |  |  |  |  |  |  |  |
| `kb:create` |  |  |  |  |  |  |  |  |  |
| `kb:delete` |  |  |  |  |  |  |  |  |  |
| `doc:upload` |  |  |  |  |  |  |  |  |  |
| `doc:delete` |  |  |  |  |  |  |  |  |  |
| `rag:query` |  |  |  |  |  |  |  |  |  |
| `voice:query` |  |  |  |  |  |  |  |  |  |
| `audit:read` |  |  |  |  |  |  |  |  |  |

---

## 4. Implementation & Enforcement

### 4.1 Dependency Injection in FastAPI
Endpoints declare authorization requirements using FastAPI's dependency injection system:

```python
from backend.app.security.rbac import require_role, require_permission

# Require specific role
@router.post("/training-runs")
async def trigger_training(
    current_user: User = Depends(require_role(["PLATFORM_OWNER", "AI_ADMIN"]))
):
    ...

# Require specific permission
@router.post("/documents/upload")
async def upload_document(
    current_user: User = Depends(require_permission("doc:upload"))
):
    ...
```

### 4.2 Superuser Bypass
`PLATFORM_OWNER` possesses wildcard permissions (`*`), allowing administrative oversight across tenant boundaries for platform recovery and system diagnostics.
