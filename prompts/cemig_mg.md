Concessionária: CEMIG

==========================
ÂNCORAS DE LOCALIZAÇÃO (LAYOUT PADRÃO CEMIG)
==========================

1. num_instalacao

- Geralmente aparece como "Instalação", "Nº Instalação" ou "Unidade Consumidora".
- Costuma estar na área superior direita do documento, junto aos dados da unidade.

2. classificacao

- Normalmente aparece próximo à palavra "Classificação" ou "Classe".
- Pode vir como: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL, PODER PÚBLICO etc.
- Saída OBRIGATORIA: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS

3. tipo_instalacao

- Normalmente aparece próximo a "Tipo de fornecimento".
- Exemplos possíveis: MONOFÁSICO, BIFÁSICO, TRIFÁSICO.
- Saída OBRIGATORIA: MONOFASICO, BIFASICO, TRIFASICO

4. mes_referencia

- Geralmente aparece próximo de "Referência" ou "Mês/Ano".
- SEMPRE retornar no formato: "MM/AAAA".

5. vencimento

- Geralmente aparece próximo de "Vencimento".
- Formato obrigatório: "DD/MM/AAAA".

6. proximo_leitura

- Geralmente aparece próximo de "Próxima Leitura" ou "Próx. Leitura".
- Muitas vezes aparece apenas como "DD/MM".
- Nesses casos, você DEVE completar o ano com base no contexto do documento:
  - Use o mesmo ano do campo mes_referencia se a data fizer sentido cronológico.
  - Caso contrário, use o ano seguinte.

7. valor_fatura

- Normalmente aparece em destaque no quadro principal como:
  - "Valor a Pagar", "Total a Pagar" ou equivalente.
- Remova "R$" e use ponto como separador decimal.

8. aliquota_icms

- Normalmente aparece na área de tributos/ICMS.
- Deve ser um número válido (ex: 18, 18.5 ou 0).
- Se encontrar algo que não seja número, isso está errado.

==========================
REGRAS DE FLAGS (BOOLEANS)
==========================

baixa_renda:

- Somente true se aparecer EXATAMENTE a expressão "BAIXA RENDA"  
  na classificação, subclasse ou modalidade tarifária.
- Caso contrário: false.

ths_verde:

- Somente true se aparecer explicitamente algo como "THS VERDE"  
  na classe, subclasse ou modalidade tarifária.
- Caso contrário: false.

tarifa_branca:

- Somente true se aparecer explicitamente "TARIFA BRANCA"  
  na classificação ou modalidade tarifária.
- Caso contrário: false.

==========================
VALORES EM ABERTO (DÉBITOS ANTERIORES)
==========================

Se houver uma seção ou quadro com título semelhante a:

- "REAVISO DE CONTAS VENCIDAS"  
  ou
- "DÉBITOS ANTERIORES"

Então:

- Para cada linha encontrada, extraia:
  - mes_ano no formato "MM/AAAA"
  - valor como float (sem R$, sem separador de milhar)

Se NÃO houver essa seção:

- valores_em_aberto = []
- faturas_venc = false

Se houver ao menos um débito listado:

- faturas_venc = true

==========================
OUTRAS REGRAS GERAIS (CEMIG)
==========================

- distribuidora: sempre "CEMIG".
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão".
- tipo_instalacao e classificacao normalmente aparecem próximos no mesmo bloco visual.
- NÃO invente valores.  
  Se não encontrar um campo, use string vazia ("") ou null conforme o tipo.

==========================
DADOS DO CLIENTE E ENDEREÇO
==========================

ATENÇÃO CRÍTICA - EXTRAIR APENAS DADOS DO CLIENTE:

Na fatura CEMIG, há DOIS endereços visíveis:
1. Endereço da CEMIG (empresa distribuidora) - aparece no topo da fatura, próximo ao logo/título, geralmente com texto como "CEMIG DISTRIBUIÇÃO S.A." ou "CNPJ" ou "AV. BARBACENA" ou "SANTO AGOSTINHO" ou "BELO HORIZONTE" ou CEP da empresa
2. Endereço do CLIENTE - aparece na área onde está o nome do cliente

