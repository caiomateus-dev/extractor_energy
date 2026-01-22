Concessionária: CEMIG

==========================
ÂNCORAS DE LOCALIZAÇÃO (LAYOUT PADRÃO CEMIG)
==========================

1. num_instalacao

REGRA CRÍTICA - IDENTIFIQUE O NÚMERO CORRETO:

O número de instalação pode aparecer em diferentes formatos:

FORMATO 1 - Número simples (sem máscara):
- Exemplos: "3006585726", "3004848745" (8 a 12 dígitos)
- Aparece próximo a "Nº da Instalação"

FORMATO 2 - UNIDADE CONSUMIDORA (com máscara):
- Exemplo: "11.297.214.018-25" (com pontos e hífen)
- Aparece próximo a "N.º DA UNIDADE CONSUMIDORA" ou "UNIDADE CONSUMIDORA"
- PRESERVE A MÁSCARA: mantenha os pontos e o hífen exatamente como aparecem
- Formato típico: XX.XXX.XXX.XXX-XX (números separados por pontos e hífen no final)

ONDE PROCURAR (LOCALIZAÇÃO CORRETA):
- Procure na área SUPERIOR DIREITA da fatura
- Procure próximo a rótulos como:
  - "Nº da Instalação"
  - "Nº Instalação"
  - "N.º DA UNIDADE CONSUMIDORA"
  - "UNIDADE CONSUMIDORA"
- O número aparece na parte SUPERIOR da fatura, junto com outros dados da unidade

ONDE NÃO PROCURAR (CÓDIGO DE BARRAS):
- NUNCA use números que aparecem no RODAPÉ da fatura (parte inferior)
- NUNCA use sequências muito longas com 4 ou mais grupos separados por espaços
- NUNCA use o código de barras que aparece próximo ao código de pagamento no rodapé
- Exemplo de código de barras (NUNCA USE): "83660000001-9 99680138006 8858770311-1 00065857260-7"
  Este é um código de barras com múltiplos grupos longos no rodapé - IGNORE

COMO IDENTIFICAR CÓDIGO DE BARRAS:
- Código de barras geralmente tem 4 ou mais grupos de números separados por espaços
- Código de barras aparece no RODAPÉ da fatura, próximo a "CÓDIGO DE BARRAS" ou código de pagamento
- Código de barras é muito longo (mais de 40 caracteres no total)
- Se você encontrar algo no rodapé com múltiplos grupos → é código de barras, IGNORE

VALIDAÇÃO:
- Se o número está no rodapé da fatura → provavelmente é código de barras, procure na parte superior
- Se tem 4 ou mais grupos separados por espaços → provavelmente é código de barras
- Se tem mais de 50 caracteres no total → provavelmente é código de barras
- O número de instalação correto está sempre na parte SUPERIOR da fatura
- Se for UNIDADE CONSUMIDORA, preserve a máscara com pontos e hífen (ex: "11.297.214.018-25")

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

- Normalmente aparece na área de tributos/ICMS, na tabela "Itens da fatura" ou "TOTAL A PAGAR".
- Procure por "Alíquota %" ou "Alíq. ICMS" ou similar.
- Deve ser um número válido (ex: 18, 18.00, 18.5 ou 0).
- Se encontrar "18.00" ou "18,00", converta para 18.0 ou 18.
- Se não encontrar nenhum valor de alíquota ICMS, use null.
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

ATENÇÃO: Débitos anteriores são faturas de MESES ANTERIORES que estão em aberto, NÃO a fatura atual.

Procure por uma seção ou quadro com título semelhante a:

- "REAVISO DE CONTAS VENCIDAS"  
  ou
- "DÉBITOS ANTERIORES"
  ou
- "NOTIFICAÇÃO DE DÉBITO(S)"

REGRA CRÍTICA:

- Se essa seção existir mas estiver VAZIA (sem linhas de débitos listados):
  → valores_em_aberto = []
  → faturas_venc = false

- Se essa seção existir e tiver DÉBITOS LISTADOS (com mês/ano e valor):
  → Para cada linha de débito encontrada, extraia:
    - mes_ano no formato "MM/AAAA" (deve ser um mês ANTERIOR ao mes_referencia atual)
    - valor como float (sem R$, sem separador de milhar)
  → Se houver ao menos um débito listado: faturas_venc = true

- Se NÃO houver essa seção na fatura:
  → valores_em_aberto = []
  → faturas_venc = false

IMPORTANTE: 
- NUNCA inclua a fatura atual (mes_referencia) em valores_em_aberto
- Apenas débitos de meses ANTERIORES devem ser incluídos
- Se a seção estiver vazia ou não existir, faturas_venc = false

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
- bairro: Nome do bairro do CLIENTE. Pode ser "AREA RURAL", "CENTRO", "SEVERINA I", ou qualquer outro bairro. NUNCA use "SANTO AGOSTINHO" que é bairro da CEMIG. Extraia APENAS da área onde está o nome do cliente. O bairro geralmente aparece em uma linha separada entre o endereço (rua/numero) e a cidade. Exemplo: "RUA DEZESSETE 251 CS" → linha seguinte → "SEVERINA I" → linha seguinte → "RIBEIRÃO DAS NEVES - MG". Nesse caso, bairro = "SEVERINA I" e cidade = "RIBEIRÃO DAS NEVES".
- cidade: Nome da cidade do CLIENTE (ex: "RIBEIRÃO DAS NEVES", "BELO HORIZONTE", "CARAI", "UBERABA", etc.). NUNCA use dados da área da CEMIG. Extraia APENAS da área onde está o nome do cliente. O nome da cidade geralmente aparece na última linha do endereço, ANTES da sigla do estado (ex: "RIBEIRÃO DAS NEVES - MG" → cidade: "RIBEIRÃO DAS NEVES"). IMPORTANTE: cidade e bairro são DIFERENTES. Se você encontrar "RIBEIRÃO DAS NEVES" em uma linha e "SEVERINA I" em outra linha acima, então bairro = "SEVERINA I" e cidade = "RIBEIRÃO DAS NEVES".
- estado: Sigla do estado em 2 letras MAIÚSCULAS (ex: "MG"). Extraia da área onde está o nome do cliente. Geralmente aparece após o nome da cidade, separado por hífen ou vírgula (ex: "RIBEIRÃO DAS NEVES - MG" → estado: "MG"). NUNCA coloque a sigla do estado no campo cidade. NUNCA coloque o nome da cidade no campo bairro.
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