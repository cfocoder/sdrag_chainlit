# Fase 8: Evaluación con Benchmarks

**Objetivo**: Ejecutar benchmarks académicos (Spider, BIRD, FinQA) para medir Execution Accuracy y validar hipótesis de la tesis.

**Prioridad**: CRÍTICA - Validación experimental del protocolo de investigación.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 0: Infraestructura verificada
- [x] Fase 3: RAG Documental (Weaviate)
- [x] Fase 4: Router n8n (clasificación)
- [x] Fase 5: Cube Core (ejecución semántica)

### Datasets requeridos

```bash
# Verificar espacio disponible en DuckLake
ssh macmini
df -h /mnt/ducklake
# Requerido: ~100 GB disponibles

# Listar datasets ya descargados
ls -lh /mnt/ducklake/benchmarks/
```

**Benchmarks a utilizar**:
- Spider (2018): 10,181 queries, 200 DBs (~5 GB)
- BIRD (2023): 12,751 queries, 95 DBs (~33.4 GB)
- FinQA (2021): 8,281 preguntas (~1 GB)
- TAT-QA (2021): 16,552 preguntas (~2 GB)
- FinanceBench (2023): 150 ejemplos (~500 MB)

**Total estimado**: ~42 GB (sin BIRD), ~75 GB (con BIRD)

---

## Contexto

### ¿Por qué Benchmarks?

Los benchmarks validan la hipótesis central de la tesis:

> "Una arquitectura de ejecución determinista (SDRAG) reduce significativamente las alucinaciones aritméticas comparada con Text-to-SQL directo y RAG tradicional."

### Métricas a Medir

| Métrica | Fórmula | Objetivo SDRAG | Baseline LLM |
|---------|---------|----------------|--------------|
| **Execution Accuracy (EX)** | Queries correctas / Total | >95% | ~40% (Spider) |
| **Numerical Hallucination Rate** | Errors aritméticos / Total | <5% | ~60% (FinanceBench) |
| **Query Routing Accuracy** | Rutas correctas / Total | >98% | N/A |
| **Latency P50** | Mediana de latencias | <2s | Variable |
| **Latency P95** | Percentil 95 | <5s | Variable |

### Configuraciones a Comparar

1. **Baseline**: LLM directo (Llama 3.1 70B) sin capa semántica
2. **RAG Tradicional**: LLM + Weaviate (embeddings) generando SQL
3. **SDRAG**: LLM + n8n + Cube Core + Weaviate + Dify

---

## Tarea 8.1: Descarga y Preparación de Benchmarks

### Descripción
Descargar benchmarks y almacenar en DuckLake.

### Spider Benchmark

```bash
# Descargar Spider
cd /tmp
wget https://yale-lily.github.io/spider/spider.zip
unzip spider.zip

# Copiar a DuckLake
ssh macmini
mkdir -p /mnt/ducklake/benchmarks/spider/
scp -r /tmp/spider/* macmini:/mnt/ducklake/benchmarks/spider/

# Verificar
ls -lh /mnt/ducklake/benchmarks/spider/
# Esperado: train_spider.json, dev.json, database/
```

### BIRD Benchmark

```bash
# Descargar BIRD
wget https://bird-bench.github.io/data/bird.zip
unzip bird.zip

# Copiar a DuckLake
ssh macmini
mkdir -p /mnt/ducklake/benchmarks/bird/
scp -r /tmp/bird/* macmini:/mnt/ducklake/benchmarks/bird/
```

### FinQA Benchmark

```bash
# Clonar repositorio
git clone https://github.com/czyssrs/FinQA.git /tmp/finqa

# Copiar datos
ssh macmini
mkdir -p /mnt/ducklake/benchmarks/finqa/
scp -r /tmp/finqa/dataset/* macmini:/mnt/ducklake/benchmarks/finqa/
```

### Criterios de aceptación
- [ ] Spider descargado (~5 GB)
- [ ] BIRD descargado (~33.4 GB) - OPCIONAL
- [ ] FinQA descargado (~1 GB)
- [ ] Archivos en /mnt/ducklake/benchmarks/

---

## Tarea 8.2: Conversión a Formato DuckDB

### Descripción
Convertir benchmarks de formato original (JSON, CSV) a Parquet en DuckLake.

### Script: convert_spider_to_parquet.py

