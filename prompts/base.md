Analise a imagem da fatura de energia e extraia os dados solicitados.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado (todas as chaves são obrigatórias):

{
  "cod_cliente": "",
  "conta_contrato": "",
  "complemento": "",
  "distribuidora": "",
  "num_instalacao": "",
  "classificacao": "",
  "tipo_instalacao": "",
  "tensao_nominal": "",
  "alta_tensao": false,
  "mes_referencia": "",
  "valor_fatura": 0.0,
  "vencimento": "",
  "proximo_leitura": "",
  "aliquota_icms": null,
  "baixa_renda": false,
  "energia_ativa_injetada": false,
  "energia_reativa": false,
  "orgao_publico": false,
  "parcelamentos": false,
  "tarifa_branca": false,
  "ths_verde": false,
  "faturas_venc": false,
  "valores_em_aberto": [],
  "nome_cliente": ""
}

REGRAS IMPORTANTES:

1. Strings: Use "" (vazia) se não encontrar o valor
2. valor_fatura: Número float com ponto decimal. Remova "R$" e separadores de milhar. Exemplo: "R$ 1.234,56" vira 1234.56
3. aliquota_icms: Número (ex: 0, 10, 12, 18, 19, 22, 23, 23,5) ou null se não existir
4. Booleanos: true ou false (nunca "sim"/"não")
5. valores_em_aberto: Lista de objetos {"mes_ano": "MM/AAAA", "valor": 123.45} ou [] se vazio. 
   CRÍTICO: NUNCA inclua a fatura atual (mes_referencia) nesta lista. Apenas débitos de meses ANTERIORES ao mes_referencia.
   VALIDAÇÃO OBRIGATÓRIA ANTES DE RETORNAR:
   - Se TODOS os valores forem iguais (ex: todos 18.0) → valores_em_aberto = []
   - Se algum valor for igual à aliquota_icms → valores_em_aberto = []
   - Se contiver o mes_referencia atual → valores_em_aberto = []
   - Se não encontrar uma seção clara de débitos anteriores na fatura → valores_em_aberto = []
6. Datas:
   - mes_referencia: formato "MM/AAAA" (ex: "01/2024", "10/2025"). 
     CRÍTICO: Se a fatura mostrar mês abreviado (ex: "OUT/2025", "SET/2025"), converta para formato numérico:
     - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
     - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
     - Exemplo: "OUT/2025" → "10/2025", "SET/2025" → "09/2025"
   - vencimento e proximo_leitura: formato "DD/MM/AAAA" (ex: "15/01/2024")
   - vencimento e proximo_leitura nunca devem ser iguais
7. Se houver débitos anteriores (meses anteriores ao mes_referencia): faturas_venc = true e preencha valores_em_aberto APENAS com esses débitos anteriores
8. Se não houver débitos anteriores ou se a seção estiver vazia: faturas_venc = false e valores_em_aberto = []
9. nome_cliente: Nome completo do cliente conforme aparece na fatura. O nome do cliente é APENAS a primeira linha da seção de identificação do cliente.
   REGRAS CRÍTICAS PARA EXTRAÇÃO:
   - O nome do cliente é SEMPRE a primeira informação textual na seção de identificação do cliente
   - Se a primeira linha contém múltiplas palavras separadas por espaços, vírgulas ou hífens, analise cuidadosamente:
     * O nome do cliente geralmente é curto (1 a 4 palavras): nome próprio, sobrenome, ou razão social simples
     * Se aparecer uma palavra que parece ser nome de cidade (palavras comuns de cidades brasileiras), essa palavra e tudo depois dela NÃO faz parte do nome
     * Se aparecer sigla de estado (2 letras maiúsculas como MG, SP, RJ, RS, etc.), essa sigla e tudo antes dela que seja nome de cidade NÃO faz parte do nome
     * Se aparecer CEP (formato numérico com ou sem hífen), tudo a partir do CEP NÃO faz parte do nome
     * Se aparecer hífen seguido de sigla de estado, tudo a partir do hífen NÃO faz parte do nome
   - PROCESSAMENTO: Identifique onde termina o nome pessoal/empresarial e começa a informação geográfica (cidade/estado/CEP). Extraia SOMENTE a parte do nome, parando antes da primeira informação geográfica identificada.
   - O campo nome_cliente contém EXCLUSIVAMENTE o nome da pessoa física ou razão social da empresa, SEM qualquer informação geográfica. 

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar explicitamente um campo na fatura, use o valor padrão ("" para strings, null para opcionais, false para booleanos, [] para listas)
- NÃO extraia valores de campos que não correspondem ao que está sendo solicitado
- NÃO use valores de outras seções da fatura para preencher campos que não existem
- Se um campo não existe na fatura (como conta_contrato em algumas concessionárias), use null (NÃO invente um valor)
- Se não encontrar uma seção específica (como "REAVISO DE VENCIMENTO"), retorne valores vazios ([] para listas, false para booleanos)
- É MELHOR retornar valores vazios/null do que inventar valores incorretos
