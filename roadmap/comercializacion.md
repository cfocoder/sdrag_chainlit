# Roadmap de Comercialización

**Objetivo**: Transformar SDRAG de proyecto de tesis a producto SaaS comercializable.

**Estado**: Planificación futura (post-tesis)

**Nota**: Este documento es independiente de la tesis. Las fases aquí descritas se implementarían después de completar la investigación académica.

---

## Visión del Producto

**SDRAG SaaS**: Plataforma de analítica financiera conversacional con IA que elimina alucinaciones aritméticas mediante arquitectura determinista.

**Propuesta de valor**:
- CFOs y equipos FP&A pueden consultar datos financieros en lenguaje natural
- Resultados 100% verificables (trazabilidad completa)
- Sin alucinaciones numéricas (capa semántica determinista)
- Documentos financieros indexados y consultables

**Mercado objetivo**:
- PyMEs con equipos de finanzas (5-50 empleados)
- Departamentos FP&A de empresas medianas
- Consultoras financieras

---

## Fase C1: Multi-tenancy y Aislamiento de Datos

**Objetivo**: Garantizar que los datos de cada cliente estén completamente aislados.

**Prioridad**: CRÍTICA - Fundamento de cualquier SaaS B2B con datos sensibles.

### Tarea C1.1: Modelo de Tenant

```python
# models/tenant.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Tenant:
    """Representa una organización/empresa cliente."""
    id: str  # UUID
    name: str
    slug: str  # URL-safe identifier (e.g., "acme-corp")
    plan: str  # "free", "pro", "enterprise"
    created_at: datetime
    settings: dict  # Configuraciones específicas del tenant

    # Límites según plan
    max_users: int
    max_documents: int
    max_queries_per_month: int

    # Estado
    is_active: bool = True
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


@dataclass
class TenantUser:
    """Usuario dentro de un tenant."""
    id: str
    tenant_id: str
    email: str
    role: str  # "owner", "admin", "analyst", "viewer"
    created_at: datetime
    last_login: Optional[datetime] = None
```

### Tarea C1.2: Aislamiento en Weaviate

```python
# services/weaviate_multitenant.py
import weaviate

def get_tenant_collection_name(tenant_id: str, collection_type: str = "Chunk") -> str:
    """Genera nombre de colección específico por tenant."""
    return f"Tenant_{tenant_id}_{collection_type}"

async def create_tenant_collections(client: weaviate.Client, tenant_id: str):
    """Crea colecciones aisladas para un nuevo tenant."""
    collections = ["Document", "Chunk"]
    for coll_type in collections:
        collection_name = get_tenant_collection_name(tenant_id, coll_type)
        if not client.collections.exists(collection_name):
            client.collections.create(name=collection_name, **COLLECTION_CONFIGS[coll_type])

async def hybrid_search_tenant(
    client: weaviate.Client,
    tenant_id: str,
    query_text: str,
    query_embedding: list[float],
    top_k: int = 5
) -> list[dict]:
    """Búsqueda híbrida aislada por tenant."""
    collection_name = get_tenant_collection_name(tenant_id, "Chunk")
    collection = client.collections.get(collection_name)
    results = collection.query.hybrid(query=query_text, vector=query_embedding, limit=top_k)
    return [obj.properties for obj in results.objects]
```

### Tarea C1.3: Middleware de Tenant

```python
# middleware/tenant.py
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    """Inyecta tenant_id en cada request."""

    async def dispatch(self, request, call_next):
        # Extraer tenant del JWT o subdomain
        tenant_id = await self.resolve_tenant(request)

        if not tenant_id:
            return JSONResponse({"error": "Tenant not found"}, status_code=404)

        # Verificar tenant activo y con suscripción válida
        tenant = await get_tenant(tenant_id)
        if not tenant.is_active:
            return JSONResponse({"error": "Account suspended"}, status_code=403)

        # Inyectar en request state
        request.state.tenant_id = tenant_id
        request.state.tenant = tenant

        return await call_next(request)
```

