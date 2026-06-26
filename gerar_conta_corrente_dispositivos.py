from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
import unicodedata
import warnings
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json"
OUTPUT_FILE = BASE_DIR / "CONTA_CORRENTE_DISPOSITIVOS_DATA.js"

DESTINO_ESTOQUE = "25d5c356-32a8-4221-84ae-8230061b9163"
FINALIDADE_SALDO_EST = "e8031b09-2d30-414d-af5b-16e43a41618b"

DEVICE_TYPES = ["ARES", "SHIELD", "SENSOR VTC", "SYOS"]
STATUS_LIST = [
    "DISPONIVEL_PARA_UTILIZAR",
    "AGUARDANDO_EXPEDICAO",
    "EM_ROTA_DE_ENTREGA",
    "ENTREGUE_AO_CLIENTE",
    "RETORNANDO",
    "MANUTENCAO",
    "CALIBRACAO",
    "FIXO_EM_VEICULO",
    "QUALIDADE",
    "EXTRAVIO",
    "SEM_MAPEAMENTO",
]
SOURCE_PRIORITY = {
    "vwTabelaMovDataloggers": 1,
    "tbddataloggerhistoricos": 2,
    "vtc_stage.documentos": 3,
    "planilha_fixos_veiculos": 4,
    "snapshots_reversa": 5,
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_accents(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    raw = str(value)
    raw = "".join(ch for ch in unicodedata.normalize("NFD", raw) if unicodedata.category(ch) != "Mn")
    return " ".join(raw.strip().upper().split())


def clean_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    text_value = str(value).strip()
    return text_value or None


def normalize_tag(value: Any) -> str | None:
    text_value = clean_value(value)
    if not text_value:
        return None
    tag = text_value.strip().upper()
    if tag in {"NAN", "NONE", "NULL", "00:00:00"}:
        return None
    return tag


def parse_dt(value: Any) -> pd.Timestamp | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    if getattr(ts, "tzinfo", None) is not None:
        ts = ts.tz_convert(None)
    return pd.Timestamp(ts).to_pydatetime().replace(microsecond=0)


def iso_dt(value: Any) -> str | None:
    dt = parse_dt(value)
    return dt.isoformat() if dt else None


def normalize_type(value: Any) -> str | None:
    norm = strip_accents(value)
    if not norm:
        return None
    if "ARES" in norm:
        return "ARES"
    if "SENSOR" in norm and "VTC" in norm:
        return "SENSOR VTC"
    if "SHIELD" in norm:
        return "SHIELD"
    if "SYOS" in norm:
        return "SYOS"
    return None


def hash_file(path: Path) -> dict[str, Any]:
    result = {"path": str(path), "sha256": None, "erro": None, "tamanho": None}
    try:
        h = hashlib.sha256()
        total = 0
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                h.update(chunk)
        result["sha256"] = h.hexdigest().upper()
        result["tamanho"] = total
    except Exception as exc:
        result["erro"] = str(exc)
    return result


def load_env_from_aura(aura_root: Path) -> None:
    env_utils = aura_root / "env_utils.py"
    if not env_utils.exists():
        raise RuntimeError(f"env_utils.py nao encontrado em {aura_root}")
    spec = importlib.util.spec_from_file_location("aura_env_utils_readonly", env_utils)
    if spec is None or spec.loader is None:
        raise RuntimeError("Falha ao carregar env_utils.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.load_env_file(aura_root / ".env")


def postgres_cfg(prefix: str = "AURA_POSTGRES") -> dict[str, Any]:
    cfg = {
        "host": os.getenv(f"{prefix}_HOST", ""),
        "port": int(os.getenv(f"{prefix}_PORT", "5432")),
        "database": os.getenv(f"{prefix}_NAME", ""),
        "user": os.getenv(f"{prefix}_USER", ""),
        "password": os.getenv(f"{prefix}_PASSWORD", ""),
    }
    missing = [key for key, value in cfg.items() if key != "port" and not value]
    if missing:
        raise RuntimeError(f"Variaveis {prefix}_* ausentes: " + ", ".join(missing))
    return cfg


def build_engine(cfg: dict[str, Any]):
    url = URL.create(
        "postgresql+psycopg2",
        username=cfg["user"],
        password=cfg["password"],
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 25})


def read_sql(engine, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def table_columns(engine, schema: str, table_name: str) -> set[str]:
    sql = """
    SELECT lower(column_name) AS column_name
    FROM information_schema.columns
    WHERE table_schema = :schema AND table_name = :table_name
    """
    df = read_sql(engine, sql, {"schema": schema, "table_name": table_name})
    return {str(row["column_name"]) for _, row in df.iterrows()}


def first_existing(columns: set[str], candidates: list[str]) -> str | None:
    for name in candidates:
        if name.lower() in columns:
            return name
    return None


def sql_expr(columns: set[str], candidates: list[str], alias: str, cast_text: bool = False) -> str:
    col = first_existing(columns, candidates)
    if not col:
        return f"NULL AS {alias}"
    if cast_text:
        return f"{col}::text AS {alias}"
    return f"{col} AS {alias}"


def query_current_positions(engine) -> pd.DataFrame:
    sql = """
    SELECT ped.cd_ufdestino,
           vwt.ds_tipodatalogger,
           vwt.ds_tag,
           vwt.ds_destino,
           vwt.ds_finalidade,
           vwt.ds_responsavel,
           vwt.id_usuarioatualizacao::text AS id_usuarioatualizacao,
           vwt.dt_atualizacao,
           vwt.ds_statusrecebimento
    FROM vwTabelaMovDataloggers vwt
    LEFT JOIN tbdsemembalagens emb ON vwt.cd_embalagem::text = emb.cd_embalagem::text
    LEFT JOIN vwimportacaopedidos ped ON emb.id_sem = ped.id_sem
    WHERE NULLIF(TRIM(vwt.ds_tag), '') IS NOT NULL
    """
    return read_sql(engine, sql)


def query_history_latest(engine) -> pd.DataFrame:
    sql = """
    SELECT DISTINCT ON (upper(trim(d.ds_tag)))
           upper(trim(d.ds_tag)) AS equipamento_id,
           d.ds_tag,
           d.ds_datalogger,
           dh.dt_inclusao,
           dh.tp_acaomovimentacao,
           tam.text AS ds_acaomovimentacao,
           dd.ds_destino,
           df.ds_finalidade,
           dh.nr_historico,
           dh.ds_observacao,
           (ui.ds_nome::text || ' ' || ui.ds_sobrenome::text) AS ds_usuarioinclusao
    FROM public.tbddataloggerhistoricos dh
    INNER JOIN vwtipos tam ON ds_tipo = 'tipoacaomovimentacao' AND dh.tp_acaomovimentacao = tam.id
    INNER JOIN public.tbdcaddataloggerdestinos dd ON dh.id_destino = dd.id_destino
    INNER JOIN public.tbdcaddataloggerfinalidades df ON dh.id_finalidade = df.id_finalidade
    INNER JOIN tbdcaddataloggers d ON dh.id_datalogger = d.id_datalogger
    LEFT JOIN vwusuarios ui ON dh.id_usuarioinclusao = ui.id_usuario
    WHERE NULLIF(TRIM(d.ds_tag), '') IS NOT NULL
    ORDER BY upper(trim(d.ds_tag)), dh.dt_inclusao DESC NULLS LAST
    """
    return read_sql(engine, sql)


def query_history_rollup(engine) -> pd.DataFrame:
    sql = """
    SELECT upper(trim(d.ds_tag)) AS equipamento_id,
           MAX(dh.dt_inclusao) AS data_ultima_movimentacao,
           MAX(CASE
                 WHEN dh.tp_acaomovimentacao IN (2, 12)
                  AND dh.id_destino = :destino_estoque
                  AND dh.id_finalidade = :finalidade_saldo
                 THEN dh.dt_inclusao
               END) AS data_ultimo_retorno,
           COUNT(*) AS qtd_movimentos
    FROM public.tbddataloggerhistoricos dh
    INNER JOIN tbdcaddataloggers d ON dh.id_datalogger = d.id_datalogger
    WHERE NULLIF(TRIM(d.ds_tag), '') IS NOT NULL
    GROUP BY upper(trim(d.ds_tag))
    """
    return read_sql(engine, sql, {"destino_estoque": DESTINO_ESTOQUE, "finalidade_saldo": FINALIDADE_SALDO_EST})


def query_history_indicators(engine) -> dict[str, Any]:
    sql = """
    SELECT
      COUNT(DISTINCT CASE
        WHEN dh.dt_inclusao >= CURRENT_DATE - INTERVAL '20 days'
         AND dh.tp_acaomovimentacao IN (2, 12)
         AND dh.id_destino = :destino_estoque
         AND dh.id_finalidade = :finalidade_saldo
        THEN upper(trim(d.ds_tag)) END) AS retornados_20d,
      COUNT(DISTINCT CASE
        WHEN dh.dt_inclusao >= CURRENT_DATE - INTERVAL '5 days'
        THEN upper(trim(d.ds_tag)) END) AS movimentacoes_5d,
      COUNT(DISTINCT CASE
        WHEN dh.dt_inclusao >= CURRENT_DATE - INTERVAL '20 days'
         AND upper(df.ds_finalidade) LIKE '%PACKING%'
        THEN upper(trim(d.ds_tag)) END) AS packing
    FROM public.tbddataloggerhistoricos dh
    INNER JOIN tbdcaddataloggers d ON dh.id_datalogger = d.id_datalogger
    INNER JOIN public.tbdcaddataloggerfinalidades df ON dh.id_finalidade = df.id_finalidade
    WHERE NULLIF(TRIM(d.ds_tag), '') IS NOT NULL
    """
    try:
        df = read_sql(engine, sql, {"destino_estoque": DESTINO_ESTOQUE, "finalidade_saldo": FINALIDADE_SALDO_EST})
    except Exception:
        return {"retornados_20d": None, "movimentacoes_5d": None, "packing": None}
    if df.empty:
        return {"retornados_20d": 0, "movimentacoes_5d": 0, "packing": 0}
    row = df.iloc[0].to_dict()
    return {key: int(row.get(key) or 0) for key in ["retornados_20d", "movimentacoes_5d", "packing"]}


def query_stage_documents(engine) -> pd.DataFrame:
    sql = """
    SELECT nr_pedido::text AS nr_pedido,
           ds_tag::text AS ds_tag,
           ds_tipo::text AS ds_tipo,
           dt_coletaefetiva,
           dt_entregaefetiva,
           imported_at,
           NULL::text AS destinatario,
           NULL::text AS uf_destino,
           NULL::text AS cidade_destino
    FROM vtc_stage.documentos
    WHERE NULLIF(TRIM(ds_tag), '') IS NOT NULL
    """
    return read_sql(engine, sql)


def classify_location(values: list[Any]) -> tuple[str | None, str | None]:
    bag = strip_accents(" ".join(str(v) for v in values if v is not None))
    checks = [
        ("CAMPINAS", "CAMPINAS", "FILIAL"),
        ("BSB", "BSB", "FILIAL"),
        ("GIG", "GIG", "FILIAL"),
        ("MG", "MG", "FILIAL"),
        ("GRU", "GRU", "ESTOQUE_CENTRAL"),
    ]
    for needle, loc, cls in checks:
        if needle in bag:
            return loc, cls
    return None, None


def classify_status(destino: Any, finalidade: Any, status_origem: Any, source: str) -> tuple[str, str, bool, str | None]:
    dest = strip_accents(destino)
    fin = strip_accents(finalidade)
    status = strip_accents(status_origem)
    bag = " | ".join([dest, fin, status])
    pendencia = "PENDENCIA" in bag
    if "FIXOS" in bag and ("VEICULO" in bag or "VEICULOS" in bag):
        return "FIXO_EM_VEICULO", "REGRA_FIXOS_VEICULOS", pendencia, None
    if "MANUTENCAO" in bag:
        return "MANUTENCAO", "REGRA_MANUTENCAO", pendencia, None
    if "CALIBRACAO" in bag:
        return "CALIBRACAO", "REGRA_CALIBRACAO", pendencia, None
    if "QUALIDADE" in bag or "CLIMATIZADO B" in bag:
        return "QUALIDADE", "REGRA_QUALIDADE", pendencia, None
    if "APTO AO USO" in bag:
        return "DISPONIVEL_PARA_UTILIZAR", "REGRA_CF_APTO_USO", pendencia, None
    if "AGUAR" in bag and "RECEBER" in bag:
        return "RETORNANDO", "REGRA_AGUARDANDO_RECEBIMENTO", pendencia, None
    if "RETORNANDO" in bag:
        return "RETORNANDO", "REGRA_RETORNANDO", pendencia, None
    if "CAMARA FRIA" in bag and "PACKING" in bag:
        return "AGUARDANDO_EXPEDICAO", "REGRA_CAMARA_FRIA_PACKING", pendencia, None
    if "TRANSPORTE" in bag or "EM ROTA" in bag:
        return "EM_ROTA_DE_ENTREGA", "REGRA_TRANSPORTE", pendencia, None
    if "ENTREGUE" in bag and source == "vtc_stage.documentos":
        return "ENTREGUE_AO_CLIENTE", "REGRA_STAGE_ENTREGA", pendencia, None
    if "EM ESTOQUE" in bag or "SALDO DE ESTOQUE" in bag or "ESTOQUE" in bag:
        return "DISPONIVEL_PARA_UTILIZAR", "REGRA_ESTOQUE", pendencia, None
    if "AGENTE" in bag:
        return "EM_ROTA_DE_ENTREGA", "REGRA_AGENTE", pendencia, None
    if pendencia:
        return "SEM_MAPEAMENTO", "REGRA_PENDENCIA_SEM_AGING", True, "PENDENCIA_OPERACIONAL_SEM_REGRA_CONFIAVEL"
    if "FORA DE OPERACAO" in bag:
        return "SEM_MAPEAMENTO", "REGRA_FORA_OPERACAO_SEM_SUBTIPO", pendencia, "FORA_OPERACAO_SEM_MANUTENCAO_OU_CALIBRACAO"
    return "SEM_MAPEAMENTO", "REGRA_STATUS_SEM_MAPEAMENTO", pendencia, "STATUS_ORIGEM_SEM_REGRA"


def candidate(
    equipamento_id: str,
    tag_original: Any,
    tipo: Any,
    source: str,
    status: str,
    status_origem: Any,
    date_value: Any,
    regra: str,
    **extra: Any,
) -> dict[str, Any]:
    data = iso_dt(date_value)
    return {
        "equipamento_id": equipamento_id,
        "tag_original": clean_value(tag_original) or equipamento_id,
        "tipo": normalize_type(tipo),
        "tipo_origem": clean_value(tipo),
        "fonte_status": source,
        "status_principal": status,
        "status_origem": clean_value(status_origem),
        "data_evento": data,
        "regra_aplicada": regra,
        "source_priority": SOURCE_PRIORITY.get(source, 99),
        **extra,
    }


def build_current_candidates(df: pd.DataFrame) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        tag = normalize_tag(row.get("ds_tag"))
        if not tag:
            continue
        status, regra, pendencia, motivo = classify_status(
            row.get("ds_destino"), row.get("ds_finalidade"), row.get("ds_statusrecebimento"), "vwTabelaMovDataloggers"
        )
        local, class_local = classify_location([
            row.get("ds_destino"), row.get("ds_finalidade"), row.get("ds_responsavel"), row.get("cd_ufdestino")
        ])
        responsabilidade = "CLIENTE" if status == "ENTREGUE_AO_CLIENTE" else "AGENTE"
        out.append(candidate(
            tag,
            row.get("ds_tag"),
            row.get("ds_tipodatalogger"),
            "vwTabelaMovDataloggers",
            status,
            " | ".join(filter(None, [clean_value(row.get("ds_destino")), clean_value(row.get("ds_finalidade")), clean_value(row.get("ds_statusrecebimento"))])),
            row.get("dt_atualizacao"),
            regra,
            responsabilidade=responsabilidade,
            localizacao=local,
            classificacao_local=class_local,
            destino=clean_value(row.get("ds_destino")),
            finalidade=clean_value(row.get("ds_finalidade")),
            responsavel=clean_value(row.get("ds_responsavel")) or clean_value(row.get("id_usuarioatualizacao")),
            pedido_atual=None,
            veiculo=None,
            placa=None,
            pendencia_operacional=pendencia,
            motivo_sem_mapeamento=motivo,
        ))
    return out


def build_history_candidates(df: pd.DataFrame) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        tag = normalize_tag(row.get("equipamento_id") or row.get("ds_tag"))
        if not tag:
            continue
        status, regra, pendencia, motivo = classify_status(
            row.get("ds_destino"), row.get("ds_finalidade"), row.get("ds_acaomovimentacao"), "tbddataloggerhistoricos"
        )
        if int(row.get("tp_acaomovimentacao") or 0) in {2, 12}:
            status = "SEM_MAPEAMENTO"
            regra = "REGRA_RETORNO_HISTORICO_NAO_DEFINE_POSICAO_ATUAL"
            motivo = "RETORNO_SEM_POSICAO_ATUAL_POSTERIOR"
        local, class_local = classify_location([row.get("ds_destino"), row.get("ds_finalidade"), row.get("ds_observacao")])
        out.append(candidate(
            tag,
            row.get("ds_tag"),
            row.get("ds_datalogger"),
            "tbddataloggerhistoricos",
            status,
            " | ".join(filter(None, [clean_value(row.get("ds_destino")), clean_value(row.get("ds_finalidade")), clean_value(row.get("ds_acaomovimentacao"))])),
            row.get("dt_inclusao"),
            regra,
            responsabilidade="AGENTE",
            localizacao=local,
            classificacao_local=class_local,
            destino=clean_value(row.get("ds_destino")),
            finalidade=clean_value(row.get("ds_finalidade")),
            responsavel=clean_value(row.get("ds_usuarioinclusao")),
            pedido_atual=None,
            veiculo=None,
            placa=None,
            pendencia_operacional=pendencia,
            motivo_sem_mapeamento=motivo,
        ))
    return out


def build_stage_candidates(df: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if df.empty:
        return [], {"entregues_20d": 0, "expedicoes_recentes": 0}
    work = df.copy()
    work["equipamento_id"] = work["ds_tag"].map(normalize_tag)
    for col in ["dt_coletaefetiva", "dt_entregaefetiva", "imported_at"]:
        work[col] = pd.to_datetime(work[col], errors="coerce", utc=True).dt.tz_convert(None)
    work = work[work["equipamento_id"].notna()].copy()
    if work.empty:
        return [], {"entregues_20d": 0, "expedicoes_recentes": 0}
    work["_data_evento"] = work[["dt_entregaefetiva", "dt_coletaefetiva", "imported_at"]].max(axis=1)
    latest = work.sort_values(["equipamento_id", "_data_evento"], ascending=[True, False]).drop_duplicates("equipamento_id")
    out: list[dict[str, Any]] = []
    for _, row in latest.iterrows():
        entregue = pd.notna(row.get("dt_entregaefetiva"))
        coletado = pd.notna(row.get("dt_coletaefetiva"))
        if entregue:
            status = "ENTREGUE_AO_CLIENTE"
            regra = "REGRA_STAGE_ENTREGA_CONCLUIDA"
            responsabilidade = "CLIENTE"
            date_value = row.get("dt_entregaefetiva")
        elif coletado:
            status = "EM_ROTA_DE_ENTREGA"
            regra = "REGRA_STAGE_COLETA_SEM_ENTREGA"
            responsabilidade = "AGENTE"
            date_value = row.get("dt_coletaefetiva")
        else:
            status = "SEM_MAPEAMENTO"
            regra = "REGRA_STAGE_SEM_DATAS_OPERACIONAIS"
            responsabilidade = None
            date_value = row.get("imported_at")
        local, class_local = classify_location([row.get("uf_destino"), row.get("cidade_destino"), row.get("destinatario")])
        out.append(candidate(
            row["equipamento_id"],
            row.get("ds_tag"),
            row.get("ds_tipo"),
            "vtc_stage.documentos",
            status,
            "ENTREGA" if entregue else ("COLETA" if coletado else None),
            date_value,
            regra,
            responsabilidade=responsabilidade,
            localizacao=local,
            classificacao_local=class_local,
            destino=clean_value(row.get("destinatario")),
            finalidade=None,
            responsavel=clean_value(row.get("destinatario")),
            pedido_atual=clean_value(row.get("nr_pedido")),
            veiculo=None,
            placa=None,
            pendencia_operacional=False,
            motivo_sem_mapeamento="STAGE_SEM_DATAS_OPERACIONAIS" if status == "SEM_MAPEAMENTO" else None,
        ))
    cutoff20 = pd.Timestamp.now().normalize() - pd.Timedelta(days=20)
    cutoff5 = pd.Timestamp.now().normalize() - pd.Timedelta(days=5)
    indicadores = {
        "entregues_20d": int(work.loc[work["dt_entregaefetiva"].ge(cutoff20), "equipamento_id"].nunique()),
        "expedicoes_recentes": int(work.loc[work["dt_coletaefetiva"].ge(cutoff5), "equipamento_id"].nunique()),
    }
    return out, indicadores


def read_fixed_vehicle_sheet(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta = config["planilha_fixos_veiculos"]
    path = Path(meta["caminho"])
    info: dict[str, Any] = {
        "caminho": str(path),
        "nome_arquivo": path.name,
        "existe": path.exists(),
        "data_leitura": now_iso(),
        "abas": [],
        "colunas_identificadas": [],
        "linhas_lidas": 0,
        "tags_identificadas": 0,
        "linhas_sem_tag_suficiente": 0,
        "erro": None,
    }
    if not path.exists():
        info["erro"] = "Planilha auxiliar nao encontrada"
        return [], info
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            xl = pd.ExcelFile(path)
            info["abas"] = xl.sheet_names
            sheet = meta.get("aba_preferencial") if meta.get("aba_preferencial") in xl.sheet_names else xl.sheet_names[0]
            df = pd.read_excel(path, sheet_name=sheet)
    except Exception as exc:
        info["erro"] = str(exc)
        return [], info
    if df.empty:
        return [], info
    info["linhas_lidas"] = int(len(df))
    info["colunas_identificadas"] = [str(c) for c in df.columns]
    norm_cols = {strip_accents(c): c for c in df.columns}
    tag_cols = [col for key, col in norm_cols.items() if re.fullmatch(r"LOGGER\s*\d+", key) or re.fullmatch(r"SENSORWEB\s*\d+", key)]
    date_cols = [col for key, col in norm_cols.items() if "ULTIMA CONFIGURACAO" in key or "DATA ATUAL" in key or "DATA DE INSTALACAO" in key]
    out: list[dict[str, Any]] = []
    rows_without_tag = 0
    for _, row in df.iterrows():
        row_tags = [normalize_tag(row.get(col)) for col in tag_cols]
        row_tags = [tag for tag in row_tags if tag]
        if not row_tags:
            rows_without_tag += 1
            continue
        dates = [parse_dt(row.get(col)) for col in date_cols]
        dates = [dt for dt in dates if dt is not None]
        data_evento = max(dates) if dates else None
        for tag in row_tags:
            out.append(candidate(
                tag,
                tag,
                None,
                "planilha_fixos_veiculos",
                "FIXO_EM_VEICULO",
                clean_value(row.get(norm_cols.get("STATUS", ""))),
                data_evento,
                "REGRA_PLANILHA_FIXOS_VEICULOS",
                responsabilidade="AGENTE",
                localizacao=clean_value(row.get(norm_cols.get("EMPRESA", ""))),
                classificacao_local="FIXO_EM_VEICULO",
                destino=clean_value(row.get(norm_cols.get("DESCRICAO", ""))),
                finalidade="FIXOS - VEICULOS",
                responsavel=clean_value(row.get(norm_cols.get("MOTORISTA", ""))),
                pedido_atual=None,
                veiculo=clean_value(row.get(norm_cols.get("DESCRICAO", ""))),
                placa=clean_value(row.get(norm_cols.get("PLACA", ""))),
                pendencia_operacional="PENDENCIA" in strip_accents(row.get(norm_cols.get("CHECK PENDENCIA", ""))),
                motivo_sem_mapeamento=None,
            ))
    info["tags_identificadas"] = len({c["equipamento_id"] for c in out})
    info["linhas_sem_tag_suficiente"] = rows_without_tag
    return out, info


def build_final_records(
    candidates: list[dict[str, Any]],
    history_rollup: pd.DataFrame,
    stage_df: pd.DataFrame,
    generated_at: str,
    limite_extravio: int,
) -> list[dict[str, Any]]:
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        by_tag[item["equipamento_id"]].append(item)

    type_by_tag: dict[str, str] = {}
    for item in candidates:
        if item.get("tipo"):
            type_by_tag.setdefault(item["equipamento_id"], item["tipo"])

    hist_dates = {}
    ret_dates = {}
    for _, row in history_rollup.iterrows():
        tag = normalize_tag(row.get("equipamento_id"))
        if tag:
            hist_dates[tag] = iso_dt(row.get("data_ultima_movimentacao"))
            ret_dates[tag] = iso_dt(row.get("data_ultimo_retorno"))

    delivery_dates: dict[str, str | None] = {}
    if not stage_df.empty:
        st = stage_df.copy()
        st["equipamento_id"] = st["ds_tag"].map(normalize_tag)
        st["dt_entregaefetiva"] = pd.to_datetime(st["dt_entregaefetiva"], errors="coerce", utc=True).dt.tz_convert(None)
        grouped = st[st["equipamento_id"].notna()].groupby("equipamento_id")["dt_entregaefetiva"].max()
        delivery_dates = {tag: iso_dt(val) for tag, val in grouped.items()}

    final: list[dict[str, Any]] = []
    today = pd.Timestamp.now().normalize()
    for tag, rows in by_tag.items():
        def sort_key(item: dict[str, Any]):
            dt = parse_dt(item.get("data_evento"))
            date_score = dt.timestamp() if dt else -1
            return (date_score, -int(item.get("source_priority") or 99))

        ordered = sorted(rows, key=sort_key, reverse=True)
        winner = dict(ordered[0])
        if not winner.get("tipo"):
            winner["tipo"] = type_by_tag.get(tag)
        status_values = {r.get("status_principal") for r in ordered if r.get("status_principal")}
        winner_dt = parse_dt(winner.get("data_evento"))
        conflict = False
        if len(status_values) > 1 and winner_dt is not None:
            for loser in ordered[1:]:
                loser_dt = parse_dt(loser.get("data_evento"))
                if loser_dt and abs((winner_dt - loser_dt).days) <= 2 and loser.get("status_principal") != winner.get("status_principal"):
                    conflict = True
                    break

        last_candidates = [parse_dt(winner.get("data_evento")), parse_dt(hist_dates.get(tag))]
        last_movement = max([dt for dt in last_candidates if dt is not None], default=None)
        last_delivery = delivery_dates.get(tag)
        last_return = ret_dates.get(tag)
        situacao_retorno = None
        dias_sem_retorno = None
        faixa = None
        delivery_dt = parse_dt(last_delivery)
        return_dt = parse_dt(last_return)
        if delivery_dt and return_dt and return_dt > delivery_dt:
            situacao_retorno = "RETORNADO"
        elif delivery_dt and (not return_dt or return_dt <= delivery_dt):
            dias_sem_retorno = int((today - pd.Timestamp(delivery_dt).normalize()).days)
            if dias_sem_retorno <= 30:
                faixa = "ATE_30"
            elif dias_sem_retorno <= 60:
                faixa = "31_60"
            elif dias_sem_retorno <= 90:
                faixa = "61_90"
            elif dias_sem_retorno <= limite_extravio:
                faixa = "91_180"

        if winner.get("status_principal") == "RETORNANDO":
            situacao_retorno = "RETORNANDO"

        if last_movement and winner.get("status_principal") not in {"MANUTENCAO", "CALIBRACAO"}:
            dias_sem_mov = int((today - pd.Timestamp(last_movement).normalize()).days)
            if dias_sem_mov > limite_extravio:
                winner["status_principal"] = "EXTRAVIO"
                winner["regra_aplicada"] = "REGRA_EXTRAVIO_MAIS_DE_180_DIAS_SEM_MOVIMENTACAO"
                winner["motivo_sem_mapeamento"] = None
                faixa = None

        record = {
            "equipamento_id": tag,
            "tag_original": winner.get("tag_original"),
            "tipo": winner.get("tipo"),
            "tipo_origem": winner.get("tipo_origem"),
            "status_principal": winner.get("status_principal"),
            "status_origem": winner.get("status_origem"),
            "responsabilidade": winner.get("responsabilidade"),
            "localizacao": winner.get("localizacao"),
            "classificacao_local": winner.get("classificacao_local"),
            "destino": winner.get("destino"),
            "finalidade": winner.get("finalidade"),
            "responsavel": winner.get("responsavel"),
            "pedido_atual": winner.get("pedido_atual"),
            "veiculo": winner.get("veiculo"),
            "placa": winner.get("placa"),
            "situacao_retorno": situacao_retorno,
            "pendencia_operacional": bool(winner.get("pendencia_operacional")),
            "data_ultima_movimentacao": iso_dt(last_movement) or winner.get("data_evento"),
            "data_ultima_entrega": last_delivery,
            "data_ultimo_retorno": last_return,
            "dias_sem_retorno": dias_sem_retorno if winner.get("status_principal") != "EXTRAVIO" else None,
            "faixa_sem_retorno": faixa if winner.get("status_principal") != "EXTRAVIO" else None,
            "fonte_status": winner.get("fonte_status"),
            "data_carga": generated_at,
            "regra_aplicada": winner.get("regra_aplicada"),
            "possui_conflito": conflict,
            "motivo_sem_mapeamento": winner.get("motivo_sem_mapeamento") if winner.get("status_principal") == "SEM_MAPEAMENTO" else None,
            "status_candidatos": [
                {
                    "fonte": item.get("fonte_status"),
                    "status_principal": item.get("status_principal"),
                    "status_origem": item.get("status_origem"),
                    "data_evento": item.get("data_evento"),
                    "regra_aplicada": item.get("regra_aplicada"),
                }
                for item in ordered
            ],
            "fontes_encontradas": sorted({item.get("fonte_status") for item in ordered if item.get("fonte_status")}),
        }
        final.append(record)
    final.sort(key=lambda x: (x.get("tipo") or "ZZZ", x["equipamento_id"]))
    return final


def summarize(records: list[dict[str, Any]], config: dict[str, Any], fixed_info: dict[str, Any], indicators: dict[str, Any]) -> dict[str, Any]:
    by_type: dict[str, dict[str, Any]] = {}
    for dtype in DEVICE_TYPES:
        rows = [r for r in records if r.get("tipo") == dtype]
        c_status = Counter(r["status_principal"] for r in rows)
        by_type[dtype] = {
            "tipo": dtype,
            "total_sistemico_tags_unicas": len(rows),
            "quantidade_classificada": len([r for r in rows if r.get("status_principal") != "SEM_MAPEAMENTO"]),
            "quantidade_sem_mapeamento": c_status.get("SEM_MAPEAMENTO", 0),
            "ultima_atualizacao": max([r.get("data_ultima_movimentacao") for r in rows if r.get("data_ultima_movimentacao")], default=None),
            "por_status": {status: c_status.get(status, 0) for status in STATUS_LIST},
            "retornados": len([r for r in rows if r.get("situacao_retorno") == "RETORNADO"]),
            "fora_operacao": c_status.get("MANUTENCAO", 0) + c_status.get("CALIBRACAO", 0),
        }
        if dtype == "SHIELD":
            expected = config.get("diagnosticos", {}).get("shield_total_esperado")
            by_type[dtype]["diagnostico_total_esperado"] = expected
            by_type[dtype]["alerta_diagnostico"] = (
                f"Total sistemico SHIELD diferente da referencia diagnostica {expected}"
                if expected is not None and len(rows) != int(expected)
                else None
            )

    resumo_status = Counter(r["status_principal"] for r in records)
    resumo_local = Counter(r.get("localizacao") or "SEM_LOCALIZACAO" for r in records)
    resumo_class_local = Counter(r.get("classificacao_local") or "SEM_CLASSIFICACAO" for r in records)
    resumo_resp = Counter(r.get("responsabilidade") or "SEM_RESPONSABILIDADE" for r in records)
    faixas = Counter(r.get("faixa_sem_retorno") for r in records if r.get("faixa_sem_retorno"))
    return {
        "resumoPorTipo": by_type,
        "resumoPorStatus": {status: resumo_status.get(status, 0) for status in STATUS_LIST},
        "resumoPorLocalizacao": dict(sorted(resumo_local.items())),
        "resumoPorClassificacaoLocal": dict(sorted(resumo_class_local.items())),
        "resumoPorResponsabilidade": dict(sorted(resumo_resp.items())),
        "resumoFixosVeiculos": {
            "sistemico_conciliado_por_tag": resumo_status.get("FIXO_EM_VEICULO", 0),
            "planilha_tags_identificadas": fixed_info.get("tags_identificadas"),
            "planilha_linhas_lidas": fixed_info.get("linhas_lidas"),
            "planilha_linhas_sem_tag_suficiente": fixed_info.get("linhas_sem_tag_suficiente"),
        },
        "faixasNaoRetorno": {item["codigo"]: faixas.get(item["codigo"], 0) for item in config.get("faixas_nao_retorno", [])},
        "indicadoresOperacionais": indicators,
    }


def main() -> int:
    generated_at = now_iso()
    config = load_json(CONFIG_FILE)
    aura_root = Path(config["aura_root_leitura"])
    protected_paths = [
        aura_root / "GESTAO_DISPOSITIVOS.html",
        aura_root / "GESTAO_DISPOSITIVOS_STAGE_DATA.js",
        aura_root / "ESTOQUE_DATALOGGERS.html",
        aura_root / "ATUALIZAR_TUDO_10_MIN.ps1",
        BASE_DIR / "controle de loggers fixos dos veículos - atualizado.xlsx",
    ]
    hashes_before = [hash_file(path) for path in protected_paths]

    print("Plano tecnico - Conta Corrente de Dispositivos")
    print(f"- Pasta de saida: {BASE_DIR}")
    print(f"- Pacote Aura original: somente leitura em {aura_root}")
    print("- Dados manuais de ARES: exibidos separados, sem somar ao total sistemico")
    print("- Planilha de fixos: lida como fonte auxiliar, sem alterar/mover/copiar linhas para codigo")
    print("- Sem deploy, commit, push, alteracao de banco ou automacao")

    load_env_from_aura(aura_root)
    portal_engine = build_engine(postgres_cfg("AURA_POSTGRES"))
    stage_engine = build_engine(postgres_cfg("AURA_DB"))

    try:
        df_current = query_current_positions(portal_engine)
        df_hist_latest = query_history_latest(portal_engine)
        df_hist_rollup = query_history_rollup(portal_engine)
        hist_indicators = query_history_indicators(portal_engine)
        df_stage = query_stage_documents(stage_engine)
    except Exception as exc:
        print(f"ERRO: fonte sistemica obrigatoria falhou: {exc}", file=sys.stderr)
        return 1

    fixed_candidates, fixed_info = read_fixed_vehicle_sheet(config)
    candidates = []
    candidates.extend(build_current_candidates(df_current))
    candidates.extend(build_history_candidates(df_hist_latest))
    stage_candidates, stage_indicators = build_stage_candidates(df_stage)
    candidates.extend(stage_candidates)
    candidates.extend(fixed_candidates)

    if not candidates:
        print("ERRO: nenhuma tag candidata foi encontrada nas fontes obrigatorias.", file=sys.stderr)
        return 1

    records = build_final_records(
        candidates,
        df_hist_rollup,
        df_stage,
        generated_at,
        int(config.get("limite_extravio_dias", 180)),
    )
    indicators = {
        "entregues_ultimos_20_dias": stage_indicators.get("entregues_20d"),
        "retornados_ultimos_20_dias": hist_indicators.get("retornados_20d"),
        "pendencias_operacionais": len([r for r in records if r.get("pendencia_operacional")]),
        "movimentacoes_ultimos_5_dias": hist_indicators.get("movimentacoes_5d"),
        "packing": hist_indicators.get("packing"),
        "recebimentos_recentes": hist_indicators.get("retornados_20d"),
        "expedicoes_recentes": stage_indicators.get("expedicoes_recentes"),
        "observacao": "Indicadores de movimentacao nao compoem a conta corrente.",
    }
    resumo = summarize(records, config, fixed_info, indicators)
    hashes_after = [hash_file(path) for path in protected_paths]
    qualidade = {
        "tags_invalidas_excluidas": 0,
        "registros_sem_data": len([r for r in records if not r.get("data_ultima_movimentacao")]),
        "registros_sem_tipo": len([r for r in records if not r.get("tipo")]),
        "registros_sem_mapeamento": len([r for r in records if r.get("status_principal") == "SEM_MAPEAMENTO"]),
        "conflitos": len([r for r in records if r.get("possui_conflito")]),
        "planilha_fixos_veiculos": fixed_info,
    }
    data = {
        "snapshotValido": True,
        "generatedAt": generated_at,
        "fontes": [
            {"nome": "vwTabelaMovDataloggers", "tipo": "sistemica", "linhas_lidas": int(len(df_current))},
            {"nome": "tbddataloggerhistoricos", "tipo": "sistemica", "linhas_lidas_latest": int(len(df_hist_latest)), "linhas_rollup": int(len(df_hist_rollup))},
            {"nome": "vtc_stage.documentos", "tipo": "sistemica", "linhas_lidas": int(len(df_stage))},
            {"nome": "planilha_fixos_veiculos", "tipo": "auxiliar", **fixed_info},
        ],
        "registros": records,
        **resumo,
        "qualidade": qualidade,
        "posicaoManualAres": config.get("posicao_manual_ares", []),
        "premissasAplicadas": [
            "equipamento_id = upper(trim(tag))",
            "ARES e ARES COM SONDA consolidados no tipo ARES",
            "Dados manuais de ARES nao compoem totais sistemicos",
            "Retornados sao subindicador e nao duplicam status principal",
            "Indicadores operacionais ficam fora da conta corrente",
            "Extravio aplicado somente acima de 180 dias sem movimentacao valida, exceto manutencao/calibracao",
        ],
        "hashesProtegidos": {
            "antes": hashes_before,
            "depois": hashes_after,
        },
        "arquivosCriadosEsperados": [
            "CONTA_CORRENTE_DISPOSITIVOS.html",
            "CONTA_CORRENTE_DISPOSITIVOS_DATA.js",
            "CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json",
            "gerar_conta_corrente_dispositivos.py",
            "validar_conta_corrente_dispositivos.py",
            "RELATORIO_VALIDACAO_CONTA_CORRENTE.md",
        ],
        "confirmacoes": {
            "deploy": False,
            "commit": False,
            "push": False,
            "alteracao_banco": False,
            "alteracao_pacote_aura_original": False,
        },
    }
    payload = json.dumps(data, ensure_ascii=True, indent=2, default=str)
    OUTPUT_FILE.write_text("window.CONTA_CORRENTE_DISPOSITIVOS_DATA = " + payload + ";\n", encoding="utf-8")
    print(f"Snapshot gerado: {OUTPUT_FILE}")
    print(f"Tags unicas: {len(records)}")
    print("Totais por tipo: " + ", ".join(f"{k}={v['total_sistemico_tags_unicas']}" for k, v in resumo["resumoPorTipo"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
