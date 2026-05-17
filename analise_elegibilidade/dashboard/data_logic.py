"""Filtros e agregações do Selects.txt em pandas (joins locais)."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import streamlit as st

from .dashboard_config import (
    DATA_FIM,
    DATA_INICIO,
    ESTOQUE_REF_CEDENTE,
    ESTOQUE_REF_SACADO,
    FUNDO_ID,
    LIMITE_CEDENTE_PCT,
    LIMITE_SACADO_PCT,
    MES_OPERADO_02_FIM,
    PL_FUNDO,
    VALOR_COL,
)
from .queries import (
    get_cedentes_periodo_query,
    get_classificacao_query,
    get_estoque_query,
    get_operacoes_query,
)

from shared.db import run_query

_EXCL_FOCO = {"INTB", "FM"}
_EXCL_PAPEL_GER_BASE = {
    "INTERCOMPANY",
    "CONTRATO",
    "NOTA COMERCIAL",
    "DS COMISSÁRIA",
    "DS DUPLICATA",
    "NOTA PROMISSÓRIA",
}
_EXCL_PAPEL_BASE = {
    "INTERCOMPANY",
    "CONTRATO",
    "NOTA COMERCIAL",
    "DS COMISSÁRIA",
    "DS DUPLICATA",
    "NOTA PROMISSÓRIA",
}
# Selects: papel_gerencial in ('DUPLICATA','COMISSÁRIA','PRE IMPRESSO')
# No dbt compat, Duplicata -> papel_gerencial 'Normal' (incluímos NORMAL + chaves de papel)
_INOVA_PAPEL_GER_KEYS = {"DUPLICATA", "COMISSARIA", "PRE IMPRESSO", "NORMAL"}
_INOVA_PAPEL_KEYS = {"DUPLICATA", "COMISSARIA", "PRE IMPRESSO"}
_NOTA_PROMISSORIA_KEY = "NOTA PROMISSORIA"


def _norm_text_key(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _norm_cnpj_key(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    digits = "".join(c for c in str(value) if c.isdigit())
    return digits.zfill(14) if digits else ""


def _to_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "t"})


def _papel_keys(labels: set[str]) -> set[str]:
    return {_norm_text_key(x) for x in labels}


# Exclusão completa de papéis (blocos Inova / empresas sem análise no Selects.txt)
_EXCL_PAPEL_STACK_COMPLETO = set(_EXCL_PAPEL_BASE)


def _enrich_operacoes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["gov_cedente_norm"] = out["gov_cedente"].map(_norm_cnpj_key)
    out["papel_key"] = out["papel"].map(_norm_text_key) if "papel" in out.columns else ""
    out["papel_gerencial_key"] = (
        out["papel_gerencial"].map(_norm_text_key) if "papel_gerencial" in out.columns else ""
    )
    out["papel_tratado_foco_key"] = (
        out["papel_tratado_foco"].map(_norm_text_key) if "papel_tratado_foco" in out.columns else ""
    )
    out["foco_key"] = out["foco"].map(_norm_text_key) if "foco" in out.columns else ""
    return out


_ENRICH_MARKERS = (
    "foco_key",
    "papel_key",
    "papel_gerencial_key",
    "papel_tratado_foco_key",
    "gov_cedente_norm",
)


def _ensure_enriched(df: pd.DataFrame) -> pd.DataFrame:
    """Garante colunas derivadas (cache antigo do Streamlit pode não tê-las)."""
    if all(c in df.columns for c in _ENRICH_MARKERS):
        return df
    work = _normalize_columns(df)
    for col in ("data_operacao", "data_vencimento", "mes_vencimento", "data_pagamento"):
        if col in work.columns and not pd.api.types.is_datetime64_any_dtype(work[col]):
            work[col] = pd.to_datetime(work[col], errors="coerce")
    if VALOR_COL in work.columns:
        work[VALOR_COL] = pd.to_numeric(work[VALOR_COL], errors="coerce").fillna(0)
    if "fundo" in work.columns:
        work["fundo"] = pd.to_numeric(work["fundo"], errors="coerce")
    return _enrich_operacoes(work)


@dataclass
class DataBundle:
    operacoes: pd.DataFrame
    empresas: pd.DataFrame
    estoque: pd.DataFrame


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Snowflake connector devolve colunas em maiúsculas."""
    out = df.copy()
    out.columns = [str(c).lower() for c in out.columns]
    return out


