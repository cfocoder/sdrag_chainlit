# Fase 5: Capa Semántica (Cube Core)

**Objetivo**: Implementar modelo semántico completo con métricas FP&A y pre-aggregations.

**Prioridad**: CRÍTICA - Componente central de ejecución determinista.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 0: Infraestructura verificada
- [x] Fase 4: Router n8n (para orquestación)

### Servicios que deben estar operativos

Ejecutar antes de comenzar:
```bash
# Verificar Cube Core
curl -s http://100.116.107.52:4000/readyz
# Esperado: {"health":"ok"}

# Verificar Redis (caché de Cube)
ssh vostro
redis-cli ping
# Esperado: PONG

# Verificar DuckDB accesible
ssh macmini
ls -lh /mnt/ducklake/facts.parquet
```

- [ ] Cube Core: `http://100.116.107.52:4000` - Capa semántica
- [ ] Redis: `localhost:6379` (en vostro) - Caché
- [ ] DuckDB: Datos en MinIO DuckLake

---

## Contexto

### ¿Por qué Cube Core?

Cube Core actúa como **Single Source of Truth (SSOT)** para métricas FP&A:

| Característica | Beneficio |
|----------------|-----------|
| **Métricas como código** | Versionadas en Git, auditables |
| **SQL determinista** | Mismo input → mismo output |
| **Pre-aggregations** | Cache inteligente (Redis) |
| **API headless** | Consumible por Chainlit, n8n, scripts Python |
| **Separación semántica/física** | Desacopla lógica de negocio de SQL crudo |

### Rol de Cube Core en SDRAG

Cube Core **SÍ es responsable de**:
- Generar SQL canónico para métricas FP&A
- Ejecutar queries sobre DuckDB/DuckLake
- Proveer pre-aggregations para queries frecuentes
- Exponer API REST/GraphQL para consumo

Cube Core **NO participa en**:
- Clasificación de consultas (responsabilidad de n8n)
- Generación de embeddings (responsabilidad de Ollama)
- Generación de explicaciones (responsabilidad de Dify)
- Decisiones de enrutamiento (responsabilidad de n8n)

**Principio crítico**: Cube Core garantiza que **todos los números provengan de una única definición versionada**, eliminando discrepancias.

---

## Arquitectura de Cube Core

```
n8n Router (Ruta Semántica)
          ↓
  Cube Core API (REST/GraphQL)
          ↓
    [Query Planner]
          ↓
    [Pre-aggregations Check]
       ↓           ↓
    Cache Hit   Cache Miss
    (Redis)        ↓
       ↓      [SQL Generation]
       ↓           ↓
       +----→ DuckDB ←----+
                 ↓
            MinIO (DuckLake)
                 ↓
         Resultado JSON
                 ↓
            n8n → Dify → Chainlit
```

---

## Tarea 5.1: Estructura de Proyecto Cube

### Descripción
Crear estructura de directorios para modelo Cube Core.

### Comando

```bash
# En vostro (donde corre Cube Core)
cd /home/hectorsa/cube-models/
mkdir -p cube_models schema
touch cube_models/Facts.js
touch cube_models/Dimensions.js
touch cube.js
touch .env
```

### Estructura resultante

```
cube-models/
├── cube.js                 # Configuración principal
├── .env                    # Variables de entorno
├── cube_models/
│   ├── Facts.js            # Cubo principal de hechos
│   └── Dimensions.js       # Dimensiones (tiempo, geografía)
└── schema/
    └── readme.md           # Documentación del schema
```

### Criterios de aceptación
- [ ] Estructura de directorios creada
- [ ] Archivos base existentes

---

## Tarea 5.2: Configuración de Cube Core

### Descripción
Configurar `cube.js` con conexión a DuckDB.

### Archivo: cube.js

