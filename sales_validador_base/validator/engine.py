"""
Validation engine for BNPL datasets.
Adapted from the original CLI validator script to return structured results
suitable for rendering in a Streamlit UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import duckdb
import pandas as pd

from .schemas import PANDAS_TYPE_MAP


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Outcome of a single validation step."""

    stage: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Column-level validations
# ---------------------------------------------------------------------------

def _validate_mandatory_columns(df: pd.DataFrame, schema: dict) -> list[str]:
    missing = [col for col in schema if col not in df.columns]
    if missing:
        return [f"Colunas obrigatórias ausentes: {missing}"]
    return []


def _validate_column_types(
    df: pd.DataFrame, schema: dict, strict: bool = False
) -> list[str]:
    errors: list[str] = []
    for col, expected_type in schema.items():
        if col not in df.columns:
            continue
        actual_dtype = str(df[col].dtype)
        acceptable = PANDAS_TYPE_MAP.get(expected_type, [expected_type])
        if actual_dtype not in acceptable:
            if strict:
                errors.append(
                    f"Coluna '{col}': tipo esperado '{expected_type}' "
                    f"(aceitos: {acceptable}), encontrado '{actual_dtype}'"
                )
            elif expected_type == "float" and actual_dtype == "object":
                errors.append(
                    f"Coluna '{col}': esperado numérico mas encontrado '{actual_dtype}'"
                )
    return errors


# ---------------------------------------------------------------------------
# Schema validation (pre / post processing)
# ---------------------------------------------------------------------------

def run_validations(
    df: pd.DataFrame,
    schema: dict,
    *,
    stage: str,
    strict: bool = False,
) -> ValidationResult:
    """Run column-presence and type validations, returning a structured result."""
    issues: list[str] = []
    issues.extend(_validate_mandatory_columns(df, schema))
    issues.extend(_validate_column_types(df, schema, strict=strict))

    if strict:
        return ValidationResult(stage=stage, passed=not issues, errors=issues)
    return ValidationResult(
        stage=stage,
        passed=not issues,
        warnings=issues if issues else [],
    )


# ---------------------------------------------------------------------------
# DuckDB post-processing
# ---------------------------------------------------------------------------

_POST_PROCESS_SQL = """\
SELECT
    CASE
        WHEN cliente_cnpj IS NULL THEN NULL
        WHEN length(regexp_replace(cliente_cnpj::varchar, '[^0-9]', '', 'g')) <= 11
            THEN lpad(regexp_replace(cliente_cnpj::varchar, '[^0-9]', '', 'g'), 11, '0')
        WHEN length(regexp_replace(cliente_cnpj::varchar, '[^0-9]', '', 'g')) <= 14
            THEN lpad(regexp_replace(cliente_cnpj::varchar, '[^0-9]', '', 'g'), 14, '0')
        ELSE NULL
    END AS cliente_cnpj,
    CASE
        WHEN emitente_cnpj IS NULL THEN NULL
        WHEN length(regexp_replace(emitente_cnpj::varchar, '[^0-9]', '', 'g')) <= 11
            THEN lpad(regexp_replace(emitente_cnpj::varchar, '[^0-9]', '', 'g'), 11, '0')
        WHEN length(regexp_replace(emitente_cnpj::varchar, '[^0-9]', '', 'g')) <= 14
            THEN lpad(regexp_replace(emitente_cnpj::varchar, '[^0-9]', '', 'g'), 14, '0')
        ELSE NULL
    END AS emitente_cnpj,
    id_pedido::varchar   AS id_pedido,
    id_cliente::varchar  AS id_cliente,
    id_parcela::varchar  AS id_parcela,
    forma_pagamento::varchar AS forma_pagamento,
    * EXCLUDE (
        cliente_cnpj, emitente_cnpj, id_pedido, id_cliente, id_parcela,
        forma_pagamento, data_pedido, data_vencimento, data_pagamento,
        valor_parcela, valor_pago
    ),
    COALESCE(
        try_cast(data_pedido AS DATE),
        try_strptime(CAST(data_pedido AS VARCHAR), '%d/%m/%Y')::DATE,
        try_strptime(CAST(data_pedido AS VARCHAR), '%Y-%m-%d')::DATE
    ) AS data_pedido,
    COALESCE(
        try_cast(data_vencimento AS DATE),
        try_strptime(CAST(data_vencimento AS VARCHAR), '%d/%m/%Y')::DATE,
        try_strptime(CAST(data_vencimento AS VARCHAR), '%Y-%m-%d')::DATE
    ) AS data_vencimento,
    COALESCE(
        try_cast(data_pagamento AS DATE),
        try_strptime(CAST(data_pagamento AS VARCHAR), '%d/%m/%Y')::DATE,
        try_strptime(CAST(data_pagamento AS VARCHAR), '%Y-%m-%d')::DATE
    ) AS data_pagamento,
    try_cast(
        CASE
            WHEN regexp_matches(CAST(valor_parcela AS VARCHAR),
                 '^\\d{1,3}(\\.\\d{3})*,\\d+$')
                THEN replace(replace(CAST(valor_parcela AS VARCHAR), '.', ''), ',', '.')
            WHEN regexp_matches(CAST(valor_parcela AS VARCHAR),
                 '^\\d{1,3}(,\\d{3})*\\.\\d+$')
                THEN replace(CAST(valor_parcela AS VARCHAR), ',', '')
            WHEN regexp_matches(CAST(valor_parcela AS VARCHAR),
                 '^\\d+,\\d+$')
                THEN replace(CAST(valor_parcela AS VARCHAR), ',', '.')
            ELSE CAST(valor_parcela AS VARCHAR)
        END
    AS DOUBLE) AS valor_parcela,
    try_cast(
        CASE
            WHEN regexp_matches(CAST(valor_pago AS VARCHAR),
                 '^\\d{1,3}(\\.\\d{3})*,\\d+$')
                THEN replace(replace(CAST(valor_pago AS VARCHAR), '.', ''), ',', '.')
            WHEN regexp_matches(CAST(valor_pago AS VARCHAR),
                 '^\\d{1,3}(,\\d{3})*\\.\\d+$')
                THEN replace(CAST(valor_pago AS VARCHAR), ',', '')
            WHEN regexp_matches(CAST(valor_pago AS VARCHAR),
                 '^\\d+,\\d+$')
                THEN replace(CAST(valor_pago AS VARCHAR), ',', '.')
            ELSE CAST(valor_pago AS VARCHAR)
        END
    AS DOUBLE) AS valor_pago
FROM base_df
"""


