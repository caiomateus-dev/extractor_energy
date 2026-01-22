Concessionária: CEMIG

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Área superior direita, próximo a "Nº da Instalação" ou "N.º DA UNIDADE CONSUMIDORA". 
   - Formato simples: "3006585726" (8-12 dígitos)
   - Formato UNIDADE CONSUMIDORA: "11.297.214.018-25" (preserve máscara com pontos e hífen)
   - NUNCA use código de barras do rodapé (4+ grupos separados por espaços)

2. classificacao: Próximo a "Classificação" ou "Classe". 
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

3. tipo_instalacao: Próximo a "Tipo de fornecimento". 
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

4. mes_referencia: Próximo a "Referência". Formato: "MM/AAAA"

5. vencimento: Próximo a "Vencimento". Formato: "DD/MM/AAAA"

6. proximo_leitura: Próximo a "Próxima Leitura". 
   - Se aparecer só "DD/MM", complete o ano baseado no mes_referencia
   - Formato: "DD/MM/AAAA". A data deve ser FUTURA em relação ao mes_referencia
   - Exemplo: se mes_referencia = "12/2025" e próxima leitura = "13/01", então proximo_leitura = "13/01/2026"

7. valor_fatura: "Valor a Pagar" ou "Total a Pagar". Remova "R$" e separadores de milhar

8. aliquota_icms: Procure em:
   - Tabela "Itens da fatura" / "Valores Faturados" → coluna "Aliquota ICMS" ou "Alíquota %"
   - Seção "Reservado ao Fisco" → tabela com coluna "Alíquota (%)" na linha ICMS
   - Converta "18,00" ou "18.00" para 18.0. Se não encontrar, use null

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer EXATAMENTE "BAIXA RENDA" na classificação/modalidade
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, a seção de débitos anteriores está VAZIA. Se você não encontrar uma LISTA CLARA de débitos com valores diferentes na seção "REAVISO DE CONTAS VENCIDAS", então valores_em_aberto = [] e faturas_venc = false.

EXEMPLO DE ERRO GRAVE (NUNCA FAÇA ISSO):
- Se você retornar valores_em_aberto com todos os valores iguais (ex: todos 18.0) → ERRADO
- Se você retornar valores_em_aberto com valores iguais à aliquota_icms → ERRADO  
- Se você retornar valores_em_aberto incluindo o mes_referencia atual → ERRADO
- Se você retornar valores_em_aberto sem encontrar uma lista clara na seção de débitos → ERRADO

Se você tiver qualquer dúvida, retorne valores_em_aberto = [] e faturas_venc = false.

ONDE PROCURAR:
- Procure APENAS na seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" ou "NOTIFICAÇÃO DE DÉBITO(S)"
- Esta seção geralmente aparece no meio ou rodapé da fatura
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" na fatura
- Se NÃO encontrar essa seção → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 2: VERIFIQUE se a seção está VAZIA:
- Se a seção existir mas não tiver NENHUMA linha de débito listada (apenas o título, sem valores abaixo)
- Se a seção estiver em branco ou com padrão hachurado
- Se não houver nenhum mês/ano e valor listados na seção
- Se a seção mostrar apenas o título mas sem conteúdo abaixo
- Se você não conseguir identificar claramente linhas de débitos com mês/ano e valor
- Se você ver apenas o título da seção mas sem uma TABELA ou LISTA de débitos abaixo
→ valores_em_aberto = []
→ faturas_venc = false
→ PARE AQUI, não procure valores em outras partes da fatura
→ NUNCA invente ou copie valores de outras seções (aliquota_icms, valores faturados, etc.)

PASSO 3: Se a seção tiver DÉBITOS LISTADOS (com linhas contendo mês/ano e valor):
   → Para cada linha de débito EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha do débito)
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha)
   → VALIDAÇÃO CRÍTICA: O valor deve ser um valor de FATURA (geralmente dezenas ou centenas de reais)
   → VALIDAÇÃO CRÍTICA: O valor NUNCA pode ser igual à aliquota_icms (ex: se aliquota_icms = 18.0, então NUNCA use 18.0)
   → VALIDAÇÃO CRÍTICA: O valor NUNCA pode ser o mesmo para todos os meses (isso indica que está copiando valor errado)
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
     - Se for FUTURO → IGNORE
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false

VALIDAÇÃO FINAL OBRIGATÓRIA - ANTES DE RETORNAR O JSON, VERIFIQUE:

1. Se você não encontrou uma seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" com uma LISTA CLARA de débitos → valores_em_aberto = [] e faturas_venc = false

2. Se a seção existir mas estiver VAZIA (sem linhas de débitos) → valores_em_aberto = [] e faturas_venc = false

3. Se TODOS os valores em valores_em_aberto forem iguais entre si (ex: todos 18.0, todos 10.0) → valores_em_aberto = [] e faturas_venc = false (isso indica erro)

4. Se algum valor em valores_em_aberto for igual à aliquota_icms → valores_em_aberto = [] e faturas_venc = false (isso indica que você copiou valor errado)

5. Se valores_em_aberto contiver o mes_referencia atual → valores_em_aberto = [] e faturas_venc = false (isso está ERRADO)

6. Se você não tiver CERTEZA ABSOLUTA de que encontrou débitos anteriores válidos na seção correta → valores_em_aberto = [] e faturas_venc = false

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false
- É melhor retornar vazio do que retornar valores errados
- NUNCA invente valores
- NUNCA copie valores de outras seções (aliquota_icms, valores faturados, tabelas, etc.)

==========================
ENDEREÇO DO CLIENTE
==========================