### Criterios de aceptación C1
- [ ] Modelo de Tenant y TenantUser definido
- [ ] Índices Weaviate separados por tenant
- [ ] Middleware inyecta tenant_id en cada request
- [ ] Imposible acceder a datos de otro tenant
- [ ] Tests de aislamiento pasan

---

## Fase C2: Autenticación Empresarial

**Objetivo**: Reemplazar autenticación básica por sistema robusto con OAuth/SSO.

### Tarea C2.1: Integrar Auth Provider

**Opciones recomendadas**:
1. **Clerk** - Más simple, buena integración
2. **Auth0** - Enterprise-ready, más complejo
3. **Supabase Auth** - Open source, self-hosted posible

```python
# auth/clerk_provider.py (ejemplo con Clerk)
from clerk_backend_api import Clerk
import os

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

async def verify_session(session_token: str) -> dict:
    """Verifica sesión y retorna usuario."""
    try:
        session = clerk.sessions.verify(session_token)
        return {
            "user_id": session.user_id,
            "email": session.user.email_addresses[0].email,
            "tenant_id": session.user.public_metadata.get("tenant_id")
        }
    except Exception:
        raise AuthenticationError("Invalid session")

async def get_user_permissions(user_id: str, tenant_id: str) -> list:
    """Obtiene permisos del usuario en el tenant."""
    user = await get_tenant_user(user_id, tenant_id)
    return ROLE_PERMISSIONS.get(user.role, [])
```

### Tarea C2.2: OAuth Providers

```python
# Configurar en Clerk/Auth0:
OAUTH_PROVIDERS = [
    "google",      # Google Workspace
    "microsoft",   # Microsoft 365 / Azure AD
    "github",      # Para desarrolladores
]

# SSO Enterprise (SAML)
# Disponible en plan Enterprise para clientes grandes
```

### Tarea C2.3: RBAC (Role-Based Access Control)

```python
# auth/permissions.py

ROLES = {
    "owner": {
        "description": "Dueño de la cuenta",
        "permissions": ["*"]  # Todo
    },
    "admin": {
        "description": "Administrador",
        "permissions": [
            "users:read", "users:write",
            "documents:*",
            "queries:*",
            "settings:read", "settings:write",
            "billing:read"
        ]
    },
    "analyst": {
        "description": "Analista FP&A",
        "permissions": [
            "documents:read", "documents:upload",
            "queries:*"
        ]
    },
    "viewer": {
        "description": "Solo lectura",
        "permissions": [
            "documents:read",
            "queries:read"
        ]
    }
}

def check_permission(user_role: str, required_permission: str) -> bool:
    """Verifica si el rol tiene el permiso requerido."""
    permissions = ROLES.get(user_role, {}).get("permissions", [])
    if "*" in permissions:
        return True
    if required_permission in permissions:
        return True
    # Verificar wildcards (e.g., "documents:*" incluye "documents:read")
    base = required_permission.split(":")[0]
    return f"{base}:*" in permissions
```

### Criterios de aceptación C2
- [ ] OAuth con Google y Microsoft funciona
- [ ] Usuarios pueden invitar a su equipo
- [ ] RBAC implementado (owner, admin, analyst, viewer)
- [ ] SSO disponible para Enterprise
- [ ] Sesiones seguras con refresh tokens

---

## Fase C3: Integración Stripe

**Objetivo**: Monetizar con suscripciones y billing basado en uso.

### Tarea C3.1: Planes de Suscripción

```python
# billing/plans.py

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "stripe_price_id": None,
        "limits": {
            "users": 1,
            "documents": 10,
            "queries_per_month": 100,
            "storage_mb": 100
        },
        "features": [
            "1 usuario",
            "10 documentos",
            "100 consultas/mes",
            "Soporte por email"
        ]
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 49,  # USD
        "stripe_price_id": "price_xxx_pro_monthly",
        "limits": {
            "users": 5,
            "documents": 500,
            "queries_per_month": 5000,
            "storage_mb": 5000
        },
        "features": [
            "Hasta 5 usuarios",
            "500 documentos",
            "5,000 consultas/mes",
            "5 GB almacenamiento",
            "Soporte prioritario",
            "API access"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": "custom",
        "stripe_price_id": None,  # Cotización personalizada
        "limits": {
            "users": -1,  # Ilimitado
            "documents": -1,
            "queries_per_month": -1,
            "storage_mb": -1
        },
        "features": [
            "Usuarios ilimitados",
            "Documentos ilimitados",
            "SSO / SAML",
            "SLA garantizado",
            "Soporte dedicado",
            "On-premise disponible"
        ]
    }
}
```

