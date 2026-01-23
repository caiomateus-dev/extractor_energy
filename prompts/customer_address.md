Analise esta imagem que contém APENAS o endereço do cliente de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "rua": "",
  "numero": "",
  "complemento": "",
  "bairro": "",
  "cidade": "",
  "estado": "",
  "cep": ""
}

REGRAS GERAIS:
- rua: Nome completo da rua/avenida SEM complementos. Se aparecer "RUA" ou "AVENIDA" seguido de números e depois vírgula com complementos (Quadra, Lote, etc.), extraia APENAS o nome da rua com o número após "RUA"/"AVENIDA". O número após "RUA"/"AVENIDA" faz parte do nome da rua, não é o número do endereço. NÃO inclua Quadra, Lote ou outros complementos no campo rua.
- numero: Número do endereço. Se aparecer "S/N" ou "Sem Número" no endereço, coloque "S/N" no campo numero (NUNCA em complemento). Se houver um número explícito de endereço, extraia-o.
- complemento: Complemento do endereço (Quadra (Q.), Lote (L.), apto, bloco, etc.) ou "" se não houver. 
  - Se aparecer "Q. 11, L. 22", extraia "Q. 11, L. 22" completo (incluindo "Q." e "L.")
  - Se aparecer apenas "Q. 11", extraia "Q. 11" completo
  - Se aparecer apenas "L. 22", extraia "L. 22" completo
  - Se aparecer "S/N" junto com complemento (ex: "Q. 11, L. 22, S/N"), extraia apenas o complemento sem o S/N: "Q. 11, L. 22"
  - CRÍTICO: NÃO extraia apenas números soltos como "22" ou "11". O complemento DEVE incluir a identificação completa (Q., L., Apto., Bloco, etc.)
  - Se não houver complemento visível na imagem, use "" (string vazia)
- bairro: Nome COMPLETO do bairro incluindo prefixos como "JARDIM", "VILA", "CONJUNTO", "PARQUE", "SETOR", "RESIDENCIAL", etc.
  - CRÍTICO: SEMPRE extraia o nome completo do bairro como aparece na fatura, incluindo TODOS os prefixos
  - Se aparecer "JARDIM PRIMAVERA" → use "JARDIM PRIMAVERA" (NUNCA apenas "PRIMAVERA")
  - Se aparecer "VILA NOVA" → use "VILA NOVA" (NUNCA apenas "NOVA")
  - Se aparecer "CONJUNTO HABITACIONAL X" → use "CONJUNTO HABITACIONAL X" completo
  - Se aparecer "PARQUE DAS FLORES" → use "PARQUE DAS FLORES" (NUNCA apenas "FLORES")
  - Se aparecer "SETOR COMERCIAL" → use "SETOR COMERCIAL" completo
  - Se aparecer "RESIDENCIAL ABC" → use "RESIDENCIAL ABC" completo
  - ATENÇÃO: Leia TUDO que aparece antes do nome do bairro. Se houver "JARDIM", "VILA", "CONJUNTO", etc., inclua no campo bairro
- cidade: Nome da cidade que aparece ANTES da sigla do estado na linha do endereço. NÃO use cidade de outras partes da fatura (como cidade da distribuidora ou cidade de outras seções). Extraia APENAS a cidade que aparece na linha do endereço do cliente.
- estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP", "GO") que aparece após o nome da cidade na linha do endereço. CRÍTICO: Extraia APENAS o estado que aparece na linha do endereço do cliente. NÃO use estado de outras partes da fatura.
- cep: CEP do endereço. Procure por "CEP:" seguido de números na linha do endereço. Extraia TODOS os números após "CEP:" (o CEP tem 8 dígitos). NÃO use CEPs de outras partes da fatura. Se aparecer "CEP: 75402700", extraia "75402700" (8 dígitos completos). Se aparecer "CEP: 65.000-000" ou similar, extraia apenas os números: "65000000".

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NÃO use valores de outras partes da fatura (como cidade da distribuidora, CEPs de outras seções, etc.)
- Se a imagem estiver ilegível ou um campo não estiver visível, use "" (string vazia)
- É MELHOR retornar campos vazios do que inventar valores incorretos
- NUNCA invente ou adivinhe valores baseado em contexto ou outras informações

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente. NÃO inclua dados da distribuidora.
- NÃO extraia o nome do cliente nesta análise - apenas o endereço.
- Se não encontrar algum campo, use "" (string vazia).
