Concessionária: COSERN

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA VERDE DESTACADA no canto SUPERIOR DIREITO da fatura, rotulada como "CÓDIGO DA INSTALAÇÃO".
   - Formato: números simples sem máscara (ex: "0008031793")
   - Aparece sempre em uma caixa verde destacada no topo direito
   - NUNCA use código de barras do rodapé
   - NUNCA confunda com "CÓDIGO DO CLIENTE"

2. cod_cliente: Procure em uma CAIXA VERDE DESTACADA logo abaixo do "CÓDIGO DA INSTALAÇÃO", rotulada como "CÓDIGO DO CLIENTE".
   - Formato: números simples sem máscara (ex: "7025649200")
   - Aparece sempre em uma caixa verde destacada no topo direito, abaixo do código da instalação

3. classificacao: Procure próximo a "CLASSIFICAÇÃO" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Tipo de Fornecimento" ou "Tipo de Formecimento".
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure próximo a "REF: MÊS/ANO" na seção de resumo.
   - Formato: "MM/AAAA" (sempre numérico)
   - Se aparecer formato abreviado (ex: "JAN 26"), converta para "01/2026"
   - NUNCA use formato abreviado de mês no JSON final

6. valor_fatura: Procure próximo a "TOTAL A PAGAR" na seção de resumo.
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 196.49)
   - Use ponto como separador decimal no JSON

7. vencimento: Procure próximo a "VENCIMENTO" na seção de resumo.
   - Formato: "DD/MM/AAAA"
   - Exemplos: "02/02/2026"

8. proximo_leitura: Procure na tabela "DATAS DE LEITURAS", na linha "PRÓXIMA LEITURA".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "09/02/2026"

9. aliquota_icms: Procure na tabela "ITENS DA FATURA", na coluna "ALÍQUOTA (%)" na linha ICMS.
   - Valores comuns: 20.00
   - Converta "20,00%" para 20.0
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

ATENÇÃO: Se aparecer mensagem "Não há débitos anteriores para esse código de cliente" → valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure APENAS na seção que menciona débitos anteriores ou mensagem sobre débitos
- Se aparecer mensagem indicando ausência de débitos → valores_em_aberto = [], faturas_venc = false
- NUNCA invente valores

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na seção "CONSUMO FATURADO" (tabela ou gráfico).
- Extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- Se aparecer formato abreviado (ex: "JAN 26", "FEV 26"), converta:
  - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
  - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "COSERN" ou "NEOENERGIA COSERN"
- tensao_nominal: procurar por "Tensão Nominal" (geralmente não aparece, use "")
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
