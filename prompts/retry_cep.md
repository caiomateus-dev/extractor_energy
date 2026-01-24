Esta imagem contém o endereço do cliente de uma fatura de energia.

Sua ÚNICA tarefa: encontrar e extrair o CEP.

Onde procurar:
- Ao lado ou após a palavra "CEP", "CEP:" ou "Cep"
- Após bairro e cidade, antes ou depois da sigla do estado (MG, SP, etc.)
- Formato típico: 5 dígitos, hífen, 3 dígitos (ex.: 30123-456) ou XX.XXX-XXX (ex.: 30.123-456)

Regras:
- CEP válido = exatamente 8 dígitos. Remova hífen ou ponto; retorne só os 8 dígitos.
- Procure em TODA a imagem. Só retorne null se você realmente não vir nenhum CEP de 8 dígitos.
- NUNCA use "99999", "00000" ou número de endereço (casa, quadra, lote) como CEP. CEP é o código postal.
- Se enxergar um CEP no documento, extraia. Não desista com null à toa.

Retorne APENAS um JSON válido, nada mais:
{ "cep": "12345678" }

Use null só se não houver CEP na imagem.
