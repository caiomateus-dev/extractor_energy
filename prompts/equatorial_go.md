Concessionária: EQUATORIAL

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA VERMELHA DESTACADA no canto SUPERIOR DIREITO da fatura, rotulada como "Unidade Consumidora".
   - Formato: números simples sem máscara (ex: "840094747")
   - Aparece sempre em uma caixa vermelha destacada no topo direito
   - NUNCA use código de barras do rodapé

2. cod_cliente: Procure em uma CAIXA LARANJA/AMARELA DESTACADA logo abaixo do "Unidade Consumidora", rotulada como "Parceiro de Negócio".
   - Formato: números simples sem máscara (ex: "1951676", "102899830")
   - Aparece sempre em uma caixa laranja/amarela destacada no topo direito, abaixo do código da instalação
   - CRÍTICO: O valor "Parceiro de Negócio" É o cod_cliente. SEMPRE extraia esse valor para cod_cliente.
   - Se encontrar "Parceiro de Negócio" com um número, esse número é o cod_cliente.
   - Se não encontrar explicitamente, use null
   - ATENÇÃO: O campo "Parceiro de Negócio" NÃO é conta_contrato. NÃO use esse valor para conta_contrato.

3. classificacao: Procure próximo a "Classificacao:" na seção de dados do cliente.
   - Valores comuns: "RESIDENCIAL RESIDENCIAL NORMAL", "RESIDENCIAL"
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer formato composto (ex: "RESIDENCIAL RESIDENCIAL NORMAL"), extraia apenas "RESIDENCIAL"
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Grupo e Subgrupo de Tensao:" na seção de dados do cliente.
   - Valores comuns: "B1 / MONO", "B1 / BIF", "B1 / TRI"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - Mapeamento OBRIGATÓRIO: "MONO" → "MONOFASICO", "BIF" → "BIFASICO", "TRI" → "TRIFASICO"
   - Se encontrar "B1 / MONO" → extraia "MONOFASICO" (NÃO "B1 / MONO")
   - Se encontrar "B1 / BIF" → extraia "BIFASICO" (NÃO "B1 / BIF")
   - Se encontrar "B1 / TRI" → extraia "TRIFASICO" (NÃO "B1 / TRI")
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.
   - NUNCA retorne o formato original "B1 / MONO" - sempre converta para "MONOFASICO"

5. mes_referencia: Procure em uma CAIXA AMARELA no lado esquerdo, próximo a "Conta mês".
   - Valores comuns: "7/2025", "12/2025"
   - Formato: "MM/AAAA" (sempre numérico, com zero à esquerda se necessário)
   - Exemplo: "7/2025" → "07/2025"
   - NUNCA use formato abreviado de mês

6. valor_fatura: Procure em uma CAIXA VERMELHA GRANDE no centro da fatura, próximo a "Total a pagar".
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 180.24)
   - Use ponto como separador decimal no JSON
   - Converta vírgula para ponto (ex: "180,24" → 180.24)

7. vencimento: Próximo a "Vencimento" em caixa amarela no lado direito, próximo ao "Total a pagar". Formato: "DD/MM/AAAA"

8. proximo_leitura: Próximo a "Próxima Leitura" na seção "Datas das Leituras" ou tabela de leituras.
   - Formato: "DD/MM/AAAA"
   - Se não encontrar, use "" (string vazia)

9. aliquota_icms: Procure na tabela "Datas das Leituras", na coluna "Aliquota ICMS(%)".
   - Valores comuns: 19.00
   - Converta "19,00%" para 19.0
   - Se não encontrar, use null

10. tensao_nominal: Procure próximo a "Tensão Nom.:" na seção de dados do cliente.
    - Formato: número seguido de "V" (ex: "220 V", "127 V")
    - Se não encontrar, use ""

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer "BAIXA RENDA" ou "TARIFA SOCIAL" na classificação
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA" ou "Tipo de Tarita: BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO CRÍTICA: 
- PROCURE ATENTAMENTE pela seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" na fatura
- Esta seção geralmente aparece no RODAPÉ da fatura, destacada em vermelho ou com fundo colorido
- Se você encontrar essa seção com débitos listados, EXTRAIA os valores
- Se você não encontrar essa seção ou ela estiver vazia, retorne valores_em_aberto = [] e faturas_venc = false
- NÃO invente valores. Mas TAMBÉM não ignore a seção se ela existir.