```javascript
// cube.js - Configuración principal de Cube Core

module.exports = {
  // Repositorio de modelos
  schemaPath: 'cube_models',

  // Configuración de base de datos
  driverFactory: ({ dataSource }) => {
    const DuckDBDriver = require('@cubejs-backend/duckdb-driver');
    
    return new DuckDBDriver({
      dataSource: process.env.CUBEJS_DATASOURCE,
      database: process.env.DUCKDB_DATABASE || ':memory:',
      // Habilitar extensión httpfs para leer de MinIO
      initSql: `
        INSTALL httpfs;
        LOAD httpfs;
        SET s3_endpoint='100.110.109.43:9000';
        SET s3_use_ssl=false;
        SET s3_access_key_id='${process.env.MINIO_ACCESS_KEY}';
        SET s3_secret_access_key='${process.env.MINIO_SECRET_KEY}';
      `
    });
  },

  // Configuración de caché (Redis)
  cacheAndQueueDriver: 'redis',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',

  // Pre-aggregations
  preAggregationsSchema: 'pre_aggregations',
  
  // API Configuration
  apiSecret: process.env.CUBEJS_API_SECRET,
  
  // Logging
  logger: (msg, params) => {
    console.log(`${msg}: ${JSON.stringify(params)}`);
  },

  // Opciones de query
  queryRewrite: (query, { securityContext }) => {
    // Aquí se pueden agregar filtros de seguridad
    // Por ahora, pasar query tal cual
    return query;
  },

  // Telemetría deshabilitada para privacidad
  telemetry: false,

  // Refresh de pre-aggregations
  scheduledRefreshTimer: 3600, // 1 hora
};
```

### Archivo: .env

```bash
# Cube Core Configuration
CUBEJS_DEV_MODE=true
CUBEJS_API_SECRET=<generar-con-openssl-rand-hex-32>
CUBEJS_DATASOURCE=default

# DuckDB
DUCKDB_DATABASE=/data/sdrag.duckdb

# Redis Cache
REDIS_URL=redis://localhost:6379

# MinIO (DuckLake)
MINIO_ACCESS_KEY=<minio-access-key>
MINIO_SECRET_KEY=<minio-secret-key>
MINIO_ENDPOINT=http://100.110.109.43:9000

# Logs
CUBEJS_LOG_LEVEL=info
```

### Criterios de aceptación
- [ ] cube.js correctamente configurado
- [ ] .env con variables necesarias
- [ ] Conexión a DuckDB exitosa
- [ ] Redis accesible para caché

---

## Tarea 5.3: Definir Cubo Facts

### Descripción
Crear modelo de datos principal con métricas FP&A.

### Archivo: cube_models/Facts.js

