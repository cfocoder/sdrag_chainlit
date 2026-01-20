# Fase 7: Audit Trail y Exportación

**Objetivo**: Implementar exportación de sesiones y trazabilidad completa para auditoría financiera.

**Prioridad**: Media - Importante para compliance y reproducibilidad, pero no crítico para validación experimental.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 2: cl.Step implementado (trazabilidad base)
- [x] Fase 6: Visualización (para incluir en exports)

### Dependencias
```bash
uv add pydantic reportlab  # Para JSON schema y PDF generation
```

---

## Contexto

### ¿Por qué Audit Trail es Importante?

En sistemas FP&A, la **trazabilidad completa** es esencial para:

1. **Compliance financiero**: Auditorías SOX, IFRS requieren evidencia de cálculos
2. **Reproducibilidad**: Misma pregunta debe generar misma respuesta numérica
3. **Debugging**: Identificar errores en clasificación, SQL o datos
4. **Governance**: Registro de quién consultó qué y cuándo

### Estructura de Sesión Auditable

```json
{
  "session_id": "uuid-12345678",
  "user_id": "hector@sanchezmx.com",
  "timestamp": "2026-01-20T10:30:00Z",
  "query": "¿Cuál fue el revenue de Q4 2024?",
  "steps": [
    {
      "step_name": "Clasificación",
      "input": "¿Cuál fue el revenue de Q4 2024?",
      "output": "Ruta: semantic, Métrica: revenue",
      "duration_ms": 150
    },
    {
      "step_name": "SQL",
      "input": "Generar SQL para revenue Q4 2024",
      "output": "SELECT SUM(revenue) FROM facts WHERE quarter='Q4' AND year=2024",
      "duration_ms": 50
    },
    {
      "step_name": "Datos",
      "input": "Ejecutar SQL en Cube Core",
      "output": {"revenue": 1234567, "period": "Q4_2024"},
      "duration_ms": 320
    },
    {
      "step_name": "Explicación",
      "input": "Generar explicación con Dify",
      "output": "El revenue de Q4 2024 fue de $1,234,567...",
      "duration_ms": 1200,
      "source": "dify"
    }
  ],
  "total_duration_ms": 1720,
  "result": {
    "answer": "El revenue de Q4 2024 fue de $1,234,567...",
    "data": {"revenue": 1234567},
    "sql": "SELECT SUM(revenue) FROM facts WHERE quarter='Q4' AND year=2024"
  }
}
```

---

## Tarea 7.1: Exportar Sesión a JSON

### Descripción
Capturar todos los pasos de ejecución en un JSON estructurado.

### Archivo a crear
`services/audit_trail.py`

### Código de referencia

```python
"""Audit Trail - Exportación de sesiones para compliance."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from pathlib import Path


class StepTrace(BaseModel):
    """Traza de un paso de ejecución."""
    step_name: str
    step_type: str  # "tool", "llm", "retrieval"
    input: str
    output: str
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = {}


class SessionTrace(BaseModel):
    """Traza completa de una sesión."""
    session_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    query: str
    steps: List[StepTrace] = []
    total_duration_ms: float = 0
    result: Dict[str, Any] = {}
    classification: Optional[Dict[str, str]] = {}
    error: Optional[str] = None


class AuditTrailManager:
    """Gestor de audit trail."""
    
    def __init__(self, storage_path: str = "./audit_trails"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[SessionTrace] = None
    
    def start_session(self, session_id: str, user_id: str, query: str) -> SessionTrace:
        """Inicia nueva sesión."""
        self.current_session = SessionTrace(
            session_id=session_id,
            user_id=user_id,
            query=query
        )
        return self.current_session
    
    def add_step(
        self,
        step_name: str,
        step_type: str,
        input_data: str,
        output_data: str,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ):
        """Agrega paso a la sesión actual."""
        if not self.current_session:
            raise ValueError("No hay sesión activa")
        
        step = StepTrace(
            step_name=step_name,
            step_type=step_type,
            input=input_data,
            output=output_data,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.current_session.steps.append(step)
    
    def finalize_session(
        self,
        result: Dict[str, Any],
        total_duration_ms: float,
        classification: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> SessionTrace:
        """Finaliza sesión y calcula totales."""
        if not self.current_session:
            raise ValueError("No hay sesión activa")
        
        self.current_session.result = result
        self.current_session.total_duration_ms = total_duration_ms
        self.current_session.classification = classification
        self.current_session.error = error
        
        return self.current_session
    
    def save_session(self, session: SessionTrace) -> str:
        """Guarda sesión a archivo JSON."""
        # Formato: audit_trail_YYYYMMDD_sessionid.json
        date_str = session.timestamp.strftime("%Y%m%d")
        filename = f"audit_trail_{date_str}_{session.session_id[:8]}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, indent=2, default=str)
        
        return str(filepath)
    
    def load_session(self, session_id: str) -> Optional[SessionTrace]:
        """Carga sesión desde archivo."""
        # Buscar archivo por session_id
        for filepath in self.storage_path.glob(f"audit_trail_*_{session_id[:8]}.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SessionTrace(**data)
        return None


# Instancia global
audit_manager = AuditTrailManager()
```

