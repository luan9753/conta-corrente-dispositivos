# Relatorio de validacao - Conta corrente de dispositivos

Gerado em: 2026-06-27T02:10:11
Snapshot: `CONTA_CORRENTE_DISPOSITIVOS_DATA.js`
Registros sistemicos: 15529
Falhas obrigatorias: 4
Alertas: 0

## Arquivos examinados
- `CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json` - existe
- `CONTA_CORRENTE_DISPOSITIVOS_DATA.js` - existe
- `CONTA_CORRENTE_DISPOSITIVOS.html` - existe
- `gerar_conta_corrente_dispositivos.py` - existe
- `validar_conta_corrente_dispositivos.py` - existe

## Arquivos criados
- `CONTA_CORRENTE_DISPOSITIVOS.html`
- `CONTA_CORRENTE_DISPOSITIVOS_DATA.js`
- `CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json`
- `gerar_conta_corrente_dispositivos.py`
- `validar_conta_corrente_dispositivos.py`
- `RELATORIO_VALIDACAO_CONTA_CORRENTE.md`

## Fontes consultadas
- `vwTabelaMovDataloggers`: tipo=sistemica, linhas_lidas=15505
- `tbddataloggerhistoricos`: tipo=sistemica, linhas_lidas_latest=12222, linhas_rollup=12222
- `vtc_stage.documentos`: tipo=sistemica, linhas_lidas=71837
- `planilha_fixos_veiculos`: tipo=auxiliar, caminho=C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx, nome_arquivo=controle de loggers fixos dos veículos - atualizado.xlsx, existe=True, data_leitura=2026-06-27T02:08:40, abas=['LOGGERS FIXOS', 'COORDENADORES', 'DATA CALIBRAÇÃO', 'AGREGADOS', 'IMPRESSÃO', 'Planilha2'], colunas_identificadas=['EMPRESA', 'DESCRIÇÃO', 'PLACA', 'MOTORISTA', 'LOGGER 1', 'CALIBRAÇÃO', 'DIAS RESTANTES', 'SITUAÇÃO', 'LOGGER 2', 'CALIBRAÇÃO2', 'DIAS RESTANTES2', 'SITUAÇÃO2', 'LOGGER 3', 'CALIBRAÇÃO3', 'DIAS RESTANTES3', 'SITUAÇÃO3', 'STATUS', 'SENSORWEB 1', 'SENSORWEB 2', 'COORDENADOR', 'DATA DE INSTALAÇÃO', 'ÚLTIMA CONFIGURAÇÃO', 'PRAZO MÁXIMO DA MEMÓRIA', 'Dias Para Baixar', 'Data Atual', 'AÇÃO GQ', 'Check Coordenador', 'Concat', 'Check Pendência', 'Circustância', 'OBSERVAÇÃO', 'Coluna2'], linhas_lidas=107, tags_identificadas=186, linhas_sem_tag_suficiente=22, erro=None

## Planilha auxiliar de fixos em veiculos
- Caminho: `C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx`
- Data de leitura: 2026-06-27T02:08:40
- Abas: LOGGERS FIXOS, COORDENADORES, DATA CALIBRAÇÃO, AGREGADOS, IMPRESSÃO, Planilha2
- Colunas identificadas: EMPRESA, DESCRIÇÃO, PLACA, MOTORISTA, LOGGER 1, CALIBRAÇÃO, DIAS RESTANTES, SITUAÇÃO, LOGGER 2, CALIBRAÇÃO2, DIAS RESTANTES2, SITUAÇÃO2, LOGGER 3, CALIBRAÇÃO3, DIAS RESTANTES3, SITUAÇÃO3, STATUS, SENSORWEB 1, SENSORWEB 2, COORDENADOR, DATA DE INSTALAÇÃO, ÚLTIMA CONFIGURAÇÃO, PRAZO MÁXIMO DA MEMÓRIA, Dias Para Baixar, Data Atual, AÇÃO GQ, Check Coordenador, Concat, Check Pendência, Circustância, OBSERVAÇÃO, Coluna2
- Tags identificadas na planilha: 186

## Regras aplicadas e premissas
- equipamento_id = upper(trim(tag))
- ARES e ARES COM SONDA consolidados no tipo ARES
- Total contratado de ARES informado pelo usuario: 10.712; divergencia sistemica fica como diagnostico
- Dados manuais de ARES nao compoem totais sistemicos
- Retornados sao subindicador e nao duplicam status principal
- Indicadores operacionais ficam fora da conta corrente
- Extravio aplicado somente acima de 180 dias sem movimentacao valida, exceto manutencao/calibracao

## Totais sistemicos
| Tipo | Total contratado | Total sistemico tags unicas | Diferenca sistema x contratado | Classificados | Sem mapeamento | Fora de operacao | Retornados |
|---|---:|---:|---:|---:|---:|---:|---:|
| ARES | 10712 | 10641 | -71 | 10068 | 573 | 1333 | 1303 |
| SHIELD | None | 937 | None | 604 | 333 | 327 | 211 |
| SENSOR VTC | None | 769 | None | 746 | 23 | 99 | 449 |
| SYOS | None | 2000 | None | 1614 | 386 | 0 | 1716 |

## Posicao manual de ARES
| UF | Base | Quantidade | Origem | Data referencia | Responsavel | Observacao |
|---|---|---:|---|---|---|---|
| DF | BSB | 116 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| MG | MG | 34 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| RJ | GIG | 50 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| SP | CAMPINAS | 1 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |

## Fixos em veiculos
- Conciliados por tag na conta corrente: 260
- Tags identificadas na planilha: 186
- Linhas sem tag suficiente: 22

