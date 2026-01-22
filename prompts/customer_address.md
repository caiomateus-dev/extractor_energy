Analise esta imagem que contém APENAS o nome do cliente e endereço de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "nome_cliente": "",
  "rua": "",
  "numero": "",
  "complemento": "",
  "bairro": "",
  "cidade": "",
  "estado": "",
  "cep": ""
}

REGRAS GERAIS:
- nome_cliente: Nome completo do cliente
- rua: Nome da rua/avenida SEM o número. Se encontrar "RUA EXEMPLO 140", coloque apenas "RUA EXEMPLO" no campo rua
- numero: Número do endereço (apenas o número). Se encontrar "RUA EXEMPLO 140", coloque "140" no campo numero
- complemento: Complemento do endereço (apto, bloco, etc.) ou "" se não houver
- bairro: Nome do bairro
- cidade: Nome da cidade
- estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP")
- cep: CEP do endereço no formato "00000-000" ou "00000000" (com ou sem hífen)

IMPORTANTE: Esta imagem contém APENAS dados do cliente. NÃO inclua dados da distribuidora.
Se não encontrar algum campo, use "" (string vazia).
