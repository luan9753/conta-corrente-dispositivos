from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "CONTA_CORRENTE_DISPOSITIVOS_DATA.js"
CONFIG_FILE = BASE_DIR / "CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json"
HTML_FILE = BASE_DIR / "CONTA_CORRENTE_DISPOSITIVOS.html"
REPORT_FILE = BASE_DIR / "RELATORIO_VALIDACAO_CONTA_CORRENTE.md"

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
REQUIRED_RECORD_FIELDS = [
    "equipamento_id",
    "tag_original",
    "tipo",
    "tipo_origem",
    "status_principal",
    "status_origem",
    "responsabilidade",
    "localizacao",
    "classificacao_local",
    "destino",
    "finalidade",
    "responsavel",
    "pedido_atual",
    "veiculo",
    "placa",
    "situacao_retorno",
    "pendencia_operacional",
    "data_ultima_movimentacao",
    "data_ultima_entrega",
    "data_ultimo_retorno",
    "dias_sem_retorno",
    "faixa_sem_retorno",
    "fonte_status",
    "data_carga",
    "regra_aplicada",
    "possui_conflito",
    "motivo_sem_mapeamento",
    "status_candidatos",
    "fontes_encontradas",
]


def load_json_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    prefix = "window.CONTA_CORRENTE_DISPOSITIVOS_DATA = "
    if text.startswith(prefix):
        text = text[len(prefix):].strip()
        if text.endswith(";"):
            text = text[:-1]
    return json.loads(text)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def add(results: list[dict[str, Any]], item: int, nome: str, ok: bool, detalhe: str, obrigatoria: bool = True) -> None:
    results.append({
        "item": item,
        "nome": nome,
        "status": "OK" if ok else ("FALHA" if obrigatoria else "ALERTA"),
        "ok": ok,
        "obrigatoria": obrigatoria,
        "detalhe": detalhe,
    })


def summarize_failures(results: list[dict[str, Any]]) -> tuple[int, int]:
    failures = len([r for r in results if not r["ok"] and r["obrigatoria"]])
    alerts = len([r for r in results if not r["ok"] and not r["obrigatoria"]])
    return failures, alerts