### Tarea C3.2: Cliente Stripe

```python
# billing/stripe_client.py
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def create_customer(tenant: Tenant, email: str) -> str:
    """Crea customer en Stripe para el tenant."""
    customer = stripe.Customer.create(
        email=email,
        name=tenant.name,
        metadata={
            "tenant_id": tenant.id,
            "tenant_slug": tenant.slug
        }
    )
    return customer.id

async def create_subscription(
    customer_id: str,
    price_id: str,
    trial_days: int = 14
) -> dict:
    """Crea suscripción con período de prueba."""
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        trial_period_days=trial_days,
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"]
    )
    return {
        "subscription_id": subscription.id,
        "client_secret": subscription.latest_invoice.payment_intent.client_secret,
        "status": subscription.status
    }

async def create_checkout_session(
    tenant_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str
) -> str:
    """Crea sesión de Stripe Checkout."""
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tenant_id": tenant_id}
    )
    return session.url

async def create_billing_portal_session(customer_id: str, return_url: str) -> str:
    """Crea sesión del portal de billing para el cliente."""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url
    )
    return session.url
```

### Tarea C3.3: Webhooks de Stripe

```python
# billing/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import stripe

router = APIRouter()

@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    """Procesa eventos de Stripe."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Manejar eventos
    if event.type == "checkout.session.completed":
        await handle_checkout_completed(event.data.object)

    elif event.type == "customer.subscription.updated":
        await handle_subscription_updated(event.data.object)

    elif event.type == "customer.subscription.deleted":
        await handle_subscription_cancelled(event.data.object)

    elif event.type == "invoice.payment_failed":
        await handle_payment_failed(event.data.object)

    return {"status": "ok"}

async def handle_checkout_completed(session):
    """Activa suscripción después de pago exitoso."""
    tenant_id = session.metadata.get("tenant_id")
    subscription_id = session.subscription
    customer_id = session.customer

    # Actualizar tenant con IDs de Stripe
    await update_tenant(tenant_id, {
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "plan": "pro",  # O detectar del price_id
        "is_active": True
    })

    # Aplicar nuevos límites
    await apply_plan_limits(tenant_id, "pro")

async def handle_subscription_cancelled(subscription):
    """Degrada a plan free cuando se cancela."""
    customer_id = subscription.customer
    tenant = await get_tenant_by_stripe_customer(customer_id)

    await update_tenant(tenant.id, {
        "plan": "free",
        "stripe_subscription_id": None
    })
    await apply_plan_limits(tenant.id, "free")
```

### Tarea C3.4: Tracking de Uso

```python
# billing/usage.py
from datetime import datetime, timedelta

async def track_usage(tenant_id: str, metric: str, count: int = 1):
    """Registra uso de recursos."""
    await redis.hincrby(f"usage:{tenant_id}:{current_month()}", metric, count)

async def get_usage(tenant_id: str) -> dict:
    """Obtiene uso del mes actual."""
    key = f"usage:{tenant_id}:{current_month()}"
    usage = await redis.hgetall(key)
    return {
        "queries": int(usage.get("queries", 0)),
        "documents": int(usage.get("documents", 0)),
        "storage_mb": int(usage.get("storage_mb", 0))
    }

async def check_limit(tenant_id: str, metric: str) -> bool:
    """Verifica si el tenant puede realizar la acción."""
    tenant = await get_tenant(tenant_id)
    plan = PLANS[tenant.plan]
    limit = plan["limits"].get(metric, 0)

    if limit == -1:  # Ilimitado
        return True

    usage = await get_usage(tenant_id)
    current = usage.get(metric, 0)

    return current < limit

# Usar en endpoints
@router.post("/query")
async def execute_query(request: Request, query: QueryInput):
    tenant_id = request.state.tenant_id

    if not await check_limit(tenant_id, "queries_per_month"):
        raise HTTPException(429, "Monthly query limit reached. Upgrade your plan.")

    # Ejecutar query...
    await track_usage(tenant_id, "queries")
```

