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
- complemento: Complemento do endereço (Quadra (Q.), Lote (L.), apto, bloco, etc.) ou "" se não houver. Se aparecer "S/N" junto com complemento, extraia apenas o complemento (sem o S/N). O S/N vai para o campo numero.
- bairro: Nome COMPLETO do bairro incluindo prefixos como "JARDIM", "VILA", "CONJUNTO", "PARQUE", "SETOR", "RESIDENCIAL", etc.
  - CRÍTICO: SEMPRE extraia o nome completo do bairro como aparece na fatura, incluindo TODOS os prefixos
  - Se aparecer "JARDIM PRIMAVERA" → use "JARDIM PRIMAVERA" (NUNCA apenas "PRIMAVERA")
  - Se aparecer "VILA NOVA" → use "VILA NOVA" (NUNCA apenas "NOVA")
  - Se aparecer "CONJUNTO HABITACIONAL X" → use "CONJUNTO HABITACIONAL X" completo
  - Se aparecer "PARQUE DAS FLORES" → use "PARQUE DAS FLORES" (NUNCA apenas "FLORES")
  - Se aparecer "SETOR COMERCIAL" → use "SETOR COMERCIAL" completo
  - Se aparecer "RESIDENCIAL ABC" → use "RESIDENCIAL ABC" completo
  - ATENÇÃO: Leia TUDO que aparece antes do nome do bairro. Se houver "JARDIM", "VILA", "CONJUNTO", etc., inclua no campo bairro
- cidade: Nome da cidade que aparece ANTES da sigla do estado na linha do endereço. NÃO use cidade de outras partes da fatura (como cidade da distribuidora ou cidade de outras seções).
- estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP", "GO") que aparece após o nome da cidade na linha do endereço.
- cep: CEP do endereço. Procure por "CEP:" seguido de números na linha do endereço. Extraia TODOS os números após "CEP:" (o CEP tem 8 dígitos). NÃO use CEPs de outras partes da fatura.

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente. NÃO inclua dados da distribuidora.
- NÃO extraia o nome do cliente nesta análise - apenas o endereço.
- Se não encontrar algum campo, use "" (string vazia).
