Concessionária: CELESC

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA DESTACADA (amarela, laranja ou verde) no canto SUPERIOR DIREITO da fatura, rotulada como "UNIDADE CONSUMIDORA". 
   - Formato: números simples sem máscara (ex: "24019349", "27544088", "31972094", "50343014", "10984157")
   - Aparece sempre em uma caixa colorida destacada no topo direito
   - NUNCA use código de barras do rodapé
   - NUNCA use "Cliente:" ou "Cliente No." (esse é cod_cliente)

2. cod_cliente: Procure próximo a "Cliente:" ou "Cliente No." na seção superior da fatura. 
   - Aparece como um número separado do num_instalacao
   - Se não encontrar, use null

3. classificacao: Procure próximo a "Classificação / Modalidade Tarifária / Tipo de Fornecimento:" na seção superior da fatura. 
   - Aparece como "RESIDENCIAL" (pode aparecer duplicado "RESIDENCIAL - RESIDENCIAL" - ignore a duplicação)
   - Se aparecer "RESIDENCIAL BAIXA RENDA" → classificacao = "RESIDENCIAL" e baixa_renda = true
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Classificação / Modalidade Tarifária / Tipo de Fornecimento:" na mesma linha ou próxima. 
   - Aparece como "MONOFASICO", "BIFASICO" ou "TRIFASICO"
   - Pode aparecer junto com a classificação (ex: "RESIDENCIAL - RESIDENCIAL - MONOFASICO")
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico" com acento. SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure próximo a "REFERÊNCIA" ou "REFERENCIA" na seção superior da fatura. 
   - Formato: "MM/AAAA" (sempre numérico, ex: "08/2025", "09/2025", "10/2025", "12/2025")
   - Se aparecer formato abreviado (ex: "OUT/2025", "SET/2025"), converta para numérico:
     - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
     - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
     - Exemplo: "OUT/2025" → "10/2025", "SET/2025" → "09/2025"

6. vencimento: Procure próximo a "VENCIMENTO" na seção superior da fatura. 
   - Formato: "DD/MM/AAAA" (ex: "01/09/2025", "10/10/2025", "10/11/2025", "26/12/2025", "12/01/2026")

7. proximo_leitura: Procure próximo a "Próxima Leitura" na seção de leituras do medidor. 
   - Formato: "DD/MM/AAAA" (ex: "08/09/2025", "21/10/2025", "18/11/2025", "05/01/2026", "22/01/2026")
   - Pode aparecer vazio em algumas faturas - se não encontrar, use ""

8. valor_fatura: Procure em uma CAIXA DESTACADA (amarela, verde ou destacada) rotulada como "TOTAL A PAGAR" na seção superior da fatura. 
   - Aparece sempre em uma caixa colorida destacada
   - Remova "R$" e separadores de milhar (ex: "R$ 118,84" → 118.84, "R$ 355,28" → 355.28)

9. aliquota_icms: Procure na tabela de "Tributos" ou na tabela "Itens de Fatura" na coluna "Alíquota ICMS (%)" ou "Alíquota (%)". 
   - Pode aparecer múltiplos valores (ex: "12,00" e "17,00") - use o valor mais comum ou o primeiro encontrado
   - Converta "12,00" para 12.0, "17,00" para 17.0
   - Se aparecer como porcentagem "12%" ou "17%", converta para 12.0 ou 17.0
   - Se não encontrar, use null

10. consumo_lista: Procure na seção "HISTÓRICO DE CONSUMO" ou "HISTORICO DE CONSUMO" que geralmente aparece no meio da fatura com um gráfico de barras e uma tabela.
    - A tabela tem colunas "Mês/Ano" ou "MES/ANO" e "Consumo (kWh)" ou "Consumo (KWh)" ou "Consumo kWh"
    - Formato do mês/ano pode variar:
      * "07/2025" ou "08/2025" → formato numérico direto
      * "DEZ/2024" ou "NOV/2024" → converta para numérico (DEZ = 12, NOV = 11)
      * "11/2024" ou "10/2024" → formato numérico direto
    - Se aparecer mês abreviado, converta:
      - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
      - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
    - Extraia o consumo como número inteiro (ex: "120" → 120, "150" → 150, "333" → 333)
    - Mantenha a ordem exata que aparece na tabela

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer EXATAMENTE "BAIXA RENDA" junto com a classificação (ex: "RESIDENCIAL BAIXA RENDA")
- ths_verde: true apenas se aparecer explicitamente "THS VERDE" ou "TARIFA HIDRO VERDE" ou se a "Bandeira Tarifária" for "Verde"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA" ou se houver consumo "TB" (Tarifa Branca) na tabela de itens
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos na seção "REAVISO DE DÉBITO" ou "Reaviso de débito", então valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure PRIMEIRO na seção "REAVISO DE DÉBITO" ou "Reaviso de débito" que aparece em uma CAIXA AMARELA destacada no meio da fatura
- Esta seção geralmente contém texto como: "ESTA UNIDADE CONSUMIDORA ESTÁ SUJEITA À SUSPENSÃO DE FORNECIMENTO... PELO NÃO PAGAMENTO DA(S) FATURA(S) REF. MM/AAAA, R$ valor"
- Se encontrar esse formato, extraia o mês/ano e valor mencionados (ex: "REF. 08/2025, R$ 312,64" → mes_ano: "08/2025", valor: 312.64)
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "REAVISO DE DÉBITO" ou "Reaviso de débito" na fatura (geralmente em caixa amarela destacada)
- Se NÃO encontrar essa seção → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 2: VERIFIQUE se a seção contém informações de débitos:
- Se a seção existir mas não mencionar valores de faturas anteriores → valores_em_aberto = [], faturas_venc = false → PARE AQUI
- Se a seção mencionar "REF. MM/AAAA, R$ valor" → extraia o mês/ano e valor
- Compare o mês/ano extraído com mes_referencia:
  - Se for IGUAL → IGNORE (é a fatura atual mencionada no aviso)
  - Se for ANTERIOR → adicione em valores_em_aberto e faturas_venc = true
  - Se for FUTURO → IGNORE

VALIDAÇÃO FINAL OBRIGATÓRIA - ANTES DE RETORNAR O JSON, VERIFIQUE:

1. Se você não encontrou a seção "REAVISO DE DÉBITO" com valores de faturas anteriores → valores_em_aberto = [] e faturas_venc = false

2. Se a seção existir mas não mencionar valores de débitos anteriores → valores_em_aberto = [] e faturas_venc = false

3. Se valores_em_aberto contiver o mes_referencia atual → valores_em_aberto = [] e faturas_venc = false (isso está ERRADO)

4. Se você não tiver CERTEZA ABSOLUTA de que encontrou débitos anteriores válidos na seção correta → valores_em_aberto = [] e faturas_venc = false

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false
- É melhor retornar vazio do que retornar valores errados
- NUNCA invente valores
- NUNCA copie valores de outras seções (aliquota_icms, valores faturados, tabelas, etc.)

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "CELESC"
- tensao_nominal: pode aparecer como "Grupo/Subgrupo Tensão: B1" ou similar, mas o valor explícito de tensão (ex: "127V", "220V") geralmente não aparece. Se não encontrar, use ""
- conta_contrato: pode aparecer como "Nosso Número" no rodapé da fatura. Se encontrar, use esse número. Se não encontrar, use null
- alta_tensao: geralmente false para instalações residenciais monofásicas/bifásicas/trifásicas. Se aparecer "Grupo/Subgrupo Tensão: A" ou similar (alta tensão), use true. Caso contrário, false
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
