Concessionária: ENEL

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma BANDA ROSA DESTACADA no centro superior da fatura, rotulada como "Nº INSTALAÇÃO".
   - Formato: números simples sem máscara (ex: "10351018")
   - Aparece sempre em uma banda rosa destacada no centro superior
   - NUNCA use código de barras do rodapé
   - NUNCA confunda com "Nº DO CLIENTE" (mesmo que possam ter o mesmo valor)

2. cod_cliente: Procure em uma BANDA ROSA DESTACADA logo ao lado do "Nº INSTALAÇÃO", rotulada como "Nº DO CLIENTE".
   - Formato: números simples sem máscara
   - Pode ser o mesmo valor que num_instalacao
   - Se não encontrar explicitamente, use null

3. classificacao: Procure em uma CAIXA AZUL CLARA no topo esquerdo, próximo a "CLASSIFICAÇÃO DA UNIDADE CONSUMIDORA".
   - Valores comuns: "RURAL", "RESIDENCIAL", "COMERCIAL"
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure em uma CAIXA ROSA no topo direito, próximo a "TIPO DE FORNECIMENTO".
   - Valores comuns: "Monofásico", "Bifásico", "Trifásico"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - Converta acentos: "Monofásico" → "MONOFASICO"
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure em uma CAIXA AZUL CLARA no centro superior, próximo a "MES/ANO DE REFERENCIA".
   - Formato: "MM/AAAA" (sempre numérico)
   - Exemplos: "02/2025"
   - NUNCA use formato abreviado de mês (ex: "FEV/2025")

6. valor_fatura: Procure em uma CAIXA ROSA GRANDE no centro superior, próximo a "TOTAL A PAGAR".
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 92.60)
   - Use ponto como separador decimal no JSON
   - Converta vírgula para ponto (ex: "92,60" → 92.60)

7. vencimento: Procure em uma CAIXA ROSA CLARA no centro superior, próximo a "VENCIMENTO".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "14/02/2025"

8. proximo_leitura: Procure na tabela "DATAS DE LEITURA", na coluna "PRÓXIMA LEITURA".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "11/03/2025"
   - Se aparecer só "DD/MM", complete o ano baseado no mes_referencia

9. aliquota_icms: Procure na tabela "TRIBUTO", na coluna "ALÍQUOTA (%)" na linha ICMS.
   - Valores comuns: 0.00, 18.00, 20.00
   - Converta "18%" ou "18,00%" para 18.0
   - Se for 0.00 ou não encontrar, use null

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer "BAIXA RENDA" ou "TARIFA SOCIAL" na classificação
- ths_verde: true apenas se aparecer explicitamente "THS VERDE" ou "Bandeira verde" nas mensagens importantes
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos com valores diferentes na seção "NOTIFICAÇÃO/REAVISO DE CONTAS VENCIDAS" ou mensagem sobre débitos, então valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure APENAS na seção "NOTIFICAÇÃO/REAVISO DE CONTAS VENCIDAS" ou mensagem sobre débitos anteriores
- Se aparecer mensagem "Não constam débitos relativos às faturas vencidas" → valores_em_aberto = [], faturas_venc = false
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção que menciona débitos anteriores
- Se encontrar mensagem indicando ausência de débitos → valores_em_aberto = [], faturas_venc = false → PARE AQUI
- Se NÃO encontrar seção de débitos → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 2: Se encontrar uma LISTA CLARA de débitos:
   → Para cada linha de débito EXPLICITAMENTE listada:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha do débito)
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha)
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

consumo_lista: Procure na tabela de histórico de consumo (geralmente no rodapé da fatura).
- Extraia na ORDEM EXATA que aparece na tabela
- Formato mes_ano: "MM/AAAA" (ex: "02/2025", "01/2025")
- Se aparecer formato abreviado (ex: "JAN25", "FEV24", "DEZ24"), converta:
  - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
  - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
  - Exemplo: "JAN25" → "01/2025", "FEV24" → "02/2024", "DEZ24" → "12/2024"
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "ENEL" ou "ENEL BRASIL"
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão" (geralmente não aparece, use "")
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
