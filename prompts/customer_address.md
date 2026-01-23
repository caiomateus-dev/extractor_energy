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
- rua: Nome completo da rua/avenida. Se aparecer "RUA" ou "AVENIDA" seguido de números, esses números podem fazer parte do nome da rua (não necessariamente o número do endereço).
- numero: Número do endereço. Se aparecer "S/N" ou "Sem Número", coloque "S/N" no campo numero (NUNCA em complemento).
- complemento: Complemento do endereço (apto, bloco, Quadra (Q.), Lote (L.), etc.) ou "" se não houver. Se aparecer "S/N" junto com complemento, extraia apenas o complemento (sem o S/N).
- bairro: Nome COMPLETO do bairro incluindo prefixos como "JARDIM", "VILA", "CONJUNTO", "PARQUE", "SETOR", "RESIDENCIAL", etc.
  - CRÍTICO: SEMPRE extraia o nome completo do bairro como aparece na fatura, incluindo TODOS os prefixos
  - Se aparecer "JARDIM PRIMAVERA" → use "JARDIM PRIMAVERA" (NUNCA apenas "PRIMAVERA")
  - Se aparecer "VILA NOVA" → use "VILA NOVA" (NUNCA apenas "NOVA")
  - Se aparecer "CONJUNTO HABITACIONAL X" → use "CONJUNTO HABITACIONAL X" completo
  - Se aparecer "PARQUE DAS FLORES" → use "PARQUE DAS FLORES" (NUNCA apenas "FLORES")
  - Se aparecer "SETOR COMERCIAL" → use "SETOR COMERCIAL" completo
  - Se aparecer "RESIDENCIAL ABC" → use "RESIDENCIAL ABC" completo
  - ATENÇÃO: Leia TUDO que aparece antes do nome do bairro. Se houver "JARDIM", "VILA", "CONJUNTO", etc., inclua no campo bairro
- cidade: Nome da cidade que aparece na linha do endereço. NÃO use cidade de outras partes da fatura.
- estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP")
- cep: CEP do endereço. Procure por "CEP:" seguido de números na linha do endereço. Extraia apenas os números (sem formatação). NÃO use CEPs de outras partes da fatura.

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente. NÃO inclua dados da distribuidora.
- NÃO extraia o nome do cliente nesta análise - apenas o endereço.
- Se não encontrar algum campo, use "" (string vazia).