```javascript
// cube_models/Facts.js - Cubo principal de hechos financieros

cube('Facts', {
  // Tabla fuente en DuckDB
  sql: `
    SELECT * FROM read_parquet('s3://ducklake/facts/*.parquet')
  `,

  // Joins con dimensiones (opcional)
  joins: {
    // Agregar joins cuando se implementen dimensiones
  },

  // ========== MEASURES (Métricas) ==========
  
  measures: {
    // Revenue (Ingresos)
    revenue: {
      sql: `amount`,
      type: `sum`,
      title: 'Revenue',
      description: 'Total revenue from sales and services',
      format: 'currency',
      meta: {
        unit: 'USD',
        category: 'Income Statement'
      }
    },

    // COGS (Cost of Goods Sold)
    cogs: {
      sql: `cost_of_goods_sold`,
      type: `sum`,
      title: 'COGS',
      description: 'Cost of Goods Sold',
      format: 'currency',
      meta: {
        unit: 'USD',
        category: 'Income Statement'
      }
    },

    // Gross Margin
    grossMargin: {
      sql: `${revenue} - ${cogs}`,
      type: `number`,
      title: 'Gross Margin',
      description: 'Revenue minus Cost of Goods Sold',
      format: 'currency',
      meta: {
        formula: 'Revenue - COGS',
        category: 'Income Statement'
      }
    },

    // Gross Margin %
    grossMarginPercentage: {
      sql: `CASE WHEN ${revenue} > 0 THEN (${grossMargin} / ${revenue}) * 100 ELSE 0 END`,
      type: `number`,
      title: 'Gross Margin %',
      description: 'Gross Margin as percentage of Revenue',
      format: 'percent',
      meta: {
        formula: '(Gross Margin / Revenue) * 100'
      }
    },

    // OPEX (Operating Expenses)
    opex: {
      sql: `operating_expenses`,
      type: `sum`,
      title: 'OPEX',
      description: 'Operating Expenses',
      format: 'currency',
      meta: {
        unit: 'USD',
        category: 'Income Statement'
      }
    },

    // EBITDA
    ebitda: {
      sql: `${grossMargin} - ${opex}`,
      type: `number`,
      title: 'EBITDA',
      description: 'Earnings Before Interest, Taxes, Depreciation and Amortization',
      format: 'currency',
      meta: {
        formula: 'Gross Margin - OPEX',
        category: 'Income Statement'
      }
    },

    // EBITDA %
    ebitdaPercentage: {
      sql: `CASE WHEN ${revenue} > 0 THEN (${ebitda} / ${revenue}) * 100 ELSE 0 END`,
      type: `number`,
      title: 'EBITDA %',
      description: 'EBITDA as percentage of Revenue',
      format: 'percent'
    },

    // Depreciation & Amortization
    depreciationAmortization: {
      sql: `depreciation_amortization`,
      type: `sum`,
      title: 'D&A',
      description: 'Depreciation and Amortization',
      format: 'currency'
    },

    // EBIT (Operating Income)
    ebit: {
      sql: `${ebitda} - ${depreciationAmortization}`,
      type: `number`,
      title: 'EBIT',
      description: 'Earnings Before Interest and Taxes (Operating Income)',
      format: 'currency',
      meta: {
        formula: 'EBITDA - D&A'
      }
    },

    // Interest Expense
    interestExpense: {
      sql: `interest_expense`,
      type: `sum`,
      title: 'Interest Expense',
      description: 'Interest paid on debt',
      format: 'currency'
    },

    // Tax Expense
    taxExpense: {
      sql: `tax_expense`,
      type: `sum`,
      title: 'Tax Expense',
      description: 'Income tax expense',
      format: 'currency'
    },

    // Net Income
    netIncome: {
      sql: `${ebit} - ${interestExpense} - ${taxExpense}`,
      type: `number`,
      title: 'Net Income',
      description: 'Bottom line profit after all expenses',
      format: 'currency',
      meta: {
        formula: 'EBIT - Interest - Taxes',
        category: 'Income Statement'
      }
    },

    // Transaction Count (para análisis)
    transactionCount: {
      sql: `id`,
      type: `count`,
      title: 'Transaction Count',
      description: 'Number of transactions'
    },

    // Average Revenue per Transaction
    avgRevenuePerTransaction: {
      sql: `${revenue} / ${transactionCount}`,
      type: `number`,
      title: 'Avg Revenue/Transaction',
      description: 'Average revenue per transaction',
      format: 'currency'
    }
  },

  // ========== DIMENSIONS (Atributos) ==========

  dimensions: {
    // Fiscal Quarter
    fiscalQuarter: {
      sql: `fiscal_quarter`,
      type: `string`,
      title: 'Fiscal Quarter',
      description: 'Fiscal quarter (Q1_2024, Q2_2024, etc.)'
    },

    // Fiscal Year
    fiscalYear: {
      sql: `fiscal_year`,
      type: `number`,
      title: 'Fiscal Year',
      description: 'Fiscal year (2023, 2024, etc.)'
    },

    // Date
    date: {
      sql: `transaction_date`,
      type: `time`,
      title: 'Transaction Date',
      description: 'Date of the transaction'
    },

    // Month
    month: {
      sql: `EXTRACT(MONTH FROM transaction_date)`,
      type: `number`,
      title: 'Month',
      description: 'Month number (1-12)'
    },

    // Business Unit (si existe)
    businessUnit: {
      sql: `business_unit`,
      type: `string`,
      title: 'Business Unit',
      description: 'Business unit or division'
    },

    // Region (si existe)
    region: {
      sql: `region`,
      type: `string`,
      title: 'Region',
      description: 'Geographic region'
    },

    // Product Category (si existe)
    productCategory: {
      sql: `product_category`,
      type: `string`,
      title: 'Product Category',
      description: 'Product category or line'
    }
  },

  // ========== PRE-AGGREGATIONS ==========

  preAggregations: {
    // Main pre-aggregation: métricas clave por trimestre
    quarterlyMetrics: {
      measures: [
        revenue, 
        cogs, 
        grossMargin, 
        opex, 
        ebitda, 
        netIncome
      ],
      dimensions: [fiscalQuarter, fiscalYear],
      timeDimension: date,
      granularity: `quarter`,
      refreshKey: {
        every: `1 hour` // Actualizar cada hora
      },
      partitionGranularity: `year`,
      buildRangeStart: {
        sql: `SELECT MIN(transaction_date) FROM read_parquet('s3://ducklake/facts/*.parquet')`
      },
      buildRangeEnd: {
        sql: `SELECT MAX(transaction_date) FROM read_parquet('s3://ducklake/facts/*.parquet')`
      }
    },

    // Pre-aggregation mensual
    monthlyMetrics: {
      measures: [revenue, cogs, ebitda],
      dimensions: [fiscalYear],
      timeDimension: date,
      granularity: `month`,
      refreshKey: {
        every: `2 hours`
      }
    },

    // Pre-aggregation anual (muy rápida)
    yearlyMetrics: {
      measures: [revenue, cogs, grossMargin, ebitda, netIncome],
      dimensions: [fiscalYear],
      timeDimension: date,
      granularity: `year`,
      refreshKey: {
        every: `6 hours`
      }
    }
  },

  // ========== SEGMENTS (Filtros predefinidos) ==========

  segments: {
    // Solo transacciones del año actual
    currentYear: {
      sql: `${CUBE}.fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)`
    },

    // Solo transacciones positivas (revenue > 0)
    profitableTransactions: {
      sql: `${revenue} > 0`
    }
  }
});
```