ONDE PROCURAR:
- Procure APENAS na seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" ou "DÉBITOS ANTERIORES"
- Na seção "REAVISO DE VENCIMENTO", procure por linhas como:
  - "NOTIFICAÇÃO: X FATURA(S)" ou "NOTIFICACAO: X FATURA(S)"
  - "UNIDADE VENCIDA: MES X/AAAA VALOR TOTAL: R$ XXX,XX"
  - "MES X/AAAA VALOR TOTAL: R$ XXX,XX"
  - "FATURA VENCIDA: MES X/AAAA VALOR TOTAL: R$ XXX,XX"
- Esta seção geralmente aparece no meio ou rodapé da fatura, muitas vezes destacada em vermelho ou com fundo colorido
- ATENÇÃO: A seção pode aparecer escrita como "REAVISO DE VENCIMENTO", "REAVISO", "NOTIFICAÇÃO", "NOTIFICACAO" (sem acento)
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" ou "DÉBITOS ANTERIORES"
- PROCURE NO RODAPÉ DA FATURA - esta seção geralmente aparece no final da fatura
- PROCURE POR TEXTOS EM VERMELHO ou com fundo colorido destacado
- PROCURE POR TEXTOS como "REAVISO DE VENCIMENTO", "REAVISO", "NOTIFICAÇÃO", "NOTIFICACAO", "DÉBITOS ANTERIORES"
- Se NÃO encontrar essa seção → valores_em_aberto = [], faturas_venc = false → PARE AQUI
- Se ENCONTRAR a seção, CONTINUE para o PASSO 2

PASSO 2: VERIFIQUE se a seção está VAZIA:
- Se a seção existir mas não tiver NENHUMA informação de fatura vencida listada
- Se não houver nenhum mês/ano e valor listados na seção
→ valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 3: Se a seção tiver FATURAS VENCIDAS LISTADAS:
   → Para cada fatura vencida EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha, ex: "MES 5/2025" → "05/2025", "MES 05/2025" → "05/2025")
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha, ex: "VALOR TOTAL: R$ 506,94" → 506.94, "R$ 506,94" → 506.94)
   → VALIDAÇÃO CRÍTICA: O valor deve ser um valor de FATURA (geralmente dezenas ou centenas de reais)
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
     - Se for FUTURO → IGNORE
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false
   
EXEMPLO PRÁTICO OBRIGATÓRIO:
- Se mes_referencia = "06/2025" e encontrar na seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" uma linha como:
  - "NOTIFICACAO: 1 FATURA VENCIDA: MES 5/2025 VALOR TOTAL: R$ 506,94"
  - "MES 5/2025 VALOR TOTAL: R$ 506,94"
  - "FATURA VENCIDA: MES 5/2025 VALOR TOTAL: R$ 506,94"
- Então você DEVE extrair:
  → valores_em_aberto = [{"mes_ano": "05/2025", "valor": 506.94}]
  → faturas_venc = true

REGRA ABSOLUTA:
- Se você encontrar a seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" com débitos listados, você DEVE extrair os valores
- Não ignore essa seção se ela existir na fatura
- Compare o mês do débito com mes_referencia: se for anterior, inclua em valores_em_aberto

VALIDAÇÃO FINAL OBRIGATÓRIA - ANTES DE RETORNAR O JSON, VERIFIQUE:

1. Você PROCUROU pela seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" no RODAPÉ da fatura? (SIM/NÃO)
   - Se NÃO procurou → PROCURE AGORA antes de retornar
   - Se procurou e NÃO encontrou → valores_em_aberto = [] e faturas_venc = false

2. Se você ENCONTROU a seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO":
   - Ela tem débitos listados? (SIM/NÃO)
   - Se SIM → Extraia os débitos que são anteriores ao mes_referencia
   - Se NÃO (seção vazia) → valores_em_aberto = [] e faturas_venc = false

3. Se valores_em_aberto contiver o mes_referencia atual → valores_em_aberto = [] e faturas_venc = false (isso está ERRADO)

REGRA ABSOLUTA:
- PROCURE ATENTAMENTE pela seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" no RODAPÉ da fatura
- Se encontrar débitos anteriores ao mes_referencia, EXTRAIA os valores
- Se não encontrar a seção ou ela estiver vazia, retorne valores_em_aberto = [] e faturas_venc = false
- NUNCA invente valores, mas TAMBÉM não ignore a seção se ela existir

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na seção de histórico de consumo (geralmente não aparece em todas as faturas).
- Se não encontrar tabela de histórico com múltiplos meses → consumo_lista = []
- Se encontrar, extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- consumo: número inteiro em kWh