## Qualidade
- registros_sem_data: 0
- registros_sem_tipo: 1182
- registros_sem_mapeamento: 1374
- conflitos: 6355

## Aging e extravios
- Faixas de nao retorno: `{"ATE_30": 3877, "31_60": 414, "61_90": 192, "91_180": 519}`
- Extravios: 68

## Indicadores operacionais
- entregues_ultimos_20_dias: 4787
- retornados_ultimos_20_dias: 4735
- pendencias_operacionais: 168
- movimentacoes_ultimos_5_dias: 3715
- packing: 4602
- recebimentos_recentes: 4735
- expedicoes_recentes: 2002
- observacao: Indicadores de movimentacao nao compoem a conta corrente.

## Resultado das validacoes
| Item | Status | Validacao | Detalhe |
|---:|---|---|---|
| 1 | OK | Ausencia de equipamento_id duplicado | duplicados=0 |
| 2 | OK | Soma dos status principais igual ao total de tags unicas | soma_status=15529; registros=15529 |
| 3 | OK | Cada equipamento em apenas um status principal | status fora da taxonomia verificados |
| 4 | OK | Faixas de nao retorno exclusivas | faixas_preenchidas=5002 |
| 5 | OK | Faixa 91_180 limitada corretamente | 91_180 validada |
| 6 | OK | Extravio recalculado por entrega sem retorno acima de 180 dias | extravios_invalidos=0 |
| 7 | OK | Manutencao e calibracao fora da regra de extravio | manutencao/calibracao avaliadas |
| 8 | OK | Ausencia de sobreposicao entre extravio e nao retorno | extravio nao possui faixa |
| 9 | OK | ARES consolida ARES e ARES COM SONDA | cards/resumo usam ARES consolidado |
| 10 | OK | Totais sistemicos por filial calculados dinamicamente | resumoPorLocalizacao presente |
| 11 | OK | Dados manuais de ARES separados da posicao sistemica | manual ARES separado |
| 12 | OK | Dados da planilha de veiculos nao incorporados como constantes | gerador le a planilha dinamicamente e nao contem tags fixas |
| 13 | OK | Tags fixas em veiculos deduplicadas contra demais fontes | dedupe global por equipamento_id |
| 14 | OK | Indicadores operacionais fora da conta corrente | indicadores em chave separada |
| 15 | OK | Ausencia de totais sistemicos fixos no HTML | HTML sem totais diagnosticos fixos |
| 16 | OK | Uso de null para dados ausentes | snapshot nao usa string N/D internamente |
| 17 | OK | Consistencia entre resumos e registros | resumoPorStatus confere |
| 18 | OK | Integridade dos arquivos protegidos por SHA-256 | alterados=[] |
| 19 | OK | Quantidade de registros sem data | sem_data=0 |
| 20 | FALHA | Registros sem tipo justificados ou eliminados | sem_tipo=1182 |
| 21 | FALHA | Status sem mapeamento analisado e resolvido | sem_mapeamento=1374 |
| 22 | FALHA | Conflitos resolvidos com criterio auditavel | conflitos=6355 |
| 23 | FALHA | Divergencia SHIELD tecnicamente reconciliada | Total sistemico SHIELD diferente da referencia diagnostica 119 |
| 24 | OK | RETORNADO nao duplica a posicao atual | retornado como subindicador |
| 25 | OK | PENDENCIA nao vira aging automaticamente | pendencias preservadas |
| 26 | OK | QUALIDADE nao agrupada em fora de operacao | fora_operacao = manutencao + calibracao |
| 27 | OK | Origem de cada fixo em veiculo registrada | fontes_encontradas auditadas |
| 28 | OK | Campos minimos por equipamento presentes | campos_ausentes=0 |
| 29 | OK | Stage operacional incorporado ao consolidado | stage_linhas=71837; candidatos_finais=9079 |
| 30 | OK | Nao retorno possui entrega real como base | referencias_saida_entrega=9079; entregas=9076; faixas_preenchidas=5002 |

## Hashes antes e depois
| Arquivo | SHA-256 antes | SHA-256 depois |
|---|---|---|
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\GESTAO_DISPOSITIVOS.html` | `AF9BAFCAF492956835F327731FDDC1F73E105FDEDC318BACADB6E9B434EBC3B5` | `AF9BAFCAF492956835F327731FDDC1F73E105FDEDC318BACADB6E9B434EBC3B5` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\GESTAO_DISPOSITIVOS_STAGE_DATA.js` | `814EB5356BE9E9B649C977145358563795E91DE6F289BA0FCAE622DE334969B4` | `814EB5356BE9E9B649C977145358563795E91DE6F289BA0FCAE622DE334969B4` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\ESTOQUE_DATALOGGERS.html` | `796FDB32B62592AF094BD3942705690FFD717115EE9AB5229D5DF7BD9BD697AA` | `796FDB32B62592AF094BD3942705690FFD717115EE9AB5229D5DF7BD9BD697AA` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\ATUALIZAR_TUDO_10_MIN.ps1` | `D063B496BC52243634CB2C7EE384F02C1B206FF1A65C3EC26A650BAD02E3BD38` | `D063B496BC52243634CB2C7EE384F02C1B206FF1A65C3EC26A650BAD02E3BD38` |
| `C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx` | `E75624F75EA907C089FD74653E52928A68B542B7BC04C0D9A2E11B8B08A88655` | `E75624F75EA907C089FD74653E52928A68B542B7BC04C0D9A2E11B8B08A88655` |

## Confirmacoes
- Nao houve deploy: True
- Nao houve commit: True
- Nao houve push: True
- A pagina atual nao foi alterada por este fluxo: True