```python
# scripts/convert_spider_to_parquet.py
import json
import pandas as pd
import duckdb
from pathlib import Path
from typing import List, Dict
import asyncio
import dask.dataframe as dd

async def convert_spider_to_parquet(
    spider_path: Path,
    output_path: Path
) -> Dict[str, int]:
    """
    Convierte Spider benchmark a formato Parquet.
    
    Args:
        spider_path: Ruta a spider/dev.json
        output_path: Ruta de salida en DuckLake
    
    Returns:
        Stats de conversión
    """
    print(f"Leyendo Spider desde {spider_path}...")
    
    # Leer JSON
    with open(spider_path) as f:
        spider_data = json.load(f)
    
    # Normalizar a DataFrame
    rows = []
    for idx, item in enumerate(spider_data):
        rows.append({
            "query_id": idx,
            "question": item["question"],
            "sql": item["query"],
            "database": item["db_id"],
            "difficulty": item.get("difficulty", "unknown")
        })
    
    df = pd.DataFrame(rows)
    
    # Escribir a Parquet con Dask (para paralelización)
    ddf = dd.from_pandas(df, npartitions=10)
    
    output_path.mkdir(parents=True, exist_ok=True)
    ddf.to_parquet(
        str(output_path / "spider_queries.parquet"),
        compression='snappy',
        write_index=False
    )
    
    print(f"✅ Spider convertido: {len(df)} queries")
    
    return {
        "num_queries": len(df),
        "databases": df["database"].nunique(),
        "size_mb": df.memory_usage(deep=True).sum() / 1024**2
    }

# Ejecutar
if __name__ == "__main__":
    spider_path = Path("/mnt/ducklake/benchmarks/spider/dev.json")
    output_path = Path("/mnt/ducklake/benchmarks/spider_parquet/")
    
    stats = asyncio.run(convert_spider_to_parquet(spider_path, output_path))
    print(f"Stats: {stats}")
```

### Script: convert_finqa_to_parquet.py

```python
# scripts/convert_finqa_to_parquet.py
import json
import pandas as pd
from pathlib import Path
from typing import Dict

def convert_finqa_to_parquet(
    finqa_path: Path,
    output_path: Path
) -> Dict[str, int]:
    """
    Convierte FinQA benchmark a formato Parquet.
    
    FinQA contiene preguntas sobre reportes financieros que requieren
    operaciones aritméticas multi-paso.
    """
    rows = []
    
    # Leer todos los archivos JSON en el directorio
    for json_file in finqa_path.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            
            for item in data:
                rows.append({
                    "query_id": item["id"],
                    "question": item["question"],
                    "pre_text": item.get("pre_text", ""),
                    "post_text": item.get("post_text", ""),
                    "table": json.dumps(item.get("table", [])),
                    "gold_answer": item["answer"],
                    "program": json.dumps(item.get("program", []))
                })
    
    df = pd.DataFrame(rows)
    
    output_path.mkdir(parents=True, exist_ok=True)
    df.to_parquet(
        output_path / "finqa_queries.parquet",
        compression='snappy',
        index=False
    )
    
    print(f"✅ FinQA convertido: {len(df)} preguntas")
    
    return {
        "num_queries": len(df),
        "size_mb": df.memory_usage(deep=True).sum() / 1024**2
    }

# Ejecutar
if __name__ == "__main__":
    finqa_path = Path("/mnt/ducklake/benchmarks/finqa/")
    output_path = Path("/mnt/ducklake/benchmarks/finqa_parquet/")
    
    stats = convert_finqa_to_parquet(finqa_path, output_path)
    print(f"Stats: {stats}")
```

### Ejecutar Conversión

```bash
# Activar entorno
cd /home/hectorsa/Documents/sdrag_chainlit
source .venv/bin/activate

# Instalar dependencias
uv add dask[dataframe] pyarrow fastparquet

# Ejecutar conversiones
python3 scripts/convert_spider_to_parquet.py
python3 scripts/convert_finqa_to_parquet.py

# Verificar archivos generados
ls -lh /mnt/ducklake/benchmarks/*_parquet/
```

### Criterios de aceptación
- [ ] Spider convertido a Parquet
- [ ] FinQA convertido a Parquet
- [ ] Archivos .parquet accesibles en DuckLake
- [ ] Conversión completa en <30 minutos con Dask

---

## Tarea 8.3: Implementar Evaluator

### Descripción
Crear script que ejecute queries del benchmark y compare con ground truth.