### Integración en app.py

```python
import uuid
from services.audit_trail import audit_manager

@cl.on_message
async def main(message: cl.Message):
    query = message.content
    session_id = str(uuid.uuid4())
    user_id = cl.user_session.get("user").identifier
    
    # Iniciar sesión de audit
    session = audit_manager.start_session(session_id, user_id, query)
    
    start_time = time.time()
    
    # Paso 1: Clasificación
    async with cl.Step(name="Clasificación", type="tool") as step:
        step_start = time.time()
        classification = classify_query(query)
        step_duration = (time.time() - step_start) * 1000
        
        # Registrar en audit trail
        audit_manager.add_step(
            step_name="Clasificación",
            step_type="tool",
            input_data=query,
            output_data=str(classification),
            duration_ms=step_duration
        )
        
        step.output = f"Ruta: {classification['route']}"
    
    # ... más pasos con audit_manager.add_step() en cada uno
    
    # Finalizar sesión
    total_duration = (time.time() - start_time) * 1000
    session = audit_manager.finalize_session(
        result={"answer": explanation, "data": data},
        total_duration_ms=total_duration,
        classification=classification
    )
    
    # Guardar a disco
    filepath = audit_manager.save_session(session)
    
    # Mostrar en UI (opcional)
    await cl.Message(
        content=f"{explanation}\n\n---\n*Sesión guardada: {session_id[:8]}*"
    ).send()
```

### ✅ Criterios de Completitud

**Testing:**
```bash
pytest tests/test_audit_trail.py::test_session_export -v
```

**Tests específicos:**
- [ ] SessionTrace se serializa a JSON válido
- [ ] Todos los pasos registrados
- [ ] Timestamps correctos
- [ ] Archivo guardado en ./audit_trails/

**Verificación manual:**
```bash
chainlit run app.py
# Hacer consulta
# Verificar archivo creado:
ls -lh audit_trails/
cat audit_trails/audit_trail_20260120_*.json | jq .
```

**Integridad de datos:**
- [ ] session_id único por consulta
- [ ] Durations suman al total
- [ ] No hay pasos duplicados

---

## Tarea 7.2: Exportar Sesión a PDF

### Descripción
Generar reporte PDF profesional de la sesión para auditoría.

### Dependencias
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
```

### Código de referencia

```python
"""Exportación de audit trail a PDF."""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from typing import List
from datetime import datetime
import json


