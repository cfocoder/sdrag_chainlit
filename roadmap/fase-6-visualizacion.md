# Fase 6: Visualización Avanzada

**Objetivo**: Implementar DataFrames interactivos y gráficos Plotly para análisis FP&A visual en Chainlit.

**Prioridad**: Media - Mejora la experiencia de usuario pero no es crítica para la validación académica.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 5: Cube Core integrado (para datos reales)
- [x] Fase 2: cl.Step funcionando

### Dependencias
```bash
uv add plotly pandas
```

### Servicios que deben estar operativos
- [ ] Cube Core: `http://100.116.107.52:4000` - Fuente de datos FP&A

---

## Contexto

### ¿Por qué Visualización en Chainlit?

Chainlit soporta nativamente:
- **DataFrames de pandas**: Renderizados como tablas interactivas
- **Gráficos Plotly**: Interactivos, con zoom, hover, filtros
- **Elementos visuales**: Imágenes, archivos, elementos custom

Esto permite que la **consola analítica determinista** de SDRAG proporcione:
- Trazabilidad visual (SQL → DataFrame → Gráfico)
- Análisis de tendencias (líneas, barras)
- Comparaciones YoY, MoM, QoQ
- Ratios y márgenes en gauges

### Tipos de Visualización por Métrica

| Métrica | Tipo de Gráfico | Razón |
|---------|----------------|-------|
| Revenue, EBITDA, NetIncome | Línea | Tendencias temporales |
| Comparaciones YoY, MoM | Barras | Lado a lado |
| Gross Margin, OPEX Ratio | Gauge | Indicadores de % |
| Waterfall Analysis | Waterfall | Contribución por categoría |

---

## Tarea 6.1: Renderizar DataFrames con Paginación

### Descripción
Mostrar resultados de Cube Core como DataFrames paginados en Chainlit.

### Archivo a modificar
`app.py`

### Código de referencia

```python
import pandas as pd
import chainlit as cl

async def render_dataframe(data: dict, step: cl.Step):
    """
    Renderiza datos de Cube Core como DataFrame con paginación.
    
    Args:
        data: Respuesta JSON de Cube Core
        step: cl.Step donde mostrar el DataFrame
    """
    # Convertir JSON a DataFrame
    if "data" in data:
        df = pd.DataFrame(data["data"])
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame([data])
    
    # Formatear columnas numéricas
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        if 'ratio' in col.lower() or 'margin' in col.lower():
            df[col] = df[col].apply(lambda x: f"{x:.2%}")
        elif 'revenue' in col.lower() or 'cost' in col.lower():
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")
    
    # Renombrar columnas para legibilidad
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    
    # Renderizar en Chainlit con paginación automática (50 filas por página)
    await cl.Message(
        content="### Resultados",
        elements=[cl.Dataframe(name="Datos FP&A", data=df, display="inline")]
    ).send()
    
    return df


async def show_data_with_pagination(
    data: list[dict], 
    title: str = "Resultados",
    page_size: int = 50
):
    """
    Muestra datos con paginación manual si exceden page_size.
    """
    df = pd.DataFrame(data)
    total_rows = len(df)
    
    if total_rows <= page_size:
        # Mostrar todo
        await cl.Message(
            content=f"### {title} ({total_rows} filas)",
            elements=[cl.Dataframe(name=title, data=df, display="inline")]
        ).send()
    else:
        # Paginación manual
        num_pages = (total_rows + page_size - 1) // page_size
        
        for page in range(num_pages):
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, total_rows)
            df_page = df.iloc[start_idx:end_idx]
            
            await cl.Message(
                content=f"### {title} - Página {page + 1}/{num_pages} (Filas {start_idx + 1}-{end_idx})",
                elements=[cl.Dataframe(name=f"{title}_p{page+1}", data=df_page, display="inline")]
            ).send()
```

### Integración en @cl.on_message

