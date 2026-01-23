Concessionária: COELBA (Neoenergia Coelba)

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA VERDE DESTACADA no canto SUPERIOR DIREITO da fatura, rotulada como "CÓDIGO DA INSTALAÇÃO".
   - Formato: números simples sem máscara (ex: "0010861656", "0001965299", "0004894294", "0005060180", "0002503097")
   - Aparece sempre em uma caixa verde destacada no topo direito
   - NUNCA use código de barras do rodapé
   - NUNCA use "Código do Cliente" (esse é cod_cliente)

2. cod_cliente: Procure em uma CAIXA VERDE DESTACADA logo abaixo do "CÓDIGO DA INSTALAÇÃO", rotulada como "CÓDIGO DO CLIENTE".
   - Formato: números simples sem máscara (ex: "7073737197", "7017081742", "7071458576", "35597085", "7679491")
   - Aparece sempre em uma caixa verde destacada no topo direito, abaixo do código da instalação
   - NUNCA confunda com código da instalação

3. classificacao: Procure próximo a "CLASSIFICAÇÃO" ou "CLASSIFICAÇÃO B1 RESIDENCIAL".
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Pode aparecer como "B1 RESIDENCIAL" - extraia apenas "RESIDENCIAL"
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "TIPO DE FORNECIMENTO" ou "Tipo de Fornecimento".
   - Valores comuns: "Conv Monômia-Bifasico", "Conv Monômia - Monofásico", "Conv Monômia-Trifásico"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - Se aparecer "Monômia" ou "Conv Monômia", ignore e extraia apenas o tipo (Monofásico/Bifásico/Trifásico)
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure próximo a "REF: MÊS/ANO" ou "REF. MÊS / ANO" na seção de resumo (banda verde).
   - Formato: "MM/AAAA" (sempre numérico)
   - Exemplos: "03/2025", "05/2025", "12/2025"
   - NUNCA use formato abreviado de mês (ex: "MAR/2025")

6. valor_fatura: Procure na BANDA VERDE destacada, próximo a "TOTAL A PAGAR".
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 698.85, 285.50, 554.37, 479.34, 210.23)
   - Use ponto como separador decimal no JSON

7. vencimento: Procure na BANDA VERDE destacada, próximo a "VENCIMENTO".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "11/04/2025", "28/03/2025", "16/04/2025", "16/06/2025", "26/01/2026"

8. proximo_leitura: Procure na tabela "DATAS DE LEITURAS", na linha "PRÓXIMA LEITURA".
   - Formato: "DD/MM/AAAA"
   - Se aparecer só "DD/MM", complete o ano baseado no mes_referencia
   - A data deve ser FUTURA em relação ao mes_referencia

9. aliquota_icms: Procure na tabela "ITENS DE FATURA" ou na tabela "TRIBUTO", na coluna "ALÍQUOTA ICMS (%)" na linha ICMS.
   - Valores comuns: 20.00, 20.50
   - Converta "20,00" ou "20.00" para 20.0
   - Se não encontrar, use null

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer "TARIFA SOCIAL DE ENERGIA ELÉTRICA" ou "BAIXA RENDA" na classificação
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos com valores diferentes na seção "REAVISO DE CONTAS VENCIDAS" ou mensagem sobre débitos, então valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure APENAS na seção que menciona débitos anteriores ou mensagem como "Até a emissão desta fatura você não possui débitos para esse código de cliente"
- Se aparecer "você não possui débitos" → valores_em_aberto = [], faturas_venc = false
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção que menciona débitos anteriores
- Se encontrar mensagem "você não possui débitos" → valores_em_aberto = [], faturas_venc = false → PARE AQUI
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

consumo_lista: Procure na seção "HISTÓRICO DE CONSUMO" ou "CONSUMO FATURADO" (gráfico de barras).
- Extraia na ORDEM EXATA que aparece na tabela/gráfico
- Formato mes_ano: "MM/AAAA" (ex: "03/2025", "05/2025")
- Se aparecer formato abreviado (ex: "MAR 25", "MAI 25"), converta:
  - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
  - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "COELBA" ou "NEOENERGIA COELBA"
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão" (geralmente não aparece, use "")
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