def generate_audit_pdf(session: SessionTrace, output_path: str):
    """
    Genera PDF de reporte de auditoría.
    
    Args:
        session: SessionTrace con datos de la sesión
        output_path: Ruta del archivo PDF a crear
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30
    )
    story.append(Paragraph("SDRAG Audit Trail Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata de sesión
    session_data = [
        ["Session ID", session.session_id],
        ["Usuario", session.user_id],
        ["Timestamp", session.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["Consulta", session.query],
        ["Duración Total", f"{session.total_duration_ms:.0f} ms"],
        ["Clasificación", session.classification.get('route', 'N/A') if session.classification else 'N/A']
    ]
    
    session_table = Table(session_data, colWidths=[2*inch, 4.5*inch])
    session_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(session_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Pasos de ejecución
    story.append(Paragraph("Pasos de Ejecución", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    for i, step in enumerate(session.steps, 1):
        # Header de paso
        step_header = f"{i}. {step.step_name} ({step.step_type}) - {step.duration_ms:.0f}ms"
        story.append(Paragraph(step_header, styles['Heading3']))
        
        # Tabla de input/output
        step_data = [
            ["Input", step.input[:200] + "..." if len(step.input) > 200 else step.input],
            ["Output", step.output[:200] + "..." if len(step.output) > 200 else step.output]
        ]
        
        step_table = Table(step_data, colWidths=[1.5*inch, 5*inch])
        step_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(step_table)
        story.append(Spacer(1, 0.2*inch))
    
    # Resultado final
    story.append(PageBreak())
    story.append(Paragraph("Resultado Final", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    # Respuesta
    if "answer" in session.result:
        story.append(Paragraph("<b>Respuesta:</b>", styles['Normal']))
        story.append(Paragraph(session.result["answer"], styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Datos
    if "data" in session.result:
        story.append(Paragraph("<b>Datos:</b>", styles['Normal']))
        data_str = json.dumps(session.result["data"], indent=2)
        story.append(Paragraph(f"<pre>{data_str}</pre>", styles['Code']))
        story.append(Spacer(1, 0.2*inch))
    
    # SQL
    if "sql" in session.result:
        story.append(Paragraph("<b>SQL:</b>", styles['Normal']))
        story.append(Paragraph(f"<pre>{session.result['sql']}</pre>", styles['Code']))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"Generado por SDRAG Chainlit | {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)


# Uso en app.py
def export_session_to_pdf(session_id: str) -> str:
    """Exporta sesión a PDF."""
    session = audit_manager.load_session(session_id)
    if not session:
        raise ValueError(f"Sesión {session_id} no encontrada")
    
    output_path = f"audit_trails/audit_report_{session_id[:8]}.pdf"
    generate_audit_pdf(session, output_path)
    return output_path
```

### ✅ Criterios de Completitud

**Testing:**
```bash
pytest tests/test_audit_trail.py::test_pdf_export -v
```

**Tests específicos:**
- [ ] PDF generado es válido
- [ ] Contiene todas las secciones (metadata, pasos, resultado)
- [ ] Formato profesional (tablas, colores)
- [ ] <1MB de tamaño para sesión típica

**Verificación manual:**
```bash
# Generar PDF de sesión
python3 -c "
from services.audit_trail import audit_manager, generate_audit_pdf
session = audit_manager.load_session('session-id')
generate_audit_pdf(session, 'test_report.pdf')
"
# Abrir PDF
xdg-open test_report.pdf
```

**Calidad visual:**
- [ ] Fuentes legibles
- [ ] Colores corporativos (azul SDRAG)
- [ ] Tablas bien formateadas

---

## Tarea 7.3: Guardar Historial en Base de Datos

### Descripción
Almacenar audit trails en SQLite para consultas históricas.

### Dependencias
```bash
uv add sqlalchemy aiosqlite
```

### Código de referencia

```python
"""Almacenamiento de audit trails en SQLite."""
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class AuditSession(Base):
    """Modelo de sesión de auditoría."""
    __tablename__ = 'audit_sessions'
    
    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(Text, nullable=False)
    classification = Column(JSON)
    total_duration_ms = Column(Float)
    result = Column(JSON)
    steps = Column(JSON)  # Lista de pasos serializada
    error = Column(Text, nullable=True)


class AuditDatabase:
    """Gestor de base de datos de auditoría."""
    
    def __init__(self, db_path: str = "./audit_trails/audit.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def save_session(self, session_trace: SessionTrace):
        """Guarda sesión en BD."""
        db_session = self.Session()
        
        audit_record = AuditSession(
            session_id=session_trace.session_id,
            user_id=session_trace.user_id,
            timestamp=session_trace.timestamp,
            query=session_trace.query,
            classification=session_trace.classification,
            total_duration_ms=session_trace.total_duration_ms,
            result=session_trace.result,
            steps=[step.dict() for step in session_trace.steps],
            error=session_trace.error
        )
        
        db_session.add(audit_record)
        db_session.commit()
        db_session.close()
    
    def get_session(self, session_id: str) -> Optional[SessionTrace]:
        """Recupera sesión por ID."""
        db_session = self.Session()
        record = db_session.query(AuditSession).filter_by(session_id=session_id).first()
        db_session.close()
        
        if not record:
            return None
        
        return SessionTrace(
            session_id=record.session_id,
            user_id=record.user_id,
            timestamp=record.timestamp,
            query=record.query,
            classification=record.classification,
            total_duration_ms=record.total_duration_ms,
            result=record.result,
            steps=[StepTrace(**step) for step in record.steps],
            error=record.error
        )
    
    def get_user_sessions(self, user_id: str, limit: int = 50) -> List[AuditSession]:
        """Recupera últimas sesiones de un usuario."""
        db_session = self.Session()
        sessions = db_session.query(AuditSession)\
            .filter_by(user_id=user_id)\
            .order_by(AuditSession.timestamp.desc())\
            .limit(limit)\
            .all()
        db_session.close()
        return sessions


# Instancia global
audit_db = AuditDatabase()
```

### ✅ Criterios de Completitud

**Testing:**
```bash
pytest tests/test_audit_trail.py::test_database_storage -v
```

**Tests específicos:**
- [ ] Inserción de sesión exitosa
- [ ] Recuperación por session_id
- [ ] Query por user_id retorna lista ordenada
- [ ] JSON serializable correctamente

**Verificación:**
```bash
sqlite3 audit_trails/audit.db "SELECT count(*) FROM audit_sessions;"
sqlite3 audit_trails/audit.db "SELECT session_id, query, total_duration_ms FROM audit_sessions LIMIT 5;"
```

---

## Tarea 7.4: Dashboard de Métricas de Uso

### Descripción
Crear endpoint simple para visualizar estadísticas de uso.

### Código de referencia

```python
"""Dashboard de métricas de uso."""
from collections import Counter
from datetime import datetime, timedelta
import pandas as pd


class UsageMetrics:
    """Métricas de uso del sistema."""
    
    def __init__(self, audit_db: AuditDatabase):
        self.db = audit_db
    
    def get_metrics_summary(self, days: int = 7) -> dict:
        """Resumen de métricas de últimos N días."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db_session = self.db.Session()
        sessions = db_session.query(AuditSession)\
            .filter(AuditSession.timestamp >= cutoff_date)\
            .all()
        db_session.close()
        
        if not sessions:
            return {"error": "No hay datos"}
        
        # Métricas básicas
        total_queries = len(sessions)
        avg_duration = sum(s.total_duration_ms for s in sessions) / total_queries
        
        # Clasificaciones
        routes = [s.classification.get('route', 'unknown') for s in sessions if s.classification]
        route_counts = Counter(routes)
        
        # Usuarios activos
        users = set(s.user_id for s in sessions)
        
        # Errores
        errors = sum(1 for s in sessions if s.error)
        
        return {
            "period_days": days,
            "total_queries": total_queries,
            "avg_duration_ms": avg_duration,
            "p50_duration_ms": pd.Series([s.total_duration_ms for s in sessions]).median(),
            "p95_duration_ms": pd.Series([s.total_duration_ms for s in sessions]).quantile(0.95),
            "routes": dict(route_counts),
            "active_users": len(users),
            "error_rate": errors / total_queries if total_queries > 0 else 0
        }