### Criterios de aceptación C3
- [ ] Checkout con Stripe funciona
- [ ] Webhooks procesan eventos correctamente
- [ ] Portal de billing accesible para clientes
- [ ] Tracking de uso por tenant
- [ ] Límites se aplican según plan
- [ ] Downgrade automático al cancelar

---

## Fase C4: Compliance y Seguridad

**Objetivo**: Preparar para manejar datos financieros sensibles de empresas.

### Tarea C4.1: Audit Logs

```python
# audit/logger.py
from datetime import datetime
import json

async def log_audit_event(
    tenant_id: str,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict = None,
    ip_address: str = None
):
    """Registra evento de auditoría inmutable."""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "action": action,  # "query", "upload", "delete", "login", "settings_change"
        "resource_type": resource_type,  # "document", "query", "user", "settings"
        "resource_id": resource_id,
        "details": details,
        "ip_address": ip_address,
        "user_agent": None  # Del request
    }

    # Indexar en Weaviate (índice de audit del tenant)
    index_name = get_tenant_index_name(tenant_id, "audit")
    await client.index(index=index_name, body=event)

    return event

# Ejemplos de uso
await log_audit_event(
    tenant_id=tenant_id,
    user_id=user_id,
    action="query",
    resource_type="query",
    resource_id=query_id,
    details={"query_text": query, "result_count": len(results)}
)

await log_audit_event(
    tenant_id=tenant_id,
    user_id=user_id,
    action="upload",
    resource_type="document",
    resource_id=doc_id,
    details={"filename": filename, "size_bytes": size}
)
```

### Tarea C4.2: Encriptación

```python
# security/encryption.py
from cryptography.fernet import Fernet
import os

# Cada tenant tiene su propia key (almacenada en vault seguro)
def get_tenant_encryption_key(tenant_id: str) -> bytes:
    """Obtiene key de encriptación del tenant desde vault."""
    # En producción: AWS KMS, HashiCorp Vault, etc.
    return vault.get_secret(f"tenant/{tenant_id}/encryption_key")

def encrypt_sensitive_field(tenant_id: str, plaintext: str) -> str:
    """Encripta campo sensible."""
    key = get_tenant_encryption_key(tenant_id)
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()

def decrypt_sensitive_field(tenant_id: str, ciphertext: str) -> str:
    """Desencripta campo sensible."""
    key = get_tenant_encryption_key(tenant_id)
    f = Fernet(key)
    return f.decrypt(ciphertext.encode()).decode()
```

### Tarea C4.3: Data Retention Policies

```python
# compliance/retention.py

RETENTION_POLICIES = {
    "free": {
        "documents_days": 90,
        "queries_days": 30,
        "audit_days": 30
    },
    "pro": {
        "documents_days": 365,
        "queries_days": 180,
        "audit_days": 365
    },
    "enterprise": {
        "documents_days": -1,  # Configurable
        "queries_days": -1,
        "audit_days": 2555  # 7 años (compliance financiero)
    }
}

async def cleanup_expired_data(tenant_id: str):
    """Elimina datos que exceden política de retención."""
    tenant = await get_tenant(tenant_id)
    policy = RETENTION_POLICIES[tenant.plan]

    for index_type, days in policy.items():
        if days == -1:
            continue

        index_name = get_tenant_index_name(tenant_id, index_type.replace("_days", ""))
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Eliminar documentos antiguos
        await client.delete_by_query(
            index=index_name,
            body={
                "query": {
                    "range": {
                        "created_at": {"lt": cutoff.isoformat()}
                    }
                }
            }
        )
```