### Script: evaluate_execution_accuracy.py

```python
# scripts/evaluate_execution_accuracy.py
import asyncio
import httpx
import pandas as pd
from pathlib import Path
from typing import List, Dict, Literal
import time
import json

SystemType = Literal["baseline", "rag", "sdrag"]

class BenchmarkEvaluator:
    """Evaluador de Execution Accuracy para benchmarks."""
    
    def __init__(
        self,
        benchmark: str,  # "spider", "finqa", "bird"
        system: SystemType,
        n8n_url: str = "http://100.105.68.15:5678/webhook/sdrag-query",
        llm_url: str = None  # Para baseline
    ):
        self.benchmark = benchmark
        self.system = system
        self.n8n_url = n8n_url
        self.llm_url = llm_url
        self.results: List[Dict] = []
    
    async def load_queries(self, limit: int = None) -> pd.DataFrame:
        """Carga queries del benchmark desde Parquet."""
        parquet_path = f"/mnt/ducklake/benchmarks/{self.benchmark}_parquet/"
        df = pd.read_parquet(parquet_path)
        
        if limit:
            df = df.head(limit)
        
        print(f"Cargadas {len(df)} queries de {self.benchmark}")
        return df
    
    async def execute_query_sdrag(self, query: str) -> Dict:
        """Ejecuta query con sistema SDRAG (n8n + Cube Core + Dify)."""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.n8n_url,
                    json={"query": query, "user_id": "benchmark"}
                )
                response.raise_for_status()
                result = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "data": result.get("data", {}),
                "sql": result.get("sql", ""),
                "explanation": result.get("explanation", ""),
                "route": result.get("route", "unknown"),
                "latency_ms": latency_ms,
                "error": None
            }
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return {
                "success": False,
                "data": None,
                "sql": None,
                "explanation": None,
                "route": None,
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    async def execute_query_baseline(self, query: str) -> Dict:
        """Ejecuta query con LLM directo (sin capa semántica)."""
        # TODO: Implementar llamada a LLM directo
        # Por ahora, mock
        start_time = time.time()
        await asyncio.sleep(0.5)  # Simular latencia
        
        return {
            "success": False,  # Baseline tiende a fallar más
            "data": {},
            "sql": "SELECT * FROM table",  # SQL mock
            "latency_ms": (time.time() - start_time) * 1000,
            "error": "Baseline implementation pending"
        }
    
    def compare_results(self, result: Dict, expected: any) -> bool:
        """
        Compara resultado obtenido con ground truth.
        
        Args:
            result: Resultado del sistema
            expected: Ground truth del benchmark
        
        Returns:
            True si match exacto
        """
        if not result["success"]:
            return False
        
        # Extraer valor numérico del resultado
        # (esto depende del formato de cada benchmark)
        if isinstance(result["data"], dict):
            obtained_values = list(result["data"].values())
            if obtained_values:
                obtained = obtained_values[0]
            else:
                return False
        else:
            obtained = result["data"]
        
        # Comparación con tolerancia para floats
        if isinstance(expected, (int, float)) and isinstance(obtained, (int, float)):
            return abs(obtained - expected) < 0.01  # 1 centavo de tolerancia
        
        # Comparación exacta para strings
        return str(obtained).strip().lower() == str(expected).strip().lower()
    
    async def evaluate(self, limit: int = None) -> Dict:
        """
        Ejecuta evaluación completa del benchmark.
        
        Args:
            limit: Número máximo de queries a evaluar (None = todas)
        
        Returns:
            Métricas agregadas
        """
        print(f"\n{'='*60}")
        print(f"Evaluando {self.benchmark.upper()} con sistema {self.system.upper()}")
        print(f"{'='*60}\n")
        
        # Cargar queries
        df = await self.load_queries(limit)
        
        # Ejecutar queries
        for idx, row in df.iterrows():
            query_id = row.get("query_id", idx)
            question = row["question"]
            expected = row.get("gold_answer") or row.get("sql")
            
            print(f"[{idx+1}/{len(df)}] Ejecutando: {question[:60]}...")
            
            # Ejecutar según sistema
            if self.system == "sdrag":
                result = await self.execute_query_sdrag(question)
            elif self.system == "baseline":
                result = await self.execute_query_baseline(question)
            else:
                raise ValueError(f"Sistema no soportado: {self.system}")
            
            # Comparar con ground truth
            match = self.compare_results(result, expected)
            
            # Guardar resultado
            self.results.append({
                "query_id": query_id,
                "question": question,
                "expected": expected,
                "obtained": result["data"],
                "match": match,
                "latency_ms": result["latency_ms"],
                "route": result.get("route"),
                "error": result["error"],
                "sql": result["sql"]
            })
            
            # Pausa para no saturar servicios
            await asyncio.sleep(0.1)
        
        # Calcular métricas
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """Calcula métricas agregadas."""
        df_results = pd.DataFrame(self.results)
        
        # Execution Accuracy
        execution_accuracy = (df_results["match"].sum() / len(df_results)) * 100
        
        # Numerical Hallucination Rate (inverso de EX)
        hallucination_rate = 100 - execution_accuracy
        
        # Latencias
        latencies = df_results["latency_ms"].dropna()
        
        # Query Routing Accuracy (solo para SDRAG)
        routing_accuracy = None
        if self.system == "sdrag" and "route" in df_results.columns:
            # Aquí se requeriría ground truth de rutas esperadas
            # Por ahora, solo contamos distribución
            route_counts = df_results["route"].value_counts()
            routing_accuracy = route_counts.to_dict()
        
        metrics = {
            "benchmark": self.benchmark,
            "system": self.system,
            "total_queries": len(df_results),
            "execution_accuracy": round(execution_accuracy, 2),
            "hallucination_rate": round(hallucination_rate, 2),
            "latency_p50": round(latencies.median(), 2),
            "latency_p95": round(latencies.quantile(0.95), 2),
            "latency_p99": round(latencies.quantile(0.99), 2),
            "latency_mean": round(latencies.mean(), 2),
            "error_count": df_results["error"].notna().sum(),
            "routing_distribution": routing_accuracy
        }
        
        return metrics
    
    def save_results(self, output_path: Path):
        """Guarda resultados detallados a JSON."""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Resultados detallados
        results_file = output_path / f"{self.benchmark}_{self.system}_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Métricas agregadas
        metrics_file = output_path / f"{self.benchmark}_{self.system}_metrics.json"
        metrics = self.calculate_metrics()
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n✅ Resultados guardados en {output_path}")

# Ejecutar evaluación
async def main():
    # Spider con SDRAG
    evaluator = BenchmarkEvaluator(
        benchmark="spider",
        system="sdrag"
    )
    metrics = await evaluator.evaluate(limit=100)  # Primeras 100 queries
    
    print(f"\n{'='*60}")
    print("RESULTADOS FINALES")
    print(f"{'='*60}")
    print(f"Execution Accuracy: {metrics['execution_accuracy']}%")
    print(f"Hallucination Rate: {metrics['hallucination_rate']}%")
    print(f"Latency P50: {metrics['latency_p50']}ms")
    print(f"Latency P95: {metrics['latency_p95']}ms")
    print(f"{'='*60}\n")
    
    # Guardar resultados
    evaluator.save_results(Path("./benchmark_results/"))

if __name__ == "__main__":
    asyncio.run(main())
```

