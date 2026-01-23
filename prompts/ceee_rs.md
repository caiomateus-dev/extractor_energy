Concessionária: CEEE

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA DESTACADA (vermelha, laranja ou verde) no canto SUPERIOR DIREITO da fatura, rotulada como "Número da UC" ou "Nº da UC". 
   - Formato: números simples sem máscara (ex: "63798891", "41005325", "58850015", "71354751")
   - Aparece sempre em uma caixa colorida destacada no topo direito
   - NUNCA use código de barras do rodapé
   - NUNCA use "Parceiro de Negócio" (esse é cod_cliente)

2. classificacao: Procure próximo a "Classificação:" na seção superior da fatura. 
   - Aparece como "Classificação: RESIDENCIAL" (pode aparecer duplicado "RESIDENCIAL RESIDENCIAL" - ignore a duplicação)
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

3. tipo_instalacao: Procure próximo a "Tipo de Fornecimento:" ou "Tipo de tarifa:". 
   - Se aparecer "Tipo de Fornecimento: MONOFÁSICO" → use "MONOFASICO" (sem acento)
   - Se aparecer "Tipo de Fornecimento: BIFÁSICO" → use "BIFASICO" (sem acento)
   - Se aparecer "Tipo de Fornecimento: TRIFÁSICO" → use "TRIFASICO" (sem acento)
   - ATENÇÃO: "Tipo de tarifa: CONVENCIONAL" NÃO é tipo de instalação. Se só aparecer "CONVENCIONAL", procure por "Tipo de Fornecimento" em outra parte da fatura.
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico" com acento. SEMPRE MAIÚSCULAS e SEM ACENTO.

4. mes_referencia: Procure em uma CAIXA AMARELA ou destacada rotulada como "Conta mês" na seção superior da fatura. 
   - Formato: "MM/AAAA" (sempre numérico, ex: "09/2025", "01/2026", "08/2025", "10/2025")
   - Se aparecer formato abreviado (ex: "OUT/2025", "SET/2025"), converta para numérico:
     - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
     - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
     - Exemplo: "OUT/2025" → "10/2025", "SET/2025" → "09/2025"

5. vencimento: Procure em uma CAIXA AMARELA ou destacada rotulada como "Vencimento" próxima à "Conta mês". 
   - Formato: "DD/MM/AAAA" (ex: "15/10/2025", "09/02/2026", "12/09/2025", "20/12/2025")

6. proximo_leitura: Procure próximo a "Próxima Leitura:" ou "Próxima leitura:" na seção de leituras do medidor. 
   - Pode aparecer vazio em algumas faturas - se não encontrar, use ""
   - Se aparecer só "DD/MM", complete o ano baseado no mes_referencia
   - Formato: "DD/MM/AAAA". A data deve ser FUTURA em relação ao mes_referencia
   - Exemplo: se mes_referencia = "10/2025" e próxima leitura = "24/11", então proximo_leitura = "24/11/2025"

7. valor_fatura: Procure em uma CAIXA VERMELHA ou VERDE destacada rotulada como "Total a pagar" ou "Total a Pagar" na seção superior da fatura. 
   - Aparece sempre em uma caixa colorida destacada
   - Remova "R$" e separadores de milhar (ex: "R$ 199,62" → 199.62, "R$249,06" → 249.06)

8. aliquota_icms: Procure na tabela "Itens da Fatura" ou "Itens da fatura" na coluna "Alíquota ICMS" ou "Alíquota ICMS (RS)". 
   - Aparece como porcentagem (ex: "17%", "18%")
   - Converta "17%" para 17.0, "18%" para 18.0
   - Se aparecer "17,00" ou "18.00", converta para 17.0 ou 18.0
   - Se não encontrar na tabela de itens, use null

9. consumo_lista: Procure na seção "Histórico de Consumo" ou "HISTÓRICO DE CONSUMO KWH" que geralmente aparece no meio da fatura com um gráfico de barras e uma tabela.
   - A tabela tem colunas "Mês/Ano" ou "Mês" e "Consumo (KWh)" ou "Consumo kWh"
   - Formato do mês/ano pode variar:
     * "2025 OUT" ou "OUT 2025" → converta para "10/2025"
     * "2025 AGO" ou "AGO 2025" → converta para "08/2025"
     * "DEC.24" ou "DEZ 2024" → converta para "12/2024"
   - Se aparecer só o mês abreviado (ex: "JUL", "AGO"), use o ano do mes_referencia ou do contexto
   - Extraia o consumo como número inteiro (ex: "141,0" → 141, "216" → 216)
   - Mantenha a ordem exata que aparece na tabela

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer EXATAMENTE "BAIXA RENDA" na classificação/modalidade
- ths_verde: true apenas se aparecer explicitamente "THS VERDE" ou "TARIFA HIDRO VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos com valores diferentes na seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES", então valores_em_aberto = [] e faturas_venc = false.

EXEMPLO DE ERRO GRAVE (NUNCA FAÇA ISSO):
- Se você retornar valores_em_aberto com todos os valores iguais (ex: todos 18.0) → ERRADO
- Se você retornar valores_em_aberto com valores iguais à aliquota_icms → ERRADO  
- Se você retornar valores_em_aberto incluindo o mes_referencia atual → ERRADO
- Se você retornar valores_em_aberto sem encontrar uma lista clara na seção de débitos → ERRADO