### Tarea C4.4: Preparación SOC 2

Checklist para SOC 2 Type II:

- [ ] **Control de acceso**: RBAC implementado, MFA disponible
- [ ] **Logs de auditoría**: Inmutables, retenidos 7 años
- [ ] **Encriptación**: At-rest y in-transit
- [ ] **Backups**: Automatizados, probados regularmente
- [ ] **Incident response**: Procedimiento documentado
- [ ] **Vendor management**: Proveedores evaluados (Stripe, Auth provider)
- [ ] **Change management**: CI/CD con aprobaciones
- [ ] **Vulnerability management**: Escaneo regular de dependencias

### Criterios de aceptación C4
- [ ] Audit logs inmutables implementados
- [ ] Encriptación at-rest para datos sensibles
- [ ] Políticas de retención aplicadas
- [ ] Checklist SOC 2 documentado
- [ ] HTTPS obligatorio en producción

---

## Fase C5: Infraestructura Escalable

**Objetivo**: Migrar de cluster Tailscale a infraestructura cloud escalable.

### Tarea C5.1: Containerización Completa

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  chainlit:
    image: sdrag/chainlit:${VERSION}
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - WEAVIATE_URL=${WEAVIATE_URL}

  worker:
    image: sdrag/worker:${VERSION}
    deploy:
      replicas: 2
    command: celery -A tasks worker -Q documents,embeddings

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # Weaviate manejado por servicio cloud (AWS Weaviate, Elastic Cloud)
```

### Tarea C5.2: Queue para Procesamiento

```python
# tasks/document_processing.py
from celery import Celery

celery = Celery('sdrag', broker=os.getenv('REDIS_URL'))

@celery.task(bind=True, max_retries=3)
def process_document(self, tenant_id: str, document_id: str, file_path: str):
    """Procesa documento en background."""
    try:
        # 1. Extraer con Docling
        content = extract_document_sync(file_path)

        # 2. Crear chunks
        chunks = create_semantic_chunks(content["text"], content["tables"], {})

        # 3. Generar embeddings
        embeddings = generate_embeddings_batch_sync([c["text"] for c in chunks])

        # 4. Indexar en Weaviate del tenant
        index_name = get_tenant_index_name(tenant_id, "documents")
        index_chunks(chunks, embeddings, index_name)

        # 5. Actualizar estado
        update_document_status(document_id, "indexed")

        # 6. Track usage
        track_usage_sync(tenant_id, "documents", 1)

    except Exception as e:
        self.retry(exc=e, countdown=60)