### Criterios de aceptación
- [ ] Facts.js correctamente definido
- [ ] Todas las métricas FP&A implementadas (Revenue, COGS, EBITDA, etc.)
- [ ] Pre-aggregations configuradas (quarterly, monthly, yearly)
- [ ] Dimensions básicas definidas

---

## Tarea 5.4: Iniciar Cube Core

### Descripción
Levantar servicio Cube Core en vostro.

### Comando

```bash
# En vostro
cd /home/hectorsa/cube-models/

# Instalar Cube Core si no está instalado
npm install -g @cubejs-backend/server-core
npm install @cubejs-backend/duckdb-driver

# O con Docker (recomendado)
docker run -d \
  --name cube \
  --restart unless-stopped \
  -p 4000:4000 \
  -v $(pwd):/cube/conf \
  -v /data:/data \
  --env-file .env \
  cubejs/cube:latest
```

### Verificación

```bash
# Health check
curl http://localhost:4000/readyz
# Esperado: {"health":"ok"}

# Verificar métricas disponibles
curl http://localhost:4000/cubejs-api/v1/meta | jq '.cubes[].measures'

# Debe mostrar: revenue, cogs, grossMargin, ebitda, etc.
```

### Criterios de aceptación
- [ ] Cube Core corriendo en puerto 4000
- [ ] Health check retorna OK
- [ ] Meta API muestra métricas definidas
- [ ] Logs sin errores de conexión a DuckDB

---

## Tarea 5.5: Query de Prueba

### Descripción
Ejecutar query de prueba para verificar funcionalidad.

### Query REST API

```bash
curl -X POST http://100.116.107.52:4000/cubejs-api/v1/load \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "measures": ["Facts.revenue", "Facts.ebitda"],
      "dimensions": ["Facts.fiscalQuarter"],
      "filters": [
        {
          "member": "Facts.fiscalYear",
          "operator": "equals",
          "values": ["2024"]
        }
      ],
      "order": {
        "Facts.fiscalQuarter": "asc"
      }
    }
  }' | jq .
```

### Respuesta esperada

```json
{
  "data": [
    {
      "Facts.fiscalQuarter": "Q1_2024",
      "Facts.revenue": 980000,
      "Facts.ebitda": 320000
    },
    {
      "Facts.fiscalQuarter": "Q2_2024",
      "Facts.revenue": 1050000,
      "Facts.ebitda": 380000
    }
  ],
  "annotation": {
    "measures": {
      "Facts.revenue": {
        "title": "Revenue",
        "shortTitle": "Revenue",
        "type": "number",
        "format": "currency"
      }
    }
  },
  "query": {
    "sql": "SELECT fiscal_quarter, SUM(amount) as revenue, ... FROM facts WHERE fiscal_year = 2024 GROUP BY fiscal_quarter ORDER BY fiscal_quarter"
  }
}
```

### Criterios de aceptación
- [ ] Query ejecutada exitosamente
- [ ] Datos retornados correctamente
- [ ] SQL visible en respuesta
- [ ] Formato de respuesta JSON válido

---

## Tarea 5.6: Integración con n8n

### Descripción
Modificar workflow n8n para usar Cube Core API real.

### Nodo HTTP Request en n8n (actualizar Tarea 4.4)

**Configuración**:
- **Method**: POST
- **URL**: `http://100.116.107.52:4000/cubejs-api/v1/load`
- **Headers**:
  - `Content-Type`: `application/json`