REGRA ABSOLUTA: VOCÊ DEVE EXTRAIR APENAS O ENDEREÇO DO CLIENTE. NUNCA USE DADOS DA DISTRIBUIDORA (CEMIG).

COMO IDENTIFICAR O ENDEREÇO CORRETO DO CLIENTE:

- O endereço do CLIENTE está SEMPRE na mesma área/seção visual onde aparece o nome do cliente
- O endereço do CLIENTE aparece logo abaixo ou ao lado do nome do cliente, formando um bloco visual único
- O endereço do CLIENTE geralmente vem em múltiplas linhas consecutivas abaixo do nome
- O endereço da CEMIG aparece separado, em outra área da fatura, geralmente no topo próximo ao logo/título da empresa
- O endereço do CLIENTE geralmente aparece junto com informações como CPF, RG, ou número de instalação do cliente
- O endereço da CEMIG geralmente aparece junto com informações da empresa como CNPJ, inscrição estadual

REGRA DE OURO: 
Use APENAS o endereço que está visualmente agrupado com o nome do cliente. Se o endereço está na mesma área/seção onde aparece o nome do cliente (ex: "VALDELITA GOMES NEVES"), esse é o endereço correto. 

IGNORE COMPLETAMENTE qualquer endereço que apareça em outra área da fatura, especialmente próximo ao logo/título da CEMIG. Se você encontrar bairro "SANTO AGOSTINHO", cidade "BELO HORIZONTE", ou CEP "30190-131" em uma área separada do nome do cliente, esses são dados da CEMIG - NÃO USE.

1. nome_cliente

- Geralmente aparece no topo da fatura, na área superior esquerda.
- É o nome completo do titular da conta de energia.
- O endereço do CLIENTE aparece logo abaixo ou ao lado deste nome.

2. Endereço completo do CLIENTE

Os dados de endereço do CLIENTE aparecem na mesma área visual onde está o nome do cliente. TODOS os campos abaixo devem ser extraídos APENAS dessa área, nunca da área da CEMIG:

- rua: Nome da rua, avenida ou logradouro do CLIENTE (NUNCA colocar numero ou complemento nesse campo). Extraia da área onde está o nome do cliente.
- numero: Número do endereço do CLIENTE. Extraia da área onde está o nome do cliente.
- complemento: Complemento como apartamento, bloco, sala, caixa postal (ex: "CX ****"), etc. Use "" se não houver. Extraia da área onde está o nome do cliente.
- bairro: Nome do bairro do CLIENTE. Pode ser "AREA RURAL", "CENTRO", ou qualquer outro bairro. NUNCA use "SANTO AGOSTINHO" que é bairro da CEMIG. Extraia APENAS da área onde está o nome do cliente.
- cidade: Nome da cidade do CLIENTE (pode ser qualquer cidade, incluindo Belo Horizonte se o cliente realmente for de lá). NUNCA use dados da área da CEMIG. Extraia APENAS da área onde está o nome do cliente.
- estado: Sigla do estado em 2 letras MAIÚSCULAS (ex: "MG"). Extraia da área onde está o nome do cliente.
- cep: CEP do CLIENTE no formato "00000-000" ou "00000000". Geralmente aparece na mesma linha da cidade/estado do cliente. NUNCA use o CEP da CEMIG (ex: "30190-131"). Extraia APENAS da área onde está o nome do cliente.

VALIDAÇÃO CRÍTICA:
Antes de preencher qualquer campo de endereço, verifique: este dado está na mesma área visual onde aparece o nome do cliente? Se NÃO estiver, IGNORE. Se estiver em uma área separada (especialmente próximo ao logo/título da CEMIG), é dado da distribuidora - NÃO USE.

IMPORTANTE: 
- Separe corretamente rua e número. O número geralmente vem após o nome da rua.
- Use APENAS dados que estão visualmente agrupados com o nome do cliente.
- NUNCA use bairro "SANTO AGOSTINHO", cidade "BELO HORIZONTE" ou CEP "30190-131" se eles aparecerem em área separada do nome do cliente - esses são dados da CEMIG.
- Se o cliente realmente for de Belo Horizonte/Santo Agostinho, esses dados aparecerão na mesma área do nome do cliente.

=======================
OBRIGATORIO
=======================

- cod_cliente: sempre null
- conta_contrato: sempre null