### Ejecutar Evaluación

```bash
# Spider (100 queries de prueba)
python3 scripts/evaluate_execution_accuracy.py

# FinQA (todas las queries)
# Modificar script con benchmark="finqa", limit=None
```

### Criterios de aceptación
- [ ] Script ejecuta queries del benchmark
- [ ] Compara resultados con ground truth
- [ ] Calcula Execution Accuracy correctamente
- [ ] Guarda resultados a JSON
- [ ] Métricas de latencia incluidas

---

## Tarea 8.4: Comparación Baseline vs SDRAG

### Descripción
Ejecutar evaluación con 3 configuraciones y comparar resultados.

### Script: compare_systems.py

```python
# scripts/compare_systems.py
import asyncio
from evaluate_execution_accuracy import BenchmarkEvaluator
import pandas as pd
import matplotlib.pyplot as plt

async def compare_systems(benchmark: str = "spider", limit: int = 100):
    """Compara 3 sistemas en mismo benchmark."""
    
    results = []
    
    # 1. Baseline (LLM directo)
    print("\n🔍 Evaluando BASELINE...")
    evaluator_baseline = BenchmarkEvaluator(benchmark, "baseline")
    metrics_baseline = await evaluator_baseline.evaluate(limit)
    evaluator_baseline.save_results(Path("./benchmark_results/baseline/"))
    results.append(metrics_baseline)
    
    # 2. RAG Tradicional (pendiente de implementar)
    # TODO: Implementar evaluator para RAG tradicional
    
    # 3. SDRAG
    print("\n🔍 Evaluando SDRAG...")
    evaluator_sdrag = BenchmarkEvaluator(benchmark, "sdrag")
    metrics_sdrag = await evaluator_sdrag.evaluate(limit)
    evaluator_sdrag.save_results(Path("./benchmark_results/sdrag/"))
    results.append(metrics_sdrag)
    
    # Comparación
    df_comparison = pd.DataFrame(results)
    
    print("\n" + "="*70)
    print("COMPARACIÓN DE SISTEMAS")
    print("="*70)
    print(df_comparison[["system", "execution_accuracy", "hallucination_rate", "latency_p50"]])
    print("="*70 + "\n")
    
    # Gráfico comparativo
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Execution Accuracy
    axes[0].bar(df_comparison["system"], df_comparison["execution_accuracy"])
    axes[0].set_ylabel("Execution Accuracy (%)")
    axes[0].set_title("Execution Accuracy por Sistema")
    axes[0].axhline(y=95, color='r', linestyle='--', label='Objetivo (95%)')
    axes[0].legend()
    
    # Latencia P50
    axes[1].bar(df_comparison["system"], df_comparison["latency_p50"])
    axes[1].set_ylabel("Latencia P50 (ms)")
    axes[1].set_title("Latencia por Sistema")
    axes[1].axhline(y=2000, color='r', linestyle='--', label='Objetivo (<2s)')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig("./benchmark_results/comparison.png")
    print("✅ Gráfico guardado en ./benchmark_results/comparison.png")

# Ejecutar
if __name__ == "__main__":
    asyncio.run(compare_systems(benchmark="spider", limit=100))
```

