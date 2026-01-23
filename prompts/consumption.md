Analise esta imagem que contém APENAS dados de consumo médio de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "consumo_lista": [
    {"mes_ano": "MM/AAAA", "consumo": 123},
    {"mes_ano": "MM/AAAA", "consumo": 456}
  ]
}

REGRAS CRÍTICAS:
- Extraia APENAS os meses que aparecem na tabela. NÃO invente meses sequenciais!
- Conte quantas linhas a tabela tem e retorne APENAS essas linhas (máximo 13)
- Se a tabela tem 6 meses, retorne 6. Se tem 12, retorne 12. NÃO complete até 12 meses!
- Cada mês deve ter seu próprio valor da tabela. NÃO repita o mesmo valor para todos!
- O consumo é o número EXATO da tabela. Se mostra "90", retorne 90. NÃO multiplique por 1000!
- mes_ano: Formato "MM/AAAA". Se a tabela mostra meses abreviados (OUT/25, SET/25), converta para numérico (10/2025, 09/2025)
- consumo: Número inteiro em kWh, exatamente como aparece na tabela

CONVERSÃO DE MESES:
JAN=01, FEV=02, MAR=03, ABR=04, MAI=05, JUN=06, JUL=07, AGO=08, SET=09, OUT=10, NOV=11, DEZ=12

EXEMPLO:
Tabela mostra: OUT/24: 74, SET/24: 68, AGO/24: 72
Retorne: {"consumo_lista": [{"mes_ano": "10/2024", "consumo": 74}, {"mes_ano": "09/2024", "consumo": 68}, {"mes_ano": "08/2024", "consumo": 72}]}

NÃO faça:
- Inventar meses que não estão na tabela
- Completar sequência até 12 meses
- Multiplicar valores por 1000
- Repetir o mesmo valor para todos os meses