Se você tiver qualquer dúvida, retorne valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure PRIMEIRO na seção "REAVISO DE VENCIMENTO" ou "REAVISO DE CONTAS VENCIDAS" no rodapé da fatura
- Se não encontrar nessa seção, verifique na tabela "Itens da Fatura" por linhas como:
  * "MULTA CONTA ANTERIOR" ou "MULTA/CONTA ANTERIOR"
  * "JUROS CONTA ANTERIOR" ou "JUROS/CONTA ANTERIOR"
  * "CORREÇÃO MONETÁRIA POR ATRASO" ou "CORR MONET CONTR"
- ATENÇÃO: Se encontrar "MULTA CONTA ANTERIOR" ou "JUROS CONTA ANTERIOR" na tabela de itens, isso indica débitos anteriores, mas NÃO extraia esses valores diretamente como valores_em_aberto. Esses são multas/juros sobre débitos anteriores, não os débitos em si.
- Para valores_em_aberto, você precisa encontrar uma LISTA de débitos com mês/ano e valor de fatura anterior
- Esta seção geralmente aparece no meio ou rodapé da fatura
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "REAVISO DE VENCIMENTO" ou "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" na fatura
- Esta seção geralmente aparece no rodapé da fatura, pode estar vazia ou com padrão hachurado
- Se NÃO encontrar essa seção OU se ela estiver vazia → valores_em_aberto = [], faturas_venc = false → PARE AQUI
- ATENÇÃO: A presença de "MULTA CONTA ANTERIOR" ou "JUROS CONTA ANTERIOR" na tabela de itens NÃO significa que há valores_em_aberto. Esses são multas/juros sobre débitos anteriores, mas você precisa encontrar a lista de débitos anteriores para preencher valores_em_aberto.

PASSO 2: VERIFIQUE se a seção está VAZIA:
- Se a seção existir mas não tiver NENHUMA linha de débito listada (apenas o título, sem valores abaixo)
- Se a seção estiver em branco ou com padrão hachurado
- Se não houver nenhum mês/ano e valor listados na seção
- Se a seção mostrar apenas o título mas sem conteúdo abaixo
- Se você não conseguir identificar claramente linhas de débitos com mês/ano e valor
- Se você ver apenas o título da seção mas sem uma TABELA ou LISTA de débitos abaixo
→ valores_em_aberto = []
→ faturas_venc = false
→ PARE AQUI, não procure valores em outras partes da fatura
→ NUNCA invente ou copie valores de outras seções (aliquota_icms, valores faturados, etc.)

PASSO 3: Se a seção tiver DÉBITOS LISTADOS (com linhas contendo mês/ano e valor):
   → Para cada linha de débito EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha do débito)
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha)
   → VALIDAÇÃO CRÍTICA: O valor deve ser um valor de FATURA (geralmente dezenas ou centenas de reais)
   → VALIDAÇÃO CRÍTICA: O valor NUNCA pode ser igual à aliquota_icms (ex: se aliquota_icms = 18.0, então NUNCA use 18.0)
   → VALIDAÇÃO CRÍTICA: O valor NUNCA pode ser o mesmo para todos os meses (isso indica que está copiando valor errado)
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
     - Se for FUTURO → IGNORE
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false

VALIDAÇÃO FINAL OBRIGATÓRIA - ANTES DE RETORNAR O JSON, VERIFIQUE:

1. Se você não encontrou uma seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" com uma LISTA CLARA de débitos → valores_em_aberto = [] e faturas_venc = false

2. Se a seção existir mas estiver VAZIA (sem linhas de débitos) → valores_em_aberto = [] e faturas_venc = false

3. Se TODOS os valores em valores_em_aberto forem iguais entre si (ex: todos 18.0, todos 10.0) → valores_em_aberto = [] e faturas_venc = false (isso indica erro)

4. Se algum valor em valores_em_aberto for igual à aliquota_icms → valores_em_aberto = [] e faturas_venc = false (isso indica que você copiou valor errado)

5. Se valores_em_aberto contiver o mes_referencia atual → valores_em_aberto = [] e faturas_venc = false (isso está ERRADO)

6. Se você não tiver CERTEZA ABSOLUTA de que encontrou débitos anteriores válidos na seção correta → valores_em_aberto = [] e faturas_venc = false

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false
- É melhor retornar vazio do que retornar valores errados
- NUNCA invente valores
- NUNCA copie valores de outras seções (aliquota_icms, valores faturados, tabelas, etc.)

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "CEEE"
- tensao_nominal: procurar por "Tensão Nominal:" ou "Tensão Nominal Dip:" na seção superior. 
  - Pode aparecer como "127V", "220V" ou "220-220 V"
  - Extraia apenas o valor numérico com unidade (ex: "127V", "220V")
- conta_contrato: sempre null
- cod_cliente: pode aparecer como "Parceiro de Negócio" em uma caixa azul acima do "Número da UC". 
  - Se aparecer "Parceiro de Negócio" com um número, use esse número
  - Se não aparecer, use null
  - NUNCA confunda com num_instalacao (que é "Número da UC")
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
