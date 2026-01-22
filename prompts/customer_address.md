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
- rua: Nome da rua/avenida SEM o número. Se encontrar "RUA EXEMPLO 140", coloque apenas "RUA EXEMPLO" no campo rua
- numero: Número do endereço (apenas o número). Se encontrar "RUA EXEMPLO 140", coloque "140" no campo numero
- complemento: Complemento do endereço (apto, bloco, etc.) ou "" se não houver
- bairro: Nome COMPLETO do bairro incluindo prefixos como "JARDIM", "VILA", "CONJUNTO", "PARQUE", "SETOR", "RESIDENCIAL", etc.
  - CRÍTICO: SEMPRE extraia o nome completo do bairro como aparece na fatura, incluindo TODOS os prefixos
  - Se aparecer "JARDIM PRIMAVERA" → use "JARDIM PRIMAVERA" (NUNCA apenas "PRIMAVERA")
  - Se aparecer "VILA NOVA" → use "VILA NOVA" (NUNCA apenas "NOVA")
  - Se aparecer "CONJUNTO HABITACIONAL X" → use "CONJUNTO HABITACIONAL X" completo
  - Se aparecer "PARQUE DAS FLORES" → use "PARQUE DAS FLORES" (NUNCA apenas "FLORES")
  - Se aparecer "SETOR COMERCIAL" → use "SETOR COMERCIAL" completo
  - Se aparecer "RESIDENCIAL ABC" → use "RESIDENCIAL ABC" completo
  - ATENÇÃO: Leia TUDO que aparece antes do nome do bairro. Se houver "JARDIM", "VILA", "CONJUNTO", etc., inclua no campo bairro
- cidade: Nome da cidade
- estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP")
- cep: CEP do endereço no formato "00000-000" ou "00000000" (com ou sem hífen)

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente. NÃO inclua dados da distribuidora.
- NÃO extraia o nome do cliente nesta análise - apenas o endereço.
- Se não encontrar algum campo, use "" (string vazia).