```python
@cl.on_message
async def main(message: cl.Message):
    # ... pasos anteriores (clasificación, SQL, datos)
    
    # Paso 3: Obtención de datos
    async with cl.Step(name="Datos", type="tool") as step:
        if classification["route"] == "semantic":
            # Llamar a Cube Core (Fase 5)
            cube_response = await call_cube_core(sql)
            data = cube_response["data"]
            
            # Renderizar DataFrame
            df = await render_dataframe(data, step)
            step.output = f"Recuperadas {len(df)} filas"
        else:
            # Ruta documental...
            pass
    
    # ... continuar con explicación Dify
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: DataFrame con 10 filas renderiza correctamente
- [ ] Test: DataFrame con 100 filas pagina automáticamente
- [ ] Test: Columnas numéricas formateadas (%, $)

**Verificación manual:**
```bash
chainlit run app.py
# Consulta: "¿Cuál fue el revenue por trimestre en 2024?"
# Verificar DataFrame con formato:
# | Quarter | Revenue      | COGS        | Gross Margin |
# | Q1 2024 | $980,000.00  | $380,000.00 | 61.22%       |
```

**Benchmark:**
- [ ] Renderizado de 50 filas <200ms
- [ ] Paginación de 1000 filas <1s

---

## Tarea 6.2: Gráficos de Línea (Tendencias)

### Descripción
Crear gráficos de línea para visualizar tendencias de métricas en el tiempo.

### Dependencias
```python
import plotly.graph_objects as go
import plotly.express as px
```

### Código de referencia

```python
import plotly.graph_objects as go
import chainlit as cl