### Ejecutar Comparación

```bash
python3 scripts/compare_systems.py
```

### Criterios de aceptación
- [ ] 3 sistemas evaluados en mismo benchmark
- [ ] Métricas comparativas generadas
- [ ] Gráfico de comparación creado
- [ ] SDRAG supera baseline en EX

---

## Tarea 8.5: Análisis de Errores

### Descripción
Analizar queries que fallaron para identificar patrones.

### Script: analyze_errors.py

```python
# scripts/analyze_errors.py
import json
import pandas as pd
from pathlib import Path
from collections import Counter

def analyze_errors(results_file: Path):
    """Analiza errores en resultados de benchmark."""
    
    with open(results_file) as f:
        results = json.load(f)
    
    df = pd.DataFrame(results)
    
    # Filtrar queries que fallaron
    df_errors = df[df["match"] == False]
    
    print(f"\n{'='*60}")
    print(f"ANÁLISIS DE ERRORES")
    print(f"{'='*60}")
    print(f"Total queries: {len(df)}")
    print(f"Errores: {len(df_errors)} ({len(df_errors)/len(df)*100:.1f}%)")
    print(f"{'='*60}\n")
    
    # Patrones de errores
    if len(df_errors) > 0:
        # Tipos de errores
        error_types = Counter([
            type(err).__name__ if err else "No error message"
            for err in df_errors["error"]
        ])
        
        print("Tipos de errores:")
        for error_type, count in error_types.most_common():
            print(f"  - {error_type}: {count}")
        
        # Queries más difíciles (latencia alta)
        df_errors_sorted = df_errors.sort_values("latency_ms", ascending=False)
        print(f"\nTop 5 queries más lentas con error:")
        for idx, row in df_errors_sorted.head(5).iterrows():
            print(f"  - Q{row['query_id']}: {row['question'][:50]}... ({row['latency_ms']:.0f}ms)")
        
        # Exportar errores para análisis manual
        df_errors[["query_id", "question", "expected", "obtained", "error"]].to_csv(
            "benchmark_results/errors_detail.csv",
            index=False
        )
        print(f"\n✅ Detalles guardados en benchmark_results/errors_detail.csv")

# Ejecutar
if __name__ == "__main__":
    results_file = Path("./benchmark_results/sdrag/spider_sdrag_results.json")
    analyze_errors(results_file)
```

### Criterios de aceptación
- [ ] Errores categorizados
- [ ] Top queries problemáticas identificadas
- [ ] CSV con detalles de errores exportado

---

## Tarea 8.6: Reporte Final

### Descripción
Generar reporte en Markdown con todos los resultados para la tesis.

