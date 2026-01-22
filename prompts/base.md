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
  "nome_cliente": "",
  "rua": "",
  "numero": "",
  "complemento": "",
  "bairro": "",
  "cidade": "",
  "estado": "",
  "cep": ""
}

REGRAS IMPORTANTES:

1. Strings: Use "" (vazia) se não encontrar o valor
2. valor_fatura: Número float com ponto decimal. Remova "R$" e separadores de milhar. Exemplo: "R$ 1.234,56" vira 1234.56
3. aliquota_icms: Número (ex: 0, 10, 12, 18, 19, 22, 23, 23,5) ou null se não existir
4. Booleanos: true ou false (nunca "sim"/"não")
5. valores_em_aberto: Lista de objetos {"mes_ano": "MM/AAAA", "valor": 123.45} ou [] se vazio. 
   CRÍTICO: NUNCA inclua a fatura atual (mes_referencia) nesta lista. Apenas débitos de meses ANTERIORES ao mes_referencia.
6. Datas:
   - mes_referencia: formato "MM/AAAA" (ex: "01/2024")
   - vencimento e proximo_leitura: formato "DD/MM/AAAA" (ex: "15/01/2024")
7. Se houver débitos anteriores (meses anteriores ao mes_referencia): faturas_venc = true e preencha valores_em_aberto APENAS com esses débitos anteriores
8. Se não houver débitos anteriores ou se a seção estiver vazia: faturas_venc = false e valores_em_aberto = []
9. Endereço e Cliente:
   - nome_cliente: Nome completo do cliente (geralmente no topo da fatura)
   - rua: Nome da rua/avenida SEM o número. Se encontrar "RUA EXEMPLO 140", coloque apenas "RUA EXEMPLO" no campo rua
   - numero: Número do endereço (apenas o número). Se encontrar "RUA EXEMPLO 140", coloque "140" no campo numero
   - complemento: Complemento do endereço (apto, bloco, etc.) ou "" se não houver
   - bairro: Nome do bairro
   - cidade: Nome da cidade
   - estado: Sigla do estado em 2 letras maiúsculas (ex: "MG", "SP")
   - cep: CEP do endereço no formato "00000-000" ou "00000000" (com ou sem hífen)

LEIA TODOS OS TEXTOS E NÚMEROS VISÍVEIS NA IMAGEM. Não invente valores. Se não encontrar, use os valores padrão acima.