```

### Tarea C5.3: Rate Limiting

```python
# middleware/rate_limit.py
from fastapi import Request, HTTPException
import redis.asyncio as redis

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting por tenant y tier."""
    tenant = request.state.tenant

    # Límites por minuto según plan
    limits = {
        "free": 10,
        "pro": 100,
        "enterprise": 1000
    }

    limit = limits.get(tenant.plan, 10)
    key = f"ratelimit:{tenant.id}:{current_minute()}"

    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, 60)

    if current > limit:
        raise HTTPException(429, "Rate limit exceeded")

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current))

    return response
```

### Tarea C5.4: Opciones de Deployment

| Opción | Pros | Contras | Costo estimado |
|--------|------|---------|----------------|
| **Railway/Render** | Simple, rápido | Menos control | $50-200/mes |
| **DigitalOcean App Platform** | Buen balance | Limitado para enterprise | $100-500/mes |
| **AWS ECS/Fargate** | Escalable, enterprise-ready | Complejo | $300-1000/mes |
| **Kubernetes (EKS/GKE)** | Máximo control | Requiere expertise | $500-2000/mes |

### Criterios de aceptación C5
- [ ] Docker Compose para producción
- [ ] Workers con Celery/Redis
- [ ] Rate limiting por tenant
- [ ] Auto-scaling configurado
- [ ] Monitoring (Datadog/Grafana)

---

## Fase C6: Onboarding y Self-Service

**Objetivo**: Permitir que clientes se registren y empiecen a usar sin intervención.

### Tarea C6.1: Flujo de Registro

```
1. Usuario llega a landing page
2. Click "Start Free Trial"
3. OAuth con Google/Microsoft
4. Crear tenant automáticamente
5. Onboarding wizard (nombre empresa, sector, etc.)
6. Subir primer documento
7. Primera consulta guiada
8. Invitar equipo (opcional)
```

### Tarea C6.2: Onboarding Wizard

```python
# Pasos del wizard
ONBOARDING_STEPS = [
    {
        "id": "company_info",
        "title": "Cuéntanos sobre tu empresa",
        "fields": ["company_name", "industry", "team_size"]
    },
    {
        "id": "first_document",
        "title": "Sube tu primer documento",
        "description": "Un P&L, Balance o reporte financiero",
        "action": "upload"
    },
    {
        "id": "first_query",
        "title": "Haz tu primera pregunta",
        "examples": [
            "¿Cuál fue el revenue del último trimestre?",
            "¿Cuánto gastamos en marketing?"
        ],
        "action": "query"
    },
    {
        "id": "invite_team",
        "title": "Invita a tu equipo",
        "optional": True,
        "action": "invite"
    }
]
```

### Tarea C6.3: Portal de Cliente

Páginas necesarias:
- `/dashboard` - Overview de uso y métricas
- `/documents` - Gestión de documentos
- `/team` - Gestión de usuarios
- `/settings` - Configuración del workspace
- `/billing` - Suscripción y facturas (Stripe Portal)

### Criterios de aceptación C6
- [ ] Registro self-service funciona
- [ ] Onboarding wizard completo
- [ ] Dashboard con métricas de uso
- [ ] Portal de billing integrado
- [ ] Invitación de team members

---

## Roadmap de Lanzamiento

### MVP (3-4 meses post-tesis)
- [ ] C1: Multi-tenancy básico
- [ ] C2: Auth con Google/Microsoft
- [ ] C3: Stripe básico (Free + Pro)
- [ ] Landing page + registro
- [ ] 10 beta testers

### v1.0 (6-8 meses post-tesis)
- [ ] C4: Audit logs
- [ ] C5: Infraestructura escalable
- [ ] C6: Onboarding completo
- [ ] Documentación para usuarios
- [ ] Lanzamiento público

### v2.0 (12+ meses post-tesis)
- [ ] Enterprise features (SSO, SLA)
- [ ] API pública para integraciones
- [ ] Marketplace de conectores
- [ ] SOC 2 certificación

---

## Métricas de Negocio

| Métrica | Objetivo MVP | Objetivo v1.0 |
|---------|--------------|---------------|
| **MRR** | $500 | $5,000 |
| **Clientes pagos** | 10 | 50 |
| **Churn mensual** | <10% | <5% |
| **CAC** | <$100 | <$200 |
| **LTV** | >$500 | >$1,000 |
| **NPS** | >30 | >50 |

---

## Costos Estimados Mensuales

### MVP (~$200-400/mes)
- Hosting (Railway/Render): $50-100
- Weaviate (Elastic Cloud starter): $95
- Auth (Clerk free tier): $0
- Stripe: 2.9% + $0.30 por transacción
- Dominio + SSL: $20

### Escala ($1,000-3,000/mes)
- Hosting (DigitalOcean/AWS): $300-800
- Weaviate cluster: $300-500
- Redis: $50-100
- Monitoring: $50-100
- Auth (Clerk Pro): $25-100
- Backups: $50-100

---

## Notas Finales

Este roadmap es **post-tesis**. El enfoque actual debe ser:

1. **Completar la investigación académica** (Fases 1-8 del ROADMAP principal)
2. **Publicar resultados** (paper, defensa de tesis)
3. **Evaluar viabilidad comercial** basada en los resultados

La arquitectura actual (determinista, trazable, sin alucinaciones) es un diferenciador fuerte en el mercado de herramientas FP&A con IA.