async def plot_trend_line(
    df: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    title: str = "Tendencia Temporal"
) -> go.Figure:
    """
    Crea gráfico de línea para tendencias.
    
    Args:
        df: DataFrame con datos
        x_col: Columna para eje X (típicamente fecha/periodo)
        y_cols: Lista de columnas para eje Y (métricas)
        title: Título del gráfico
    
    Returns:
        Figura de Plotly
    """
    fig = go.Figure()
    
    # Agregar línea por cada métrica
    for col in y_cols:
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode='lines+markers',
            name=col.replace('_', ' ').title(),
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    # Configuración de layout
    fig.update_layout(
        title=title,
        xaxis_title=x_col.replace('_', ' ').title(),
        yaxis_title="Valor",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Formato de eje Y según tipo de métrica
    if any(word in ' '.join(y_cols).lower() for word in ['ratio', 'margin', 'percent']):
        fig.update_yaxes(tickformat=".1%")
    else:
        fig.update_yaxes(tickformat="$,.0f")
    
    return fig


async def show_trend_chart(data: dict, metric: str):
    """
    Muestra gráfico de tendencia en Chainlit.
    """
    df = pd.DataFrame(data["data"])
    
    # Auto-detectar columnas
    time_col = next((col for col in df.columns if 'quarter' in col.lower() or 'period' in col.lower()), df.columns[0])
    value_cols = [col for col in df.columns if col != time_col]
    
    # Crear gráfico
    fig = await plot_trend_line(
        df=df,
        x_col=time_col,
        y_cols=value_cols,
        title=f"Tendencia: {metric.replace('_', ' ').title()}"
    )
    
    # Enviar a Chainlit
    await cl.Message(
        content=f"### 📈 Gráfico de Tendencia: {metric}",
        elements=[cl.Plotly(name="trend_chart", figure=fig, display="inline")]
    ).send()
```

### Integración en flujo principal

```python
@cl.on_message
async def main(message: cl.Message):
    # ... pasos anteriores
    
    # Paso 4: Visualización (opcional)
    async with cl.Step(name="Visualización", type="tool") as step:
        if classification["route"] == "semantic" and len(data["data"]) > 1:
            # Si hay múltiples periodos, mostrar tendencia
            await show_trend_chart(data, classification["metric"])
            step.output = "Gráfico de tendencia generado"
        else:
            step.output = "Sin visualización (datos únicos)"
    
    # ... explicación Dify
```

### ✅ Criterios de Completitud

**Testing:**
```bash
pytest tests/test_visualization.py::test_plot_trend_line -v
```

**Tests específicos:**
- [ ] Gráfico con 4 trimestres renderiza correctamente
- [ ] Múltiples métricas en el mismo gráfico
- [ ] Formato de eje Y correcto (%, $)
- [ ] Hover muestra valores exactos

**Verificación manual:**
```bash
chainlit run app.py
# Consulta: "Muestra el revenue por trimestre en 2024"
# Verificar gráfico interactivo con:
# - Línea con markers
# - Hover con valores
# - Leyenda horizontal arriba
```

**Benchmark:**
- [ ] Renderizado de gráfico <300ms
- [ ] Interactividad fluida (zoom, pan)

---

## Tarea 6.3: Gráficos de Barras (Comparaciones)

### Descripción
Crear gráficos de barras para comparaciones YoY, MoM, QoQ.

### Código de referencia

```python
import plotly.graph_objects as go

async def plot_comparison_bars(
    df: pd.DataFrame,
    categories: str,
    values: list[str],
    title: str = "Comparación"
) -> go.Figure:
    """
    Crea gráfico de barras para comparaciones.
    
    Args:
        df: DataFrame con datos
        categories: Columna de categorías (ej: periodos)
        values: Lista de columnas a comparar
        title: Título del gráfico
    """
    fig = go.Figure()
    
    # Agregar barra por cada métrica
    for val_col in values:
        fig.add_trace(go.Bar(
            x=df[categories],
            y=df[val_col],
            name=val_col.replace('_', ' ').title(),
            text=df[val_col],
            texttemplate='%{text:$,.0f}',
            textposition='auto'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=categories.replace('_', ' ').title(),
        yaxis_title="Valor",
        barmode='group',  # Barras lado a lado
        template='plotly_white',
        height=500,
        showlegend=True
    )
    
    return fig


async def show_yoy_comparison(current_period: dict, previous_period: dict, metric: str):
    """
    Muestra comparación Year-over-Year.
    """
    # Crear DataFrame comparativo
    comparison_df = pd.DataFrame([
        {"Period": "2023", metric: previous_period[metric]},
        {"Period": "2024", metric: current_period[metric]}
    ])
    
    # Calcular variación
    variance = (current_period[metric] - previous_period[metric]) / previous_period[metric]
    
    # Crear gráfico
    fig = await plot_comparison_bars(
        df=comparison_df,
        categories="Period",
        values=[metric],
        title=f"Comparación YoY: {metric} ({variance:+.1%})"
    )
    
    await cl.Message(
        content=f"### 📊 Comparación Year-over-Year",
        elements=[cl.Plotly(name="yoy_comparison", figure=fig, display="inline")]
    ).send()
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Gráfico con 2 periodos (2023 vs 2024)
- [ ] Etiquetas en barras con valores
- [ ] Variación % en título

**Verificación manual:**
```bash
# Consulta: "Compara el revenue de 2024 vs 2023"
# Verificar barras lado a lado con valores encima
```

**Benchmark:**
- [ ] Renderizado <300ms

---

## Tarea 6.4: Auto-detectar Tipo de Gráfico

### Descripción
Implementar lógica para elegir automáticamente el tipo de gráfico según la consulta.

### Código de referencia

```python
def auto_select_chart_type(data: dict, query: str) -> str:
    """
    Decide qué tipo de gráfico usar según los datos y la consulta.
    
    Returns:
        "line", "bar", "gauge", o "none"
    """
    # Si hay múltiples periodos → línea (tendencia)
    if "data" in data and len(data["data"]) > 2:
        return "line"
    
    # Si query contiene palabras de comparación → barras
    comparison_keywords = ["compara", "vs", "versus", "diferencia", "yoy", "mom"]
    if any(keyword in query.lower() for keyword in comparison_keywords):
        return "bar"
    
    # Si es un ratio o margen único → gauge
    if len(data.get("data", [])) == 1:
        metric_name = query.lower()
        if any(word in metric_name for word in ["ratio", "margen", "margin", "percentage"]):
            return "gauge"
    
    # Default: sin gráfico (solo DataFrame)
    return "none"


@cl.on_message
async def main(message: cl.Message):
    # ... pasos anteriores
    
    # Auto-detectar visualización
    chart_type = auto_select_chart_type(data, query)
    
    if chart_type == "line":
        await show_trend_chart(data, classification["metric"])
    elif chart_type == "bar":
        # Implementar lógica de comparación
        pass
    elif chart_type == "gauge":
        # Implementar gauge (opcional)
        pass
    else:
        # Solo DataFrame
        pass
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Query "tendencia revenue" → gráfico línea
- [ ] Query "compara 2023 vs 2024" → gráfico barras
- [ ] Query "¿cuál fue revenue Q4?" → solo DataFrame

**Verificación:**
```bash
# Test múltiples queries y verificar tipo de gráfico correcto
pytest tests/test_visualization.py::test_auto_select_chart_type -v
```

---

## Tarea 6.5: Tests de Visualización

### Descripción
Implementar tests para funciones de visualización.

### Archivo de test
`tests/test_visualization.py`

### Código de referencia

```python
"""Tests para visualización con Plotly en Chainlit."""
import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch

# Importar funciones de visualización (una vez implementadas)
# from app import plot_trend_line, plot_comparison_bars, auto_select_chart_type


@pytest.fixture
def sample_timeseries_data():
    """Datos de ejemplo con serie temporal."""
    return pd.DataFrame([
        {"quarter": "Q1_2024", "revenue": 980000, "cogs": 380000},
        {"quarter": "Q2_2024", "revenue": 1050000, "cogs": 400000},
        {"quarter": "Q3_2024", "revenue": 1100000, "cogs": 420000},
        {"quarter": "Q4_2024", "revenue": 1234567, "cogs": 450000}
    ])


@pytest.fixture
def sample_comparison_data():
    """Datos de ejemplo para comparación YoY."""
    return pd.DataFrame([
        {"period": "2023", "revenue": 3890000},
        {"period": "2024", "revenue": 4364567}
    ])


class TestVisualization:
    """Tests de funciones de visualización."""
    
    @pytest.mark.asyncio
    async def test_plot_trend_line(self, sample_timeseries_data):
        """Gráfico de línea genera figura válida."""
        from app import plot_trend_line
        
        fig = await plot_trend_line(
            df=sample_timeseries_data,
            x_col="quarter",
            y_cols=["revenue", "cogs"],
            title="Test Trend"
        )
        
        assert fig is not None
        assert len(fig.data) == 2  # 2 líneas (revenue, cogs)
        assert fig.layout.title.text == "Test Trend"
    
    @pytest.mark.asyncio
    async def test_plot_comparison_bars(self, sample_comparison_data):
        """Gráfico de barras genera figura válida."""
        from app import plot_comparison_bars
        
        fig = await plot_comparison_bars(
            df=sample_comparison_data,
            categories="period",
            values=["revenue"],
            title="YoY Comparison"
        )
        
        assert fig is not None
        assert len(fig.data) == 1  # 1 serie de barras
        assert fig.layout.barmode == 'group'
    
    def test_auto_select_chart_type_line(self, sample_timeseries_data):
        """Auto-selección detecta gráfico de línea para series temporales."""
        from app import auto_select_chart_type
        
        data = {"data": sample_timeseries_data.to_dict('records')}
        chart_type = auto_select_chart_type(data, "revenue por trimestre")
        
        assert chart_type == "line"
    
    def test_auto_select_chart_type_bar(self):
        """Auto-selección detecta gráfico de barras para comparaciones."""
        from app import auto_select_chart_type
        
        data = {"data": [{"revenue": 1000000}]}
        chart_type = auto_select_chart_type(data, "compara revenue 2023 vs 2024")
        
        assert chart_type == "bar"
    
    def test_auto_select_chart_type_none(self):
        """Auto-selección retorna 'none' para queries sin visualización."""
        from app import auto_select_chart_type
        
        data = {"data": [{"revenue": 1234567}]}
        chart_type = auto_select_chart_type(data, "cuál fue el revenue de Q4")
        
        assert chart_type == "none"
```

### ✅ Criterios de Completitud

**Ejecución de tests:**
```bash
pytest tests/test_visualization.py -v
# Todos los tests deben pasar
```

**Coverage:**
- [ ] >80% cobertura en funciones de visualización
- [ ] Tests para cada tipo de gráfico (línea, barras)
- [ ] Test de auto-selección

---

## Resumen de Entregables Fase 6

| ID  | Entregable | Archivo | Estado |
|-----|-----------|---------|--------|
| 6.1 | Renderizado de DataFrames | `app.py` | ⬜ Pendiente |
| 6.2 | Gráficos de línea | `app.py` | ⬜ Pendiente |
| 6.3 | Gráficos de barras | `app.py` | ⬜ Pendiente |
| 6.4 | Auto-selección de gráficos | `app.py` | ⬜ Pendiente |
| 6.5 | Tests de visualización | `tests/test_visualization.py` | ⬜ Pendiente |

---

## Métricas de Éxito Fase 6

| Métrica | Objetivo | Verificación |
|---------|----------|--------------|
| **Renderizado de DataFrame** | <200ms para 50 filas | Benchmark en tests |
| **Gráfico interactivo** | <300ms generación | Medición con time.time() |
| **Auto-selección correcta** | >90% accuracy | Tests con queries variadas |
| **UX satisfactoria** | Gráficos legibles | Validación manual |

---

## Notas de Implementación

### Plotly vs Matplotlib

**Elegimos Plotly porque:**
- ✅ Interactividad nativa (zoom, pan, hover)
- ✅ Integración directa con Chainlit (`cl.Plotly`)
- ✅ Renderizado en navegador (no requiere servidor de imágenes)
- ✅ Estilo profesional por defecto

**Matplotlib requeriría:**
- ❌ Guardar imagen a archivo
- ❌ Enviar como `cl.Image`
- ❌ Sin interactividad
- ❌ Más código para estilos profesionales

### Performance

- **DataFrames grandes**: Usar paginación manual si >1000 filas
- **Gráficos complejos**: Limitar a 10-20 series máximo
- **Cache**: Considerar cachear gráficos frecuentes (fase futura)

---

**Tiempo estimado Fase 6:** 15-20 horas

**Dependencias críticas:**
- Fase 5 (Cube Core) para datos reales
- Fase 2 (cl.Step) para integración visual

**Próxima fase:** Fase 7 - Audit Trail y Exportación