REGRA ABSOLUTA CRÍTICA: Extraia APENAS o endereço que está na mesma área visual do nome do cliente. IGNORE COMPLETAMENTE o endereço da CEMIG.

ONDE ESTÁ O ENDEREÇO DO CLIENTE:
- Nome do cliente aparece no TOPO ESQUERDO da fatura, logo abaixo do logo grande "CEMIG"
- Endereço do cliente está LOGO ABAIXO do nome do cliente, formando um BLOCO VISUAL ÚNICO
- Este endereço do cliente está na ÁREA ESQUERDA da fatura

ONDE ESTÁ O ENDEREÇO DA CEMIG (IGNORE COMPLETAMENTE):
- Endereço da CEMIG aparece no TOPO DIREITO da fatura
- Está próximo ao texto "DOCUMENTO AUXILIAR DA NOTA FISCAL DE ENERGIA ELÉTRICA ELETRONICA"
- Contém informações como "CEMIG DISTRIBUIÇÃO S.A."
- Contém endereço como "AV. BARBACENA", "SANTO AGOSTINHO", "BELO HORIZONTE", CEP "30190-131"
- Este endereço da CEMIG está na ÁREA DIREITA da fatura, SEPARADO do nome do cliente

VALIDAÇÃO OBRIGATÓRIA ANTES DE EXTRAIR:
1. LOCALIZE o nome do cliente no TOPO ESQUERDO da fatura
2. VERIFIQUE se o endereço que você vai extrair está LOGO ABAIXO ou AO LADO do nome do cliente (mesma área visual)
3. Se o endereço estiver no TOPO DIREITO, próximo a "CEMIG DISTRIBUIÇÃO" ou "DOCUMENTO AUXILIAR" → É DA CEMIG, NÃO USE
4. Se o endereço contiver "AV. BARBACENA", "SANTO AGOSTINHO", "BELO HORIZONTE", CEP "30190-131" → É DA CEMIG, NÃO USE

CAMPOS (extrair APENAS da área ESQUERDA, abaixo do nome do cliente):
- rua: Nome da rua SEM o número. Se encontrar "CORREGO AREAO 99999", extraia apenas "CORREGO AREAO". 
  O número vai separado no campo "numero". NUNCA inclua o número no campo rua.
- numero: Número do endereço (apenas o número, sem a rua). Exemplo: se encontrar "CORREGO AREAO 99999", 
  então rua = "CORREGO AREAO" e numero = "99999"
- complemento: Apto, bloco, caixa postal, etc. Use "" se não houver
- bairro: Nome do bairro (linha separada entre rua e cidade). Exemplo: "AREA RURAL", "OLIVEIRAS"
- cidade: Nome da cidade na última linha do endereço, antes do estado. Exemplo: "MONTEZUMA", "DIVINOPOLIS"
- estado: Sigla 2 letras após cidade. Exemplo: "MG"
- cep: Formato "00000-000" ou "00000000", geralmente na mesma linha da cidade/estado

REGRA FINAL - LEIA COM MUITA ATENÇÃO:
- Se você tiver DÚVIDA sobre qual endereço usar → Use APENAS o endereço que está na ÁREA ESQUERDA, abaixo do nome do cliente
- NUNCA use endereço que esteja na ÁREA DIREITA da fatura
- NUNCA use endereço que contenha "CEMIG DISTRIBUIÇÃO" ou "DOCUMENTO AUXILIAR"
- NUNCA use endereço que contenha "AV. BARBACENA", "SANTO AGOSTINHO", "BELO HORIZONTE", CEP "30190-131"
- Se você encontrar "CEMIG DISTRIBUIÇÃO S.A." próximo ao endereço → É DA CEMIG, NÃO USE
- Se você encontrar "17º ANDAR" ou "ALA 1" no endereço → É DA CEMIG, NÃO USE
- O endereço do cliente está SEMPRE na mesma área visual do nome do cliente (topo esquerdo)
- O endereço da CEMIG está SEMPRE separado, no topo direito, próximo a textos administrativos

VALIDAÇÃO FINAL ANTES DE RETORNAR:
Antes de preencher rua, numero, bairro, cidade, estado, cep:
1. Verifique se o endereço está na ÁREA ESQUERDA da fatura, abaixo do nome do cliente
2. Se o endereço estiver na ÁREA DIREITA → NÃO USE, é da CEMIG
3. Se o endereço contiver qualquer referência a "CEMIG DISTRIBUIÇÃO", "DOCUMENTO AUXILIAR", "AV. BARBACENA", "SANTO AGOSTINHO", "BELO HORIZONTE", CEP "30190-131" → NÃO USE, é da CEMIG
4. Se o endereço contiver "17º ANDAR", "ALA 1", "1200" (número do prédio da CEMIG) → NÃO USE, é da CEMIG
5. Se você não tiver CERTEZA → Use apenas o endereço que está na área esquerda, abaixo do nome do cliente

EXEMPLO DE ERRO GRAVE (NUNCA FAÇA ISSO):
- Se você extrair cidade = "BELO HORIZONTE" e bairro = "SANTO AGOSTINHO" → ERRADO, isso é da CEMIG
- Se você extrair rua = "AV. BARBACENA" → ERRADO, isso é da CEMIG
- Se você extrair cep = "30190-131" → ERRADO, isso é da CEMIG
- O endereço correto do cliente está SEMPRE na área esquerda, abaixo do nome do cliente

==========================
OUTRAS REGRAS
==========================

- distribuidora: sempre "CEMIG"
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão"
- cod_cliente: sempre null
- conta_contrato: sempre null
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