- **Body**: Generado por Function Node previo

### Function Node: Build Cube Query

```javascript
// Construir query dinámicamente basado en clasificación
const query = $input.item.json.query_normalized;
const detected_metric = $input.item.json.detected_metric; // de clasificación
const detected_period = $input.item.json.detected_period;

// Mapear métrica detectada a medida Cube
const metricMap = {
  'revenue': 'Facts.revenue',
  'cogs': 'Facts.cogs',
  'ebitda': 'Facts.ebitda',
  'margen': 'Facts.grossMargin',
  'utilidad': 'Facts.netIncome'
};

const cubeMeasure = metricMap[detected_metric] || 'Facts.revenue';

// Construir query Cube
const cubeQuery = {
  query: {
    measures: [cubeMeasure],
    dimensions: ['Facts.fiscalQuarter'],
    filters: detected_period ? [
      {
        member: 'Facts.fiscalQuarter',
        operator: 'equals',
        values: [detected_period]
      }
    ] : [],
    order: {
      'Facts.fiscalQuarter': 'asc'
    }
  }
};

return {
  json: {
    ...($input.item.json),
    cube_query: cubeQuery
  }
};
```

### Parse Cube Response

```javascript
// Extraer datos de respuesta Cube Core
const cubeData = $input.item.json.data;
const sql = $input.item.json.query.sql;

// Transformar a formato simple para Dify
const data = cubeData.reduce((acc, row) => {
  const key = row['Facts.fiscalQuarter'];
  const value = Object.values(row).find(v => typeof v === 'number');
  acc[key] = value;
  return acc;
}, {});

return {
  json: {
    query: $input.item.json.query,
    route: 'semantic',
    data: data,
    sql: sql,
    timestamp: new Date().toISOString()
  }
};
```

### Criterios de aceptación
- [ ] n8n llama correctamente a Cube Core API
- [ ] Query construida dinámicamente
- [ ] Response parseada correctamente
- [ ] SQL visible para trazabilidad

---

## Tarea 5.7: Pre-aggregations Build

### Descripción
Construir pre-aggregations para acelerar queries frecuentes.

### Comando

```bash
# Forzar build de pre-aggregations
curl -X POST http://100.116.107.52:4000/cubejs-api/v1/pre-aggregations/build \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "measures": ["Facts.revenue"],
      "dimensions": ["Facts.fiscalQuarter"]
    }
  }'
```

### Verificar en Redis

```bash
ssh vostro
redis-cli

# Ver keys de pre-aggregations
KEYS pre_aggregations:*

# Verificar TTL
TTL pre_aggregations:Facts_quarterlyMetrics
```

### Criterios de aceptación
- [ ] Pre-aggregations construidas exitosamente
- [ ] Keys visibles en Redis
- [ ] Queries subsecuentes usan caché (verificar en logs)
- [ ] Latencia reducida en queries repetidas

---

## Tarea 5.8: Dashboard de Monitoreo

### Descripción
Configurar Cube Playground para testing y debugging.

### Habilitar Cube Playground

En `.env`:
```bash
CUBEJS_DEV_MODE=true
CUBEJS_PLAYGROUND_AUTH_SECRET=<secret>
```

### Acceso

```
http://100.116.107.52:4000
```

**Nota**: Deshabilitar en producción por seguridad.

### Uso de Playground

1. Ir a "Build" tab
2. Seleccionar métricas: `Facts.revenue`, `Facts.ebitda`
3. Agregar dimensión: `Facts.fiscalQuarter`
4. Agregar filtro: `Facts.fiscalYear = 2024`
5. Ejecutar query
6. Ver SQL generado en "SQL" tab
7. Ver JSON response en "Response" tab

### Criterios de aceptación
- [ ] Playground accesible
- [ ] Queries ejecutables visualmente
- [ ] SQL visible
- [ ] Útil para debugging

---

## Tarea 5.9: Métricas de Performance

### Descripción
Medir latencia de Cube Core para validar objetivo <500ms.

### Script de Benchmarking