def _normalize_operacoes(df: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_columns(df)
    for col in ("data_operacao", "data_vencimento", "mes_vencimento", "data_pagamento"):
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    if VALOR_COL in out.columns:
        out[VALOR_COL] = pd.to_numeric(out[VALOR_COL], errors="coerce").fillna(0)
    if "fundo" in out.columns:
        out["fundo"] = pd.to_numeric(out["fundo"], errors="coerce")
    return _enrich_operacoes(out)


def _build_empresas(cedentes: pd.DataFrame, classificacao: pd.DataFrame) -> pd.DataFrame:
    ced = cedentes.copy()
    cla = classificacao.copy()
    ced["cnpj_cedente"] = ced["cnpj_cedente"].map(_norm_cnpj_key)
    cla["cnpj"] = cla["cnpj"].map(_norm_cnpj_key)
    emp = ced.merge(cla, left_on="cnpj_cedente", right_on="cnpj", how="left")
    if "cnpj" in emp.columns:
        emp = emp.drop(columns=["cnpj"])
    if "rj" in emp.columns:
        emp["rj"] = _to_bool_series(emp["rj"])
    if "status" in emp.columns:
        emp["status"] = emp["status"].astype(str).str.strip()
    return emp


@st.cache_data(ttl=300, show_spinner="Carregando dados…")
def load_data(_schema_version: int = 3) -> DataBundle:
    del _schema_version  # invalida cache ao mudar lógica de filtros
    operacoes = _normalize_operacoes(run_query(get_operacoes_query()))
    classificacao = _normalize_columns(run_query(get_classificacao_query()))
    cedentes = _normalize_columns(run_query(get_cedentes_periodo_query()))
    estoque = _normalize_columns(run_query(get_estoque_query()))
    empresas = _build_empresas(cedentes, classificacao)
    return DataBundle(operacoes=operacoes, empresas=empresas, estoque=estoque)


def _base_ops(ops: pd.DataFrame) -> pd.DataFrame:
    ops = _ensure_enriched(ops)
    mask = (
        (ops["data_operacao"] >= pd.Timestamp(DATA_INICIO))
        & (ops["data_operacao"] < pd.Timestamp(DATA_FIM))
        & (ops["fundo"] == FUNDO_ID)
    )
    return ops.loc[mask].copy()


def _mask_excl_intb_fm_intercompany(df: pd.DataFrame) -> pd.Series:
    return (
        df["foco_key"].isin(_EXCL_FOCO)
        | df["papel_tratado_foco_key"].isin(_EXCL_FOCO)
        | df["papel_key"].eq("INTERCOMPANY")
        | df["papel_gerencial_key"].eq("INTERCOMPANY")
    )


def _cnpj_rj(empresas: pd.DataFrame) -> set[str]:
    if empresas.empty or "rj" not in empresas.columns:
        return set()
    return set(empresas.loc[empresas["rj"], "cnpj_cedente"])


def _cnpj_analisar(empresas: pd.DataFrame) -> set[str]:
    if empresas.empty or "status" not in empresas.columns:
        return set()
    return set(empresas.loc[empresas["status"].str.lower() == "analisar", "cnpj_cedente"])


def _mask_papel_inova(df: pd.DataFrame) -> pd.Series:
    return df["papel_gerencial_key"].isin(_INOVA_PAPEL_GER_KEYS) | df["papel_key"].isin(
        _INOVA_PAPEL_KEYS
    )


def _not_excl_stack(df: pd.DataFrame, extra: set[str] | None = None) -> pd.DataFrame:
    """Exclui INTB/FM/INTERCOMPANY + papéis listados em extra (como no Selects por bloco).

    Não aplica a lista completa de papéis em todo filtro — senão CONTRATO/Serviços
    seriam excluídos antes do filtro de inclusão.
    """
    m = _mask_excl_intb_fm_intercompany(df)
    if extra:
        keys = _papel_keys(extra)
        m = m | df["papel_key"].isin(keys) | df["papel_gerencial_key"].isin(keys)
    return df.loc[~m]


def _match_papel(df: pd.DataFrame, *labels: str) -> pd.Series:
    keys = {_norm_text_key(l) for l in labels}
    return df["papel_key"].isin(keys) | df["papel_gerencial_key"].isin(keys)


def filter_fomento(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["papel_tratado_foco_key"].eq("FM")]


def filter_intercompany(df: pd.DataFrame) -> pd.DataFrame:
    m_fm = df["papel_tratado_foco_key"].eq("FM")
    m_ic = df["papel_tratado_foco_key"].eq("INTB") | df["papel_key"].eq("INTERCOMPANY")
    return df.loc[~m_fm & m_ic]


def filter_rj(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df)
    return base.loc[base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]


def filter_contrato(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df)
    base = base.loc[~base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]
    return base.loc[_match_papel(base, "CONTRATO")]


def filter_nota_comercial(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df, extra={"CONTRATO"})
    base = base.loc[~base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]
    return base.loc[_match_papel(base, "NOTA COMERCIAL")]


def filter_servicos(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df, extra={"CONTRATO", "NOTA COMERCIAL"})
    base = base.loc[~base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]
    return base.loc[_match_papel(base, "DS COMISSÁRIA", "DS DUPLICATA")]


def filter_nota_promissoria(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(
        df, extra={"CONTRATO", "NOTA COMERCIAL", "DS COMISSÁRIA", "DS DUPLICATA"}
    )
    base = base.loc[~base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]
    m_np = base["papel_key"].eq(_NOTA_PROMISSORIA_KEY) | base["papel_gerencial_key"].eq(
        _NOTA_PROMISSORIA_KEY
    )
    return base.loc[m_np]


def filter_empresas_sem_analise(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df, extra=_EXCL_PAPEL_STACK_COMPLETO)
    base = base.loc[~base["gov_cedente_norm"].isin(_cnpj_rj(empresas))]
    return base.loc[base["gov_cedente_norm"].isin(_cnpj_analisar(empresas))]


def filter_inova_disponiveis(df: pd.DataFrame, empresas: pd.DataFrame) -> pd.DataFrame:
    base = _not_excl_stack(df, extra=_EXCL_PAPEL_STACK_COMPLETO)
    excl = _cnpj_rj(empresas) | _cnpj_analisar(empresas)
    base = base.loc[~base["gov_cedente_norm"].isin(excl)]
    return base.loc[_mask_papel_inova(base)]


def sum_valor(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    return float(df[VALOR_COL].sum())


def _grupo_cedente_map(ops: pd.DataFrame) -> pd.Series:
    return ops.dropna(subset=["cedente_grupo"]).drop_duplicates("gov_cedente").set_index("gov_cedente")[
        "cedente_grupo"
    ]


def _grupo_sacado_map(ops: pd.DataFrame) -> pd.Series:
    return ops.dropna(subset=["sacado_grupo"]).drop_duplicates("gov_sacado").set_index("gov_sacado")[
        "sacado_grupo"
    ]


def build_analise_cedente(ops_inova: pd.DataFrame, estoque: pd.DataFrame, ops_all: pd.DataFrame) -> pd.DataFrame:
    grp_map = _grupo_cedente_map(ops_all)
    est = estoque.loc[estoque["ref_date"] == pd.Timestamp(ESTOQUE_REF_CEDENTE)].copy()
    est["grupo_cedente_tratado"] = est["nr_gov_id_cedent"].map(grp_map)
    expo = (
        est.dropna(subset=["grupo_cedente_tratado"])
        .groupby("grupo_cedente_tratado", as_index=False)["amt_present"]
        .sum()
        .rename(columns={"amt_present": "expo_fundo_inova_20260202"})
    )
    operado = (
        ops_inova.groupby("cedente_grupo", as_index=False)[VALOR_COL]
        .sum()
        .rename(columns={"cedente_grupo": "grupo_cedente_tratado", VALOR_COL: "valor_operado"})
    )
    out = operado.merge(expo, on="grupo_cedente_tratado", how="left")
    out["expo_fundo_inova_20260202"] = out["expo_fundo_inova_20260202"].fillna(0)
    out["nova_expo"] = out["valor_operado"] + out["expo_fundo_inova_20260202"]
    out["pl_fundo"] = PL_FUNDO
    out["limite"] = PL_FUNDO * LIMITE_CEDENTE_PCT
    out["classificacao"] = out.apply(
        lambda r: "OK" if r["limite"] >= r["nova_expo"] else "Analisar", axis=1
    )
    return out.sort_values("nova_expo", ascending=False)


def build_analise_sacado(ops_inova: pd.DataFrame, estoque: pd.DataFrame, ops_all: pd.DataFrame) -> pd.DataFrame:
    _cols = [
        "grupo_sacado_tratado",
        "valor_operado_02",
        "valor_operado_03",
        "expo_fundo_inova_20260202",
        "expo_fundo_inova_20260303",
        "expo_fundo_inova_202602",
        "expo_fundo_inova_202603",
        "nova_expo_all",
        "nova_expo_02",
        "nova_expo_03",
        "pl_fundo",
        "limite",
        "classificacao_all",
        "classificacao_02",
        "classificacao_03",
    ]
    if ops_inova.empty:
        return pd.DataFrame(columns=_cols)

    sac_map = _grupo_sacado_map(ops_all)
    d1, d2 = pd.Timestamp(DATA_INICIO), pd.Timestamp(MES_OPERADO_02_FIM)
    d3, d4 = pd.Timestamp(MES_OPERADO_02_FIM), pd.Timestamp(DATA_FIM)

    ops = ops_inova.copy()
    ops["_valor_02"] = np.where(
        (ops["data_operacao"] >= d1) & (ops["data_operacao"] < d2),
        ops[VALOR_COL],
        0.0,
    )
    ops["_valor_03"] = np.where(
        (ops["data_operacao"] >= d3) & (ops["data_operacao"] < d4),
        ops[VALOR_COL],
        0.0,
    )
    agg = (
        ops.groupby("sacado_grupo", as_index=False)
        .agg(valor_operado_02=("_valor_02", "sum"), valor_operado_03=("_valor_03", "sum"))
        .rename(columns={"sacado_grupo": "grupo_sacado_tratado"})
    )

    est = estoque.copy()
    est["ref_date"] = pd.to_datetime(est["ref_date"])
    est["grupo_sacado_tratado"] = est["nr_gov_id_debtor"].astype(str).map(sac_map)
    ref02, ref03 = pd.Timestamp(ESTOQUE_REF_SACADO[0]), pd.Timestamp(ESTOQUE_REF_SACADO[1])
    e02 = (
        est.loc[est["ref_date"] == ref02]
        .dropna(subset=["grupo_sacado_tratado"])
        .groupby("grupo_sacado_tratado", as_index=False)["amt_present"]
        .sum()
        .rename(columns={"amt_present": "expo_fundo_inova_20260202"})
    )
    e03 = (
        est.loc[est["ref_date"] == ref03]
        .dropna(subset=["grupo_sacado_tratado"])
        .groupby("grupo_sacado_tratado", as_index=False)["amt_present"]
        .sum()
        .rename(columns={"amt_present": "expo_fundo_inova_20260303"})
    )
    out = agg.merge(e02, on="grupo_sacado_tratado", how="left")
    out = out.merge(e03, on="grupo_sacado_tratado", how="left")
    for c in ("expo_fundo_inova_20260202", "expo_fundo_inova_20260303"):
        out[c] = out[c].fillna(0)
    out["expo_fundo_inova_202602"] = out["expo_fundo_inova_20260202"]
    out["expo_fundo_inova_202603"] = out["expo_fundo_inova_20260303"]
    out["nova_expo_all"] = (
        out["valor_operado_02"] + out["valor_operado_03"] + out["expo_fundo_inova_202602"]
    )
    out["nova_expo_02"] = out["valor_operado_02"] + out["expo_fundo_inova_202602"]
    out["nova_expo_03"] = out["valor_operado_03"] + out["expo_fundo_inova_202603"]
    out["pl_fundo"] = PL_FUNDO
    out["limite"] = PL_FUNDO * LIMITE_SACADO_PCT
    lim = out["limite"]
    out["classificacao_all"] = out["nova_expo_all"].le(lim).map({True: "OK", False: "Analisar"})
    out["classificacao_02"] = out["nova_expo_02"].le(lim).map({True: "OK", False: "Analisar"})
    out["classificacao_03"] = out["nova_expo_03"].le(lim).map({True: "OK", False: "Analisar"})
    return out.sort_values("nova_expo_all", ascending=False)


def build_operacoes_selecionadas(
    ops_inova: pd.DataFrame, analise_sacado: pd.DataFrame
) -> pd.DataFrame:
    lim_map = analise_sacado.set_index("grupo_sacado_tratado")
    analisar = lim_map.index[lim_map["classificacao_all"] == "Analisar"]
    cand = ops_inova.loc[ops_inova["sacado_grupo"].isin(analisar)].copy()
    if cand.empty:
        return ops_inova.iloc[0:0]

    cand["limite_disponivel"] = cand["sacado_grupo"].map(
        lim_map["limite"] - lim_map["expo_fundo_inova_20260202"]
    )
    cand = cand.sort_values(
        ["sacado_grupo", VALOR_COL, "data_operacao", "codigo_operacao"],
        ascending=[True, False, True, True],
    )
    cand["valor_acumulado_mes"] = cand.groupby("sacado_grupo")[VALOR_COL].cumsum()
    excedidas = cand.loc[cand["valor_acumulado_mes"] > cand["limite_disponivel"], ["codigo_operacao", "doc"]]
    if excedidas.empty:
        return ops_inova.sort_values(["sacado_grupo", "data_operacao", "codigo_operacao"])

    keys = set(zip(excedidas["codigo_operacao"], excedidas["doc"]))
    mask = ~ops_inova.apply(lambda r: (r["codigo_operacao"], r["doc"]) in keys, axis=1)
    return ops_inova.loc[mask].sort_values(["sacado_grupo", "data_operacao", "codigo_operacao"])


CATEGORY_FILTERS: list[tuple[str, Callable[..., pd.DataFrame]]] = [
    ("Operações de Fomento", filter_fomento),
    ("Operações de Intercompany", filter_intercompany),
    ("Operações de Empresas em RJ", filter_rj),
    ("Operações de Contrato", filter_contrato),
    ("Operações de Nota Comercial", filter_nota_comercial),
    ("Operações de Serviços", filter_servicos),
    ("Operações de Nota Promissória", filter_nota_promissoria),
    ("Operações de Empresas sem Análise", filter_empresas_sem_analise),
]