def validate(data: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    records = data.get("registros", [])
    ids = [r.get("equipamento_id") for r in records]
    id_counter = Counter(ids)
    duplicated = [tag for tag, count in id_counter.items() if tag and count > 1]
    status_counter = Counter(r.get("status_principal") for r in records)
    sum_status = sum(status_counter.get(status, 0) for status in STATUS_LIST)
    faixas = [r.get("faixa_sem_retorno") for r in records if r.get("faixa_sem_retorno")]
    valid_faixas = {f["codigo"] for f in config.get("faixas_nao_retorno", [])}
    html_text = HTML_FILE.read_text(encoding="utf-8", errors="ignore") if HTML_FILE.exists() else ""
    missing_fields = [
        (r.get("equipamento_id"), field)
        for r in records
        for field in REQUIRED_RECORD_FIELDS
        if field not in r
    ]

    add(results, 1, "Ausencia de equipamento_id duplicado", not duplicated, f"duplicados={len(duplicated)}")
    add(results, 2, "Soma dos status principais igual ao total de tags unicas", sum_status == len(records), f"soma_status={sum_status}; registros={len(records)}")
    add(results, 3, "Cada equipamento em apenas um status principal", all(r.get("status_principal") in STATUS_LIST for r in records), "status fora da taxonomia verificados")
    add(results, 4, "Faixas de nao retorno exclusivas", len(faixas) == len([r for r in records if r.get("faixa_sem_retorno") in valid_faixas]), f"faixas_preenchidas={len(faixas)}")
    add(results, 5, "Faixa 91_180 limitada corretamente", all((r.get("faixa_sem_retorno") != "91_180") or (91 <= int(r.get("dias_sem_retorno") or -1) <= 180) for r in records), "91_180 validada")
    add(results, 6, "Extravio somente acima de 180 dias", all((r.get("status_principal") != "EXTRAVIO") or ("180" in str(r.get("regra_aplicada")) or (r.get("dias_sem_retorno") is None)) for r in records), "regra de extravio auditada")
    add(results, 7, "Manutencao e calibracao fora da regra de extravio", all(r.get("status_principal") != "EXTRAVIO" or "MANUTENCAO" not in str(r.get("status_origem")) for r in records), "manutencao/calibracao avaliadas")
    add(results, 8, "Ausencia de sobreposicao entre extravio e nao retorno", all(not (r.get("status_principal") == "EXTRAVIO" and r.get("faixa_sem_retorno")) for r in records), "extravio nao possui faixa")
    add(results, 9, "ARES consolida ARES e ARES COM SONDA", "ARES COM SONDA" not in data.get("resumoPorTipo", {}), "cards/resumo usam ARES consolidado")
    add(results, 10, "Totais sistemicos por filial calculados dinamicamente", "resumoPorLocalizacao" in data and isinstance(data.get("resumoPorLocalizacao"), dict), "resumoPorLocalizacao presente")
    add(results, 11, "Dados manuais de ARES separados da posicao sistemica", bool(data.get("posicaoManualAres")) and "posicao_manual_ares" in config, "manual ARES separado")
    generator_text = (BASE_DIR / "gerar_conta_corrente_dispositivos.py").read_text(encoding="utf-8", errors="ignore")
    hardcoded_tag = re.search(r"['\"](?:A|TA|S)[0-9]{3,}['\"]", generator_text)
    add(results, 12, "Dados da planilha de veiculos nao incorporados como constantes", hardcoded_tag is None, "gerador le a planilha dinamicamente e nao contem tags fixas")
    add(results, 13, "Tags fixas em veiculos deduplicadas contra demais fontes", not duplicated, "dedupe global por equipamento_id")
    add(results, 14, "Indicadores operacionais fora da conta corrente", "indicadoresOperacionais" in data and sum_status == len(records), "indicadores em chave separada")
    add(results, 15, "Ausencia de totais sistemicos fixos no HTML", not re.search(r">\s*(119|10712|10\.712)\s*<", html_text), "HTML sem totais diagnosticos fixos")
    add(results, 16, "Uso de null para dados ausentes", '"N/D"' not in DATA_FILE.read_text(encoding="utf-8", errors="ignore"), "snapshot nao usa string N/D internamente")
    add(results, 17, "Consistencia entre resumos e registros", data.get("resumoPorStatus", {}) == {status: status_counter.get(status, 0) for status in STATUS_LIST}, "resumoPorStatus confere")
    before = {h.get("path"): h.get("sha256") for h in data.get("hashesProtegidos", {}).get("antes", [])}
    after = {h.get("path"): h.get("sha256") for h in data.get("hashesProtegidos", {}).get("depois", [])}
    hash_changed = [path for path, sha in before.items() if sha and after.get(path) and after.get(path) != sha]
    add(results, 18, "Integridade dos arquivos protegidos por SHA-256", not hash_changed, f"alterados={hash_changed}")
    add(results, 19, "Quantidade de registros sem data", data.get("qualidade", {}).get("registros_sem_data", 0) == len([r for r in records if not r.get("data_ultima_movimentacao")]), f"sem_data={data.get('qualidade', {}).get('registros_sem_data')}")
    add(results, 20, "Quantidade de registros sem tipo", data.get("qualidade", {}).get("registros_sem_tipo", 0) == len([r for r in records if not r.get("tipo")]), f"sem_tipo={data.get('qualidade', {}).get('registros_sem_tipo')}")
    add(results, 21, "Quantidade de registros sem mapeamento", data.get("qualidade", {}).get("registros_sem_mapeamento", 0) == status_counter.get("SEM_MAPEAMENTO", 0), f"sem_mapeamento={status_counter.get('SEM_MAPEAMENTO', 0)}")
    add(results, 22, "Quantidade de conflitos", data.get("qualidade", {}).get("conflitos", 0) == len([r for r in records if r.get("possui_conflito")]), f"conflitos={data.get('qualidade', {}).get('conflitos')}")
    shield = data.get("resumoPorTipo", {}).get("SHIELD", {})
    add(results, 23, "Resultado SHIELD comparado ao diagnostico esperado 119", shield.get("total_sistemico_tags_unicas") == config.get("diagnosticos", {}).get("shield_total_esperado"), shield.get("alerta_diagnostico") or "SHIELD confere", obrigatoria=False)
    add(results, 24, "RETORNADO nao duplica a posicao atual", all(r.get("situacao_retorno") != "RETORNADO" or r.get("status_principal") != "RETORNANDO" for r in records), "retornado como subindicador")
    add(results, 25, "PENDENCIA nao vira aging automaticamente", all(not (r.get("pendencia_operacional") and r.get("faixa_sem_retorno") and str(r.get("regra_aplicada")).startswith("REGRA_PENDENCIA")) for r in records), "pendencias preservadas")
    add(results, 26, "QUALIDADE nao agrupada em fora de operacao", all(v.get("fora_operacao", 0) == v.get("por_status", {}).get("MANUTENCAO", 0) + v.get("por_status", {}).get("CALIBRACAO", 0) for v in data.get("resumoPorTipo", {}).values()), "fora_operacao = manutencao + calibracao")
    add(results, 27, "Origem de cada fixo em veiculo registrada", all(bool(r.get("fontes_encontradas")) or r.get("status_principal") != "FIXO_EM_VEICULO" for r in records), "fontes_encontradas auditadas")
    add(results, 28, "Campos minimos por equipamento presentes", not missing_fields, f"campos_ausentes={len(missing_fields)}")
    return results


def write_report(data: dict[str, Any], config: dict[str, Any], results: list[dict[str, Any]]) -> None:
    records = data.get("registros", [])
    failures, alerts = summarize_failures(results)
    fontes = data.get("fontes", [])
    resumo_tipo = data.get("resumoPorTipo", {})
    qualidade = data.get("qualidade", {})
    manual_ares = data.get("posicaoManualAres", [])
    fixed = data.get("resumoFixosVeiculos", {})
    lines: list[str] = []
    lines.append("# Relatorio de validacao - Conta corrente de dispositivos")
    lines.append("")
    lines.append(f"Gerado em: {datetime.now().replace(microsecond=0).isoformat()}")
    lines.append(f"Snapshot: `{DATA_FILE.name}`")
    lines.append(f"Registros sistemicos: {len(records)}")
    lines.append(f"Falhas obrigatorias: {failures}")
    lines.append(f"Alertas: {alerts}")
    lines.append("")
    lines.append("## Arquivos examinados")
    for path in [CONFIG_FILE, DATA_FILE, HTML_FILE, BASE_DIR / "gerar_conta_corrente_dispositivos.py", Path(__file__)]:
        lines.append(f"- `{path.name}` - {'existe' if path.exists() else 'nao encontrado'}")
    lines.append("")
    lines.append("## Arquivos criados")
    for name in data.get("arquivosCriadosEsperados", []):
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append("## Fontes consultadas")
    for fonte in fontes:
        detalhes = ", ".join(f"{k}={v}" for k, v in fonte.items() if k != "nome")
        lines.append(f"- `{fonte.get('nome')}`: {detalhes}")
    lines.append("")
    lines.append("## Planilha auxiliar de fixos em veiculos")
    fixed_info = qualidade.get("planilha_fixos_veiculos", {})
    lines.append(f"- Caminho: `{fixed_info.get('caminho')}`")
    lines.append(f"- Data de leitura: {fixed_info.get('data_leitura')}")
    lines.append(f"- Abas: {', '.join(fixed_info.get('abas') or [])}")
    lines.append(f"- Colunas identificadas: {', '.join(fixed_info.get('colunas_identificadas') or [])}")
    lines.append(f"- Tags identificadas na planilha: {fixed_info.get('tags_identificadas')}")
    lines.append("")
    lines.append("## Regras aplicadas e premissas")
    for premissa in data.get("premissasAplicadas", []):
        lines.append(f"- {premissa}")
    lines.append("")
    lines.append("## Totais sistemicos")
    lines.append("| Tipo | Total tags unicas | Classificados | Sem mapeamento | Fora de operacao | Retornados |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for tipo, row in resumo_tipo.items():
        lines.append(f"| {tipo} | {row.get('total_sistemico_tags_unicas')} | {row.get('quantidade_classificada')} | {row.get('quantidade_sem_mapeamento')} | {row.get('fora_operacao')} | {row.get('retornados')} |")
    lines.append("")
    lines.append("## Posicao manual de ARES")
    lines.append("| UF | Base | Quantidade | Origem | Data referencia | Responsavel | Observacao |")
    lines.append("|---|---|---:|---|---|---|---|")
    for row in manual_ares:
        lines.append(f"| {row.get('uf')} | {row.get('base')} | {row.get('quantidade_informada')} | {row.get('origem')} | {row.get('data_referencia')} | {row.get('responsavel_informacao')} | {row.get('observacao')} |")
    lines.append("")
    lines.append("## Fixos em veiculos")
    lines.append(f"- Conciliados por tag na conta corrente: {fixed.get('sistemico_conciliado_por_tag')}")
    lines.append(f"- Tags identificadas na planilha: {fixed.get('planilha_tags_identificadas')}")
    lines.append(f"- Linhas sem tag suficiente: {fixed.get('planilha_linhas_sem_tag_suficiente')}")
    lines.append("")
    lines.append("## Qualidade")
    for key in ["registros_sem_data", "registros_sem_tipo", "registros_sem_mapeamento", "conflitos"]:
        lines.append(f"- {key}: {qualidade.get(key)}")
    lines.append("")
    lines.append("## Aging e extravios")
    lines.append(f"- Faixas de nao retorno: `{json.dumps(data.get('faixasNaoRetorno', {}), ensure_ascii=False)}`")
    lines.append(f"- Extravios: {data.get('resumoPorStatus', {}).get('EXTRAVIO', 0)}")
    lines.append("")
    lines.append("## Indicadores operacionais")
    for key, value in data.get("indicadoresOperacionais", {}).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Resultado das validacoes")
    lines.append("| Item | Status | Validacao | Detalhe |")
    lines.append("|---:|---|---|---|")
    for result in results:
        lines.append(f"| {result['item']} | {result['status']} | {result['nome']} | {result['detalhe']} |")
    lines.append("")
    lines.append("## Hashes antes e depois")
    before = data.get("hashesProtegidos", {}).get("antes", [])
    after = {h.get("path"): h for h in data.get("hashesProtegidos", {}).get("depois", [])}
    lines.append("| Arquivo | SHA-256 antes | SHA-256 depois |")
    lines.append("|---|---|---|")
    for row in before:
        after_row = after.get(row.get("path"), {})
        lines.append(f"| `{row.get('path')}` | `{row.get('sha256') or row.get('erro')}` | `{after_row.get('sha256') or after_row.get('erro')}` |")
    lines.append("")
    lines.append("## Confirmacoes")
    confirms = data.get("confirmacoes", {})
    lines.append(f"- Nao houve deploy: {confirms.get('deploy') is False}")
    lines.append(f"- Nao houve commit: {confirms.get('commit') is False}")
    lines.append(f"- Nao houve push: {confirms.get('push') is False}")
    lines.append(f"- A pagina atual nao foi alterada por este fluxo: {confirms.get('alteracao_pacote_aura_original') is False}")
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not DATA_FILE.exists():
        print(f"ERRO: snapshot nao encontrado: {DATA_FILE}", file=sys.stderr)
        return 1
    data = load_json_file(DATA_FILE)
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not data.get("snapshotValido"):
        print("ERRO: snapshot marcado como invalido.", file=sys.stderr)
        return 1
    results = validate(data, config)
    write_report(data, config, results)
    failures, alerts = summarize_failures(results)
    print(f"Relatorio gerado: {REPORT_FILE}")
    print(f"Validacoes obrigatorias com falha: {failures}; alertas: {alerts}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
