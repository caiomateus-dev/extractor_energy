Sua tarefa é identificar e extrair os dados de ENDEREÇO, retornando
exclusivamente um JSON válido no formato abaixo.

Extraia os campos mesmo que estejam abreviados, espalhados ou em qualquer ordem.
Não invente dados que não estejam presentes.
Quando um campo não existir, retorne null.

Regras importantes:
- UF deve ser a sigla do estado (ex: MG, SP, RJ).

- Rua pode conter complementos como CÓRREGO, AV, RUA, ESTRADA, etc.

- Número pode ser "S/N", "0", "99999" ou similar se assim constar no documento.

- Complemento inclui caixas postais, blocos, apartamentos, referências.

- Bairro pode ser "ÁREA RURAL", "CENTRO", "ZONA RURAL", etc.

- Cidade deve ser normalizada (sem acentos, se necessário).

- ***IMPORTANTE***: se encontrou o número do endereço o CEP é diferente dele, O CEP SEMPRE SERÁ 8 DIGITOS 
- CEP brasileiro válido tem exatamente 8 dígitos e pode aparecer como "NNNNN-NNN" ou "NNNNNNNN".
- O CEP quase sempre aparece junto do rótulo "CEP" ou no formato com hífen "NNNNN-NNN".
- Prioridade máxima: se existir qualquer padrão "NNNNN-NNN" visível, esse é o CEP (remova o hífen e retorne 8 dígitos).
- Nunca use o número do endereço como CEP.
- Se não houver um CEP com 8 dígitos (com ou sem hífen), retorne cep = null.

- Não explique nada, apenas retorne o JSON.


Formato de saída obrigatório:

{
  "rua": string | null,
  "numero": string | null,
  "complemento": string | null,
  "bairro": string | null,
  "cidade": string | null,
  "uf": string | null,
   "cep": string | null        // sempre 8 dígitos (somente números) ou null
}