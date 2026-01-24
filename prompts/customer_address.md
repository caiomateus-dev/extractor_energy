Sua tarefa é identificar e extrair os dados de ENDEREÇO, retornando
exclusivamente um JSON válido no formato abaixo.

Extraia os campos mesmo que estejam abreviados, espalhados ou em qualquer ordem.
Não invente dados que não estejam presentes.
Quando um campo não existir, retorne null.

Regras importantes:
- CEP deve conter apenas números (8 dígitos).
- UF deve ser a sigla do estado (ex: MG, SP, RJ).
- Rua pode conter complementos como CÓRREGO, AV, RUA, ESTRADA, etc.
- Número pode ser "S/N", "0", "99999" ou similar se assim constar no documento.
- Complemento inclui caixas postais, blocos, apartamentos, referências.
- Bairro pode ser "ÁREA RURAL", "CENTRO", "ZONA RURAL", etc.
- Cidade deve ser normalizada (sem acentos, se necessário).
- Não explique nada, apenas retorne o JSON.

Formato de saída obrigatório:

{
  "cep": string | null,
  "rua": string | null,
  "numero": string | null,
  "complemento": string | null,
  "bairro": string | null,
  "cidade": string | null,
  "uf": string | null
}