==========================
ENDEREÇO - REGRAS ESPECÍFICAS EQUATORIAL
==========================

⚠️⚠️⚠️ ATENÇÃO: Esta seção é usada APENAS para extração de endereço via crop separado ⚠️⚠️⚠️

REGRA CRÍTICA PARA ENDEREÇOS EQUATORIAL - SIGA EXATAMENTE:

EXEMPLO DE ENDEREÇO EQUATORIAL: "RUA 01, Q. 11, L. 22, S/N VILA SAO JOSE CEP: 75402700 INHUMAS GO"

EXTRAÇÃO OBRIGATÓRIA (SIGA EXATAMENTE):
- rua: "RUA 01" (o número "01" após "RUA" faz parte do nome da rua. NÃO é o número do endereço. NUNCA extraia esse número como campo `numero`. Se aparecer "RUA 01", o campo `rua` deve ser "RUA 01" completo)
- numero: "S/N" (SEMPRE que aparecer "S/N" ou "Sem Número" no endereço, coloque "S/N" no campo `numero`. NUNCA coloque em `complemento`. Se aparecer "S/N" no endereço, o campo `numero` DEVE ser "S/N")
- complemento: "Q. 11, L. 22" (Quadra e Lote são complementos. Se aparecer "Q. 11, L. 22, S/N", extraia apenas "Q. 11, L. 22" sem o S/N. O S/N vai para o campo `numero`)
- bairro: "VILA SAO JOSE" (nome completo incluindo prefixo "VILA". Se aparecer "VILA SAO JOSE", extraia completo)
- cep: "75402700" (extraia APENAS os números após "CEP:" na linha do endereço. Se aparecer "CEP: 75402700", extraia "75402700". NÃO use CEPs de outras partes da fatura como "54.000-000")
- cidade: "INHUMAS" (nome da cidade que aparece ANTES da sigla do estado na linha do endereço. Se aparecer "INHUMAS GO", a cidade é "INHUMAS". NÃO use "GOIÂNIA" ou outras cidades de outras partes da fatura)
- estado: "GO" (sigla de 2 letras após o nome da cidade na linha do endereço)

REGRAS ABSOLUTAS (SIGA EXATAMENTE):
1. Se aparecer "RUA XX" ou "AVENIDA XX" (onde XX é um número), o número XX faz parte do nome da rua. NÃO extraia esse número como campo `numero`. O campo `rua` deve conter "RUA XX" completo.
2. Se aparecer "S/N" ou "Sem Número" no endereço, SEMPRE coloque "S/N" no campo `numero` (NUNCA em `complemento`). Se aparecer "S/N", o campo `numero` DEVE ser "S/N".
3. Complemento: Use para Quadra (Q.), Lote (L.), Bloco, Apto, etc. Se aparecer "Q. 11, L. 22, S/N", extraia apenas "Q. 11, L. 22" no campo `complemento` (sem o S/N). O S/N vai para `numero`.
4. CEP: Procure por "CEP:" seguido de números na linha do endereço. Extraia apenas os números (sem formatação). Se aparecer "CEP: 75402700", extraia "75402700". NÃO use valores de outras partes da fatura.
5. Cidade: Nome da cidade que aparece ANTES da sigla do estado na linha do endereço. Se aparecer "INHUMAS GO", a cidade é "INHUMAS". NÃO confunda com outras cidades que possam aparecer em outras partes da fatura.
6. Extraia APENAS os dados que aparecem na linha do endereço do cliente. NÃO use valores de outras seções da fatura (como cidade da distribuidora, CEPs de outras partes, etc.).

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "EQUATORIAL"
- conta_contrato: SEMPRE null (NÃO existe este campo nesta fatura. NÃO extraia "Parceiro de Negócio" ou qualquer outro número como conta_contrato. Se você extrair qualquer valor aqui, está ERRADO. Use APENAS null)
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
- REGRA CRÍTICA: Se você não encontrar explicitamente um campo na fatura, NÃO invente. Use o valor padrão ("" para strings, null para opcionais, false para booleanos, [] para listas)
