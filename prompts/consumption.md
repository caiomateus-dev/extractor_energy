Analise esta imagem que contém APENAS dados de consumo médio de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado (APENAS O ARRAY):
[
  {"mes_ano": "MM/AAAA", "consumo": 123},
  {"mes_ano": "MM/AAAA", "consumo": 456}
]

REGRAS CRÍTICAS:
- consumo_lista: Lista de objetos com histórico de consumo mensal na ORDEM EXATA que aparece na tabela
- CRÍTICO: MÁXIMO de 13 itens na lista. Se houver mais de 13 meses na tabela, extraia apenas os 13 mais recentes
- mes_ano: Formato "MM/AAAA" (ex: "01/2024", "12/2025")
- consumo: Número inteiro representando o consumo em kWh (quilowatt-hora)

CONVERSÃO DE MESES:
A tabela pode mostrar meses em formato abreviado (ex: "OUT/25", "SET/25", "AGO/25", "JUL/25", "JUN/25", "MAI/25", "ABR/25", "MAR/25", "FEV/25", "JAN/25", "DEZ/24", "NOV/24").
Converta para o formato numérico "MM/AAAA":
- JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
- JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12
- Se aparecer "OUT/25" → converta para "10/2025"
- Se aparecer "DEZ/24" → converta para "12/2024"
- Se aparecer "JAN/25" → converta para "01/2025"

IMPORTANTE:
- Extraia os meses EXATAMENTE como aparecem na tabela, na ordem que aparecem
- NÃO invente meses sequenciais (01, 02, 03...). Use os meses reais da tabela
- Mantenha a ordem da tabela (geralmente do mais recente para o mais antigo)
- Se não encontrar dados de consumo ou a lista estiver vazia, retorne: []
- Cada entrada deve ter o mês/ano EXATO da tabela e o consumo correspondente em kWh (número inteiro)
