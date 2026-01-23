Concessionária: COPEL

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA CINZA DESTACADA no centro superior da fatura, rotulada como "UNIDADE CONSUMIDORA".
   - Formato: números simples sem máscara (ex: "70093245", "17605199")
   - Aparece sempre em uma caixa cinza destacada no centro superior
   - NUNCA use código de barras do rodapé
   - NUNCA use outros códigos que aparecem na fatura

2. classificacao: Procure próximo a "Classificação:" na seção de dados do cliente.
   - Valores comuns: "RESIDENCIAL/RESIDENCIAL", "B1 Residencial / Residencial"
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer "B1 Residencial", extraia apenas "RESIDENCIAL"
   - Se aparecer formato duplo (ex: "RESIDENCIAL/RESIDENCIAL"), use apenas "RESIDENCIAL"
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

3. tipo_instalacao: Procure próximo a "Tipo de Fornecimento:" ou "Tipo de Formecimento:" na seção de dados do cliente.
   - Valores comuns: "TRIFASICO/70A", "Trifásico / 50A", "MONOFASICO", "BIFASICO"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - Se aparecer formato com amperagem (ex: "TRIFASICO/70A", "Trifásico / 50A"), extraia apenas "TRIFASICO"
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

4. mes_referencia: Procure na tabela de resumo, próximo a "REF: MÊS/ANO".
   - Formato: "MM/AAAA" (sempre numérico)
   - Exemplos: "10/2025", "12/2025"
   - NUNCA use formato abreviado de mês (ex: "OUT/2025")

5. valor_fatura: Procure na tabela de resumo, próximo a "TOTAL A PAGAR".
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 163.54, 213.91)
   - Use ponto como separador decimal no JSON
   - Converta vírgula para ponto (ex: "163,54" → 163.54)

6. vencimento: Procure na tabela de resumo, próximo a "VENCIMENTO".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "25/10/2025", "04/01/2026"

7. proximo_leitura: Procure na tabela "DATAS DE LEITURAS", na linha "Próxima Leitura".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "04/11/2025", "13/01/2026"
   - Se aparecer só "DD/MM", complete o ano baseado no mes_referencia

8. aliquota_icms: Procure na seção "ICMS" ao lado da tabela "Itens de fatura", na coluna "Alíquota (%)".
   - Valores comuns: 18.00
   - Converta "18%" ou "18,00%" para 18.0
   - Se não encontrar, use null

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer "BAIXA RENDA" ou "TARIFA SOCIAL" na classificação
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos com valores diferentes na seção "* REAVISO DE VENCIMENTO *", então valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure APENAS na seção "* REAVISO DE VENCIMENTO *" (com asteriscos)
- Esta seção geralmente aparece no rodapé da fatura
- Se a seção existir mas não tiver débitos listados → valores_em_aberto = [], faturas_venc = false
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "* REAVISO DE VENCIMENTO *"
- Se NÃO encontrar essa seção → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 2: VERIFIQUE se a seção está VAZIA:
- Se a seção existir mas não tiver NENHUMA linha de débito listada → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 3: Se a seção tiver DÉBITOS LISTADOS (com linhas contendo mês/ano e valor):
   → Para cada linha de débito EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha do débito, ex: "Referência: 09/2025")
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha, ex: "Valor (R$): 87,67")
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false
- É melhor retornar vazio do que retornar valores errados
- NUNCA invente valores

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na tabela "HISTORICO DE CONSUMO/KWH" ou "HISTÓRICO DE CONSUMO / kWh" (lado direito da fatura).
- Extraia na ORDEM EXATA que aparece na tabela
- Formato mes_ano: "MM/AAAA" (ex: "10/2025", "12/2025")
- Se aparecer formato abreviado (ex: "OUT25", "DEZ25", "NOV25"), converta:
  - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
  - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
  - Exemplo: "OUT25" → "10/2025", "DEZ25" → "12/2025"
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "COPEL" ou "COPEL DISTRIBUIÇÃO"
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão" (geralmente não aparece, use "")
- conta_contrato: sempre null
- cod_cliente: sempre null (não aparece explicitamente na fatura)
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
