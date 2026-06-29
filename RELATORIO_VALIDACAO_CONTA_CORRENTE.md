# Relatorio de validacao - Conta corrente de dispositivos

Gerado em: 2026-06-29T07:55:51
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
- `tbddataloggerhistoricos`: tipo=sistemica, linhas_lidas_latest=12223, linhas_rollup=12223
- `vtc_stage.documentos`: tipo=sistemica, linhas_lidas=72438
- `planilha_fixos_veiculos`: tipo=auxiliar, caminho=C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx, nome_arquivo=controle de loggers fixos dos veículos - atualizado.xlsx, existe=True, data_leitura=2026-06-29T07:54:23, abas=['LOGGERS FIXOS', 'COORDENADORES', 'DATA CALIBRAÇÃO', 'AGREGADOS', 'IMPRESSÃO', 'Planilha2'], colunas_identificadas=['EMPRESA', 'DESCRIÇÃO', 'PLACA', 'MOTORISTA', 'LOGGER 1', 'CALIBRAÇÃO', 'DIAS RESTANTES', 'SITUAÇÃO', 'LOGGER 2', 'CALIBRAÇÃO2', 'DIAS RESTANTES2', 'SITUAÇÃO2', 'LOGGER 3', 'CALIBRAÇÃO3', 'DIAS RESTANTES3', 'SITUAÇÃO3', 'STATUS', 'SENSORWEB 1', 'SENSORWEB 2', 'COORDENADOR', 'DATA DE INSTALAÇÃO', 'ÚLTIMA CONFIGURAÇÃO', 'PRAZO MÁXIMO DA MEMÓRIA', 'Dias Para Baixar', 'Data Atual', 'AÇÃO GQ', 'Check Coordenador', 'Concat', 'Check Pendência', 'Circustância', 'OBSERVAÇÃO', 'Coluna2'], linhas_lidas=107, tags_identificadas=186, linhas_sem_tag_suficiente=22, erro=None

## Planilha auxiliar de fixos em veiculos
- Caminho: `C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx`
- Data de leitura: 2026-06-29T07:54:23
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
| ARES | 10712 | 10641 | -71 | 10229 | 412 | 1333 | 1736 |
| SHIELD | None | 937 | None | 604 | 333 | 327 | 211 |
| SENSOR VTC | None | 769 | None | 761 | 8 | 99 | 450 |
| SYOS | None | 2000 | None | 1614 | 386 | 0 | 1749 |

## Posicao manual de ARES
| UF | Base | Quantidade | Origem | Data referencia | Responsavel | Observacao |
|---|---|---:|---|---|---|---|
| DF | BSB | 116 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| MG | MG | 34 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| RJ | GIG | 50 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |
| SP | CAMPINAS | 1 | LEVANTAMENTO_MANUAL | None | None | Posicao fisica informada manualmente pela base; nao conciliada individualmente por tag. |

## Fixos em veiculos
- Conciliados por tag na conta corrente: 258
- Tags identificadas na planilha: 186
- Linhas sem tag suficiente: 22

## Qualidade
- registros_sem_data: 0
- registros_sem_tipo: 1182
- registros_sem_mapeamento: 1171
- conflitos: 6221

## Aging e extravios
- Faixas de nao retorno: `{"ATE_30": 3342, "31_60": 441, "61_90": 212, "91_180": 497}`
- Extravios: 73

## Indicadores operacionais
- entregues_ultimos_20_dias: 4819
- retornados_ultimos_20_dias: 4683
- pendencias_operacionais: 160
- movimentacoes_ultimos_5_dias: 2996
- packing: 4346
- recebimentos_recentes: 4683
- expedicoes_recentes: 1229
- observacao: Indicadores de movimentacao nao compoem a conta corrente.

## Resultado das validacoes
| Item | Status | Validacao | Detalhe |
|---:|---|---|---|
| 1 | OK | Ausencia de equipamento_id duplicado | duplicados=0 |
| 2 | OK | Soma dos status principais igual ao total de tags unicas | soma_status=15529; registros=15529 |
| 3 | OK | Cada equipamento em apenas um status principal | status fora da taxonomia verificados |
| 4 | OK | Faixas de nao retorno exclusivas | faixas_preenchidas=4492 |
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
| 21 | FALHA | Status sem mapeamento analisado e resolvido | sem_mapeamento=1171 |
| 22 | FALHA | Conflitos resolvidos com criterio auditavel | conflitos=6221 |
| 23 | FALHA | Divergencia SHIELD tecnicamente reconciliada | Total sistemico SHIELD diferente da referencia diagnostica 119 |
| 24 | OK | RETORNADO nao duplica a posicao atual | retornado como subindicador |
| 25 | OK | PENDENCIA nao vira aging automaticamente | pendencias preservadas |
| 26 | OK | QUALIDADE nao agrupada em fora de operacao | fora_operacao = manutencao + calibracao |
| 27 | OK | Origem de cada fixo em veiculo registrada | fontes_encontradas auditadas |
| 28 | OK | Campos minimos por equipamento presentes | campos_ausentes=0 |
| 29 | OK | Stage operacional incorporado ao consolidado | stage_linhas=72438; candidatos_finais=9080 |
| 30 | OK | Nao retorno possui entrega real como base | referencias_saida_entrega=9080; entregas=9078; faixas_preenchidas=4492 |

## Hashes antes e depois
| Arquivo | SHA-256 antes | SHA-256 depois |
|---|---|---|
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\GESTAO_DISPOSITIVOS.html` | `AF9BAFCAF492956835F327731FDDC1F73E105FDEDC318BACADB6E9B434EBC3B5` | `AF9BAFCAF492956835F327731FDDC1F73E105FDEDC318BACADB6E9B434EBC3B5` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\GESTAO_DISPOSITIVOS_STAGE_DATA.js` | `E218F712579B74ABFC90352487C60360F8A7B8A34D359E1EF24D0EC4B69771AC` | `E218F712579B74ABFC90352487C60360F8A7B8A34D359E1EF24D0EC4B69771AC` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\ESTOQUE_DATALOGGERS.html` | `CBFF669E1524714F41928FE81E5EC02DCC1C7FE243A124EA0C969706E6807BD4` | `CBFF669E1524714F41928FE81E5EC02DCC1C7FE243A124EA0C969706E6807BD4` |
| `C:\Users\Administrador\Documents\PACOTE_AURA_24H (2)\PACOTE_AURA_24H\PACOTE_AURA_24H\Banco_Aura\ATUALIZAR_TUDO_10_MIN.ps1` | `D063B496BC52243634CB2C7EE384F02C1B206FF1A65C3EC26A650BAD02E3BD38` | `D063B496BC52243634CB2C7EE384F02C1B206FF1A65C3EC26A650BAD02E3BD38` |
| `C:\Users\Administrador\Documents\Novo indicador CONTA CORRENTE\controle de loggers fixos dos veículos - atualizado.xlsx` | `E75624F75EA907C089FD74653E52928A68B542B7BC04C0D9A2E11B8B08A88655` | `E75624F75EA907C089FD74653E52928A68B542B7BC04C0D9A2E11B8B08A88655` |

## Confirmacoes
- Nao houve deploy: True
- Nao houve commit: True
- Nao houve push: True
- A pagina atual nao foi alterada por este fluxo: True
