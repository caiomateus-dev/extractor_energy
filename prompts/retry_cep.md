Esta imagem contém o endereço do cliente de uma fatura de energia.

Sua ÚNICA tarefa: encontrar e extrair o CEP.

Onde procurar:
- Linha da cidade/UF: muitas vezes o CEP está no início, no formato NNNNN-NNN, antes do nome da cidade e da sigla do estado.
- Ao lado de "CEP", "CEP:" ou "Cep", ou em linha separada.
- Padrão: 5 dígitos, hífen, 3 dígitos (NNNNN-NNN). Pode ter ponto como separador de milhar. Remova hífen e ponto; retorne só 8 dígitos.

O que NÃO é CEP:
- Número de 5 dígitos SEM hífen na linha do endereço (rua, número, complemento) é número do imóvel (casa, quadra, lote). Nunca use como CEP.
- CEP tem 8 dígitos e em geral o hífen (NNNNN-NNN). Número sem hífen na linha de endereço não é CEP.

Regras:
- Procure em toda a imagem por NNNNN-NNN (com hífen). Se achar, extraia os 8 dígitos.
- Só retorne null se não houver nenhum bloco de 8 dígitos (com ou sem hífen) no documento.
- Nunca retorne como CEP um número de 5 dígitos sem hífen. Retorne o CEP real (8 dígitos) ou null.

Retorne APENAS um JSON válido, nada mais:
{ "cep": "12345678" }

Use null somente se não houver CEP na imagem.