### Script: generate_report.py

```python
# scripts/generate_report.py
import json
from pathlib import Path
from datetime import datetime

def generate_report(output_path: Path = Path("./benchmark_results/REPORT.md")):
    """Genera reporte en Markdown de resultados de benchmarks."""
    
    # Cargar métricas
    metrics_files = list(Path("./benchmark_results/").rglob("*_metrics.json"))
    
    report = []
    report.append("# Reporte de Evaluación de Benchmarks\n")
    report.append(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**Proyecto**: SDRAG - Arquitectura RAG Híbrida\n\n")
    
    report.append("## Resumen Ejecutivo\n\n")
    
    # Tabla comparativa
    report.append("| Benchmark | Sistema | EX (%) | Halluc. Rate (%) | Latency P50 (ms) | Latency P95 (ms) |\n")
    report.append("|-----------|---------|--------|------------------|------------------|------------------|\n")
    
    for metrics_file in sorted(metrics_files):
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        report.append(
            f"| {metrics['benchmark']} | {metrics['system']} | "
            f"{metrics['execution_accuracy']:.2f} | {metrics['hallucination_rate']:.2f} | "
            f"{metrics['latency_p50']:.2f} | {metrics['latency_p95']:.2f} |\n"
        )
    
    report.append("\n## Métricas Detalladas\n\n")
    
    for metrics_file in sorted(metrics_files):
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        report.append(f"### {metrics['benchmark'].upper()} - {metrics['system'].upper()}\n\n")
        report.append(f"- **Execution Accuracy**: {metrics['execution_accuracy']}%\n")
        report.append(f"- **Hallucination Rate**: {metrics['hallucination_rate']}%\n")
        report.append(f"- **Total Queries**: {metrics['total_queries']}\n")
        report.append(f"- **Latency P50**: {metrics['latency_p50']}ms\n")
        report.append(f"- **Latency P95**: {metrics['latency_p95']}ms\n")
        report.append(f"- **Latency P99**: {metrics['latency_p99']}ms\n")
        report.append(f"- **Error Count**: {metrics['error_count']}\n\n")
        
        if metrics.get("routing_distribution"):
            report.append("**Distribución de Rutas**:\n")
            for route, count in metrics["routing_distribution"].items():
                report.append(f"- {route}: {count}\n")
            report.append("\n")
    
    report.append("## Conclusiones\n\n")
    report.append("TODO: Agregar análisis cualitativo de resultados.\n\n")
    
    # Escribir reporte
    with open(output_path, "w") as f:
        f.writelines(report)
    
    print(f"✅ Reporte generado en {output_path}")

# Ejecutar
if __name__ == "__main__":
    generate_report()
```

### Ejecutar

```bash
python3 scripts/generate_report.py
```

### Criterios de aceptación
- [ ] Reporte REPORT.md generado
- [ ] Tabla comparativa incluida
- [ ] Métricas detalladas por sistema y benchmark
- [ ] Listo para incluir en tesis

---

## Métricas de Éxito (Objetivos de la Tesis)

| Métrica | Baseline | SDRAG Objetivo | SDRAG Medido |
|---------|----------|----------------|--------------|
| **Execution Accuracy** | ~40% | >95% | ⬜ Por medir |
| **Hallucination Rate** | ~60% | <5% | ⬜ Por medir |
| **Query Routing Accuracy** | N/A | >98% | ⬜ Por medir |
| **Latency P50** | Variable | <2s | ⬜ Por medir |
| **Latency P95** | Variable | <5s | ⬜ Por medir |

---

## Troubleshooting

### Problema: Benchmark muy lento

```bash
# Reducir limit en evaluate()
# Usar solo subset de queries
evaluator.evaluate(limit=50)
```

### Problema: Ground truth no disponible

```bash
# Para benchmarks sin ground truth explícito,
# usar validación manual de subset (n=50)
```

### Problema: Timeout en queries complejas

```bash
# Aumentar timeout en httpx
async with httpx.AsyncClient(timeout=60.0) as client:
    ...
```

---

## Próximos Pasos

Después de completar esta fase:
1. ✅ Benchmarks ejecutados y evaluados
2. ✅ Métricas comparativas generadas
3. → Análisis cualitativo de resultados para tesis
4. → Defensa de tesis con evidencia cuantitativa

---

*Documento creado para implementación LLM - Fase 8 crítica para validación de tesis*