```python
# scripts/benchmark_cube_core.py
import httpx
import time
import statistics

async def benchmark_cube_query(query: dict, num_runs: int = 10) -> dict:
    """Benchmark latencia de Cube Core."""
    latencies = []
    
    async with httpx.AsyncClient() as client:
        for _ in range(num_runs):
            start = time.time()
            response = await client.post(
                "http://100.116.107.52:4000/cubejs-api/v1/load",
                json={"query": query}
            )
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
    
    return {
        "p50": statistics.median(latencies),
        "p95": statistics.quantiles(latencies, n=20)[18],
        "p99": statistics.quantiles(latencies, n=100)[98],
        "mean": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies)
    }

# Ejecutar
query = {
    "measures": ["Facts.revenue"],
    "dimensions": ["Facts.fiscalQuarter"],
    "filters": [{"member": "Facts.fiscalYear", "operator": "equals", "values": ["2024"]}]
}

results = await benchmark_cube_query(query)
print(f"P50: {results['p50']:.2f}ms")
print(f"P95: {results['p95']:.2f}ms")
```

### Objetivo

| Métrica | Objetivo | Estrategia si no se cumple |
|---------|----------|---------------------------|
| P50 | <300ms | Verificar pre-aggregations activas |
| P95 | <500ms | Aumentar RAM de Redis, optimizar SQL |
| P99 | <1000ms | Analizar queries lentas en logs |

### Criterios de aceptación
- [ ] Script de benchmark ejecutado
- [ ] P50 < 300ms (con pre-aggregations)
- [ ] P95 < 500ms
- [ ] Latencia acceptable para UX

---

## Testing

### Test Unitario: Validación de Métricas

```python
# tests/test_cube_metrics.py
import pytest
import httpx

@pytest.mark.asyncio
async def test_revenue_metric():
    """Test que métrica revenue existe y retorna datos."""
    query = {
        "measures": ["Facts.revenue"],
        "dimensions": ["Facts.fiscalQuarter"]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://100.116.107.52:4000/cubejs-api/v1/load",
            json={"query": query}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert "Facts.revenue" in data["data"][0]

@pytest.mark.asyncio
async def test_ebitda_calculation():
    """Test que EBITDA se calcula correctamente."""
    query = {
        "measures": ["Facts.revenue", "Facts.cogs", "Facts.opex", "Facts.ebitda"],
        "dimensions": ["Facts.fiscalQuarter"],
        "filters": [
            {"member": "Facts.fiscalQuarter", "operator": "equals", "values": ["Q1_2024"]}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://100.116.107.52:4000/cubejs-api/v1/load",
            json={"query": query}
        )
    
    data = response.json()["data"][0]
    
    # Verificar fórmula: EBITDA = Revenue - COGS - OPEX
    revenue = data["Facts.revenue"]
    cogs = data["Facts.cogs"]
    opex = data["Facts.opex"]
    ebitda = data["Facts.ebitda"]
    
    expected_ebitda = revenue - cogs - opex
    assert abs(ebitda - expected_ebitda) < 0.01  # Tolerancia para float
```

---

## Troubleshooting

### Problema: Cube Core no inicia

```bash
# Verificar logs
docker logs cube --tail 100

# Error común: DuckDB no puede conectar a MinIO
# Solución: Verificar .env tiene MINIO_ACCESS_KEY correctas
```

### Problema: Pre-aggregations no se construyen

```bash
# Verificar Redis
redis-cli ping

# Forzar rebuild
curl -X POST http://localhost:4000/cubejs-api/v1/pre-aggregations/build
```

### Problema: Query muy lenta

```bash
# Verificar si usa pre-aggregation
# En logs de Cube, buscar: "Using pre-aggregation: quarterlyMetrics"

# Si no usa pre-aggregation, forzar refresh
curl -X POST http://localhost:4000/cubejs-api/v1/pre-aggregations/refresh
```

---

## Métricas de Éxito

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| **Latencia P50** | <300ms | ⬜ Medir |
| **Latencia P95** | <500ms | ⬜ Medir |
| **Pre-aggregation Hit Rate** | >80% | ⬜ Medir |
| **Métricas FP&A definidas** | 10+ | ✅ Completado |
| **SQL determinista** | 100% | ✅ Por diseño |

---

## Próximos Pasos

Después de completar esta fase:
1. ✅ Capa semántica operativa con métricas FP&A
2. → Fase 6: Visualizaciones avanzadas (renderizar datos de Cube)
3. → Fase 8: Benchmarks (medir Execution Accuracy con Cube Core)

---

*Documento creado para implementación LLM - Fase 5 crítica del roadmap SDRAG*
