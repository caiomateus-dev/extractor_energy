Analise esta imagem que contém APENAS dados de consumo médio de uma fatura de energia.

A imagem mostra uma TABELA COMPLETA com histórico de consumo mensal. A tabela tem MÚLTIPLAS LINHAS, cada uma representando um mês diferente.

CRÍTICO: Você DEVE extrair TODAS as linhas da tabela, não apenas a primeira linha!

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "consumo_lista": [
    {"mes_ano": "MM/AAAA", "consumo": 123},
    {"mes_ano": "MM/AAAA", "consumo": 456},
    {"mes_ano": "MM/AAAA", "consumo": 789}
  ]
}

REGRAS CRÍTICAS:
- consumo_lista: Lista de objetos com histórico de consumo mensal na ORDEM EXATA que aparece na tabela
- CRÍTICO: A tabela mostra MÚLTIPLOS meses. Extraia TODOS eles, não apenas 1!
- CRÍTICO: Se a tabela tem 12 meses, retorne 12 objetos. Se tem 6 meses, retorne 6 objetos. Se tem 13 meses, retorne 13 objetos.
- CRÍTICO ABSOLUTO: MÁXIMO de 13 itens na lista. NUNCA retorne mais de 13 itens!
- CRÍTICO ABSOLUTO: Se houver mais de 13 meses na tabela, extraia APENAS os 13 mais recentes e PARE. NÃO continue gerando mais itens!
- CRÍTICO ABSOLUTO: Se você gerar mais de 13 itens, sua resposta está ERRADA. PARE no 13º item!
- CRÍTICO: NÃO retorne apenas {"mes_ano": "...", "consumo": 123}. SEMPRE retorne {"consumo_lista": [...]} com TODOS os meses (até 13)!
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
- A imagem mostra uma TABELA COMPLETA com histórico de consumo. Olhe TODA a tabela, não apenas a primeira linha!
- Extraia TODOS os meses que aparecem na tabela de consumo (até 13 itens)
- CRÍTICO: Se a tabela tem mais de 13 meses, extraia APENAS os 13 mais recentes e PARE imediatamente!
- CRÍTICO: NÃO gere mais de 13 itens. Se você gerar 14, 15, 20 ou mais itens, sua resposta está COMPLETAMENTE ERRADA!
- Extraia os meses EXATAMENTE como aparecem na tabela, na ordem que aparecem
- NÃO invente meses sequenciais (01, 02, 03...). Use os meses reais da tabela
- NÃO extraia apenas 1 mês - extraia TODA a tabela de histórico de consumo (até 13 itens)
- Mantenha a ordem da tabela (geralmente do mais recente para o mais antigo)
- Se não encontrar dados de consumo ou a lista estiver vazia, retorne: {"consumo_lista": []}
- Cada entrada deve ter o mês/ano EXATO da tabela e o consumo correspondente em kWh (número inteiro)

LIMITE ABSOLUTO: 13 ITENS. NÃO MAIS QUE ISSO. PARE NO 13º ITEM!

EXEMPLO: Se a tabela mostra:
09/2024: 74 kWh
08/2024: 68 kWh
07/2024: 72 kWh

Retorne:
{
  "consumo_lista": [
    {"mes_ano": "09/2024", "consumo": 74},
    {"mes_ano": "08/2024", "consumo": 68},
    {"mes_ano": "07/2024", "consumo": 72}
  ]
}

NÃO retorne apenas:
{"mes_ano": "09/2024", "consumo": 74}