# Uso
metrics = UsageMetrics(audit_db)
summary = metrics.get_metrics_summary(days=7)
print(json.dumps(summary, indent=2))
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Métricas calculadas correctamente
- [ ] P50, P95 latency precisas
- [ ] Route distribution correcta

**Output esperado:**
```json
{
  "period_days": 7,
  "total_queries": 150,
  "avg_duration_ms": 1823.5,
  "p50_duration_ms": 1650.0,
  "p95_duration_ms": 3200.0,
  "routes": {
    "semantic": 120,
    "documental": 25,
    "hybrid": 5
  },
  "active_users": 3,
  "error_rate": 0.02
}
```

---

## Resumen de Entregables Fase 7

| ID  | Entregable | Archivo | Estado |
|-----|-----------|---------|--------|
| 7.1 | Exportación JSON | `services/audit_trail.py` | ⬜ Pendiente |
| 7.2 | Exportación PDF | `services/audit_trail.py` | ⬜ Pendiente |
| 7.3 | Base de datos SQLite | `services/audit_trail.py` | ⬜ Pendiente |
| 7.4 | Dashboard de métricas | `services/audit_trail.py` | ⬜ Pendiente |

---

## Métricas de Éxito Fase 7

| Métrica | Objetivo | Verificación |
|---------|----------|--------------|
| **Sesión JSON completa** | 100% de pasos capturados | Validación schema |
| **PDF legible** | Formato profesional | Revisión manual |
| **Latencia de guardado** | <100ms insert en SQLite | Benchmark |
| **Retrieval de historial** | <500ms para últimas 50 | Query performance |

---

## Valor para Auditoría FP&A

### Trazabilidad Completa
- ✅ Pregunta → SQL → Datos → Explicación (todo registrado)
- ✅ Timestamps precisos por paso
- ✅ Duración de cada operación

### Reproducibilidad
- ✅ Mismo input genera mismo output numérico (determinismo)
- ✅ Puede re-ejecutarse con datos históricos
- ✅ Evidencia para auditorías externas

### Compliance
- ✅ Registro de quién consultó qué y cuándo
- ✅ Export a PDF para reportes de auditoría
- ✅ Historial inmutable en SQLite

---

## Notas de Implementación

### Almacenamiento

**Estructura recomendada:**
```
audit_trails/
├── audit.db                              # SQLite
├── audit_trail_20260120_abc12345.json    # JSONs individuales
├── audit_report_abc12345.pdf             # PDFs
└── README.md                             # Documentación
```

### Retención de Datos

- **Desarrollo**: 30 días
- **Producción**: 7 años (requirement financiero típico)
- **Implementar rotación**: Archivar a MinIO después de 90 días

### Privacy

- **No guardar datos sensibles** en audit trail (ej: SSN, passwords)
- **Anonimizar user_id** si es requerido por GDPR
- **Encriptar PDFs** si contienen PII

---

**Tiempo estimado Fase 7:** 12-15 horas

**Dependencias críticas:**
- Fase 2 (cl.Step) para captura de trazas

**Próxima fase:** Fase 8 - Evaluación con Benchmarks