def duckdb_post_process(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise CNPJs, parse dates and numeric values using DuckDB."""
    con = duckdb.connect()
    con.register("base_df", df)
    result = con.execute(_POST_PROCESS_SQL).fetchdf()
    con.close()
    return result


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_statistics(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Compute per-column statistics and return as a DataFrame."""
    rows: list[dict] = []
    total_rows = len(df)

    for col, col_type in schema.items():
        if col not in df.columns:
            continue

        nulls = int(df[col].isna().sum())
        null_pct = f"{nulls / total_rows * 100:.1f}%" if total_rows > 0 else "N/A"
        unique_count = int(df[col].nunique(dropna=True))
        stats: dict = {
            "coluna": col,
            "tipo": col_type,
            "total_linhas": total_rows,
            "únicos": unique_count,
            "nulos": nulls,
            "nulos_%": null_pct,
            "min": None,
            "max": None,
            "média": None,
        }

        non_null = df[col].dropna()
        if len(non_null) > 0:
            if col_type == "float":
                stats["min"] = f"{non_null.min():.2f}"
                stats["max"] = f"{non_null.max():.2f}"
                stats["média"] = f"{non_null.mean():.2f}"
            elif col_type == "date":
                mn = non_null.min()
                mx = non_null.max()
                stats["min"] = str(mn.date()) if hasattr(mn, "date") else str(mn)
                stats["max"] = str(mx.date()) if hasattr(mx, "date") else str(mx)
                stats["média"] = "-"
            else:
                stats["min"] = "-"
                stats["max"] = "-"
                stats["média"] = "-"

        rows.append(stats)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Null-limit validation
# ---------------------------------------------------------------------------

def validate_null_limits(
    df: pd.DataFrame, limits: dict[str, int]
) -> ValidationResult:
    """Check that no column exceeds its allowed null count."""
    errors: list[str] = []
    for col, max_nulls in limits.items():
        if col not in df.columns:
            continue
        actual_nulls = int(df[col].isna().sum())
        if actual_nulls > max_nulls:
            errors.append(
                f"Coluna '{col}': {actual_nulls} nulos encontrados, "
                f"máximo permitido: {max_nulls}"
            )
    return ValidationResult(
        stage="Limites de Nulos", passed=not errors, errors=errors
    )


# ---------------------------------------------------------------------------
# Business-rule validation
# ---------------------------------------------------------------------------

def validate_business_rules(df: pd.DataFrame) -> ValidationResult:
    """Validate domain-specific business rules."""
    total = len(df)
    issues: list[str] = []

    if "data_pagamento" in df.columns and "data_pedido" in df.columns:
        mask = df["data_pagamento"].notna() & df["data_pedido"].notna()
        count = int((df.loc[mask, "data_pagamento"] < df.loc[mask, "data_pedido"]).sum())
        if count > 0:
            pct = count / total * 100
            issues.append(
                f"data_pagamento anterior a data_pedido: {count} linhas ({pct:.2f}%)"
            )

    if "data_vencimento" in df.columns and "data_pedido" in df.columns:
        mask = df["data_vencimento"].notna() & df["data_pedido"].notna()
        count = int((df.loc[mask, "data_vencimento"] < df.loc[mask, "data_pedido"]).sum())
        if count > 0:
            pct = count / total * 100
            issues.append(
                f"data_vencimento anterior a data_pedido: {count} linhas ({pct:.2f}%)"
            )

    if "valor_parcela" in df.columns:
        count = int((df["valor_parcela"].dropna() <= 0).sum())
        if count > 0:
            pct = count / total * 100
            issues.append(f"valor_parcela <= 0: {count} linhas ({pct:.2f}%)")

    if "valor_pago" in df.columns:
        count = int((df["valor_pago"].dropna() < 0).sum())
        if count > 0:
            pct = count / total * 100
            issues.append(f"valor_pago < 0: {count} linhas ({pct:.2f}%)")

    return ValidationResult(
        stage="Regras de Negócio", passed=not issues, errors=issues
    )
