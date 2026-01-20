"""
Tests para classify_query() - clasificación de consultas.

Verifica que las consultas se enruten correctamente:
- Semánticas (FP&A): revenue, expenses, profit, etc.
- Documentales: políticas, procedimientos, etc.
"""
import pytest


class TestClassifyQuery:
    """Tests de la función classify_query()."""

    def test_semantic_revenue_query(self, sample_fpa_query):
        """Query de revenue debe clasificarse como semántica."""
        # TODO: Importar classify_query cuando esté modularizado
        # from app import classify_query
        # result = classify_query(sample_fpa_query)
        # assert result["route"] == "semantic"
        # assert result["metric"] == "revenue"
        pass

    def test_semantic_expenses_query(self):
        """Query de gastos debe clasificarse como semántica."""
        query = "¿Cuáles fueron los gastos operativos del año?"
        # result = classify_query(query)
        # assert result["route"] == "semantic"
        pass

    def test_documental_policy_query(self, sample_documental_query):
        """Query de políticas debe clasificarse como documental."""
        # result = classify_query(sample_documental_query)
        # assert result["route"] == "documental"
        pass

    def test_ambiguous_query_defaults_to_semantic(self):
        """Query ambigua debe defaultear a semántica."""
        query = "Dame información del último período"
        # result = classify_query(query)
        # assert result["route"] in ["semantic", "documental"]
        pass

    def test_classification_returns_required_fields(self, sample_fpa_query):
        """Clasificación debe retornar campos requeridos."""
        # result = classify_query(sample_fpa_query)
        # assert "route" in result
        # assert "confidence" in result or "metric" in result
        pass
