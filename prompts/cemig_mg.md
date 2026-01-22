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

ONDE PROCURAR:
- Procure APENAS na seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" ou "NOTIFICAÇÃO DE DÉBITO(S)"
- Esta seção geralmente aparece no meio ou rodapé da fatura
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA:

1. LOCALIZE a seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES" na fatura

2. VERIFIQUE se a seção está VAZIA:
   - Se a seção existir mas não tiver NENHUMA linha de débito listada (apenas o título, sem valores)
   - Se a seção estiver em branco ou com padrão hachurado
   - Se não houver nenhum mês/ano e valor listados na seção
   - Se a seção mostrar apenas o título mas sem conteúdo abaixo
   - Se você não conseguir identificar claramente linhas de débitos com mês/ano e valor
   → valores_em_aberto = []
   → faturas_venc = false
   → PARE AQUI, não procure valores em outras partes da fatura
   → NUNCA invente ou copie valores de outras seções (aliquota_icms, valores faturados, etc.)
   → NUNCA use valores que não estejam EXPLICITAMENTE na seção de débitos anteriores

3. Se a seção tiver DÉBITOS LISTADOS (com linhas contendo mês/ano e valor):
   → Para cada linha de débito EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha do débito)
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha)
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
     - Se for FUTURO → IGNORE
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false

REGRA ABSOLUTA:
- Se a seção de débitos anteriores estiver VAZIA ou não existir → valores_em_aberto = [] e faturas_venc = false
- NUNCA invente valores se a seção estiver vazia
- NUNCA copie valores de outras seções da fatura (aliquota_icms, valores faturados, tabelas, etc.)
- NUNCA use valores que não estejam EXPLICITAMENTE listados na seção de débitos anteriores
- Os valores devem aparecer em LINHAS ESPECÍFICAS dentro da seção de débitos anteriores, com mês/ano e valor na mesma linha
- Se mes_referencia = "12/2025", então valores_em_aberto NUNCA pode conter "12/2025"
- Se você não encontrar uma seção clara com débitos listados, valores_em_aberto = [] e faturas_venc = false
- ATENÇÃO: Se você ver valores como 18.0 (igual à aliquota_icms) ou valores muito baixos (menores que 10 reais), provavelmente está pegando valores errados. Verifique novamente se está na seção correta de débitos anteriores.

==========================
ENDEREÇO DO CLIENTE
==========================

REGRA ABSOLUTA: Extraia APENAS o endereço que está na mesma área visual do nome do cliente. IGNORE endereço da CEMIG (aparece próximo ao logo/título no topo).

COMO IDENTIFICAR:
- Nome do cliente aparece no topo esquerdo
- Endereço do cliente está logo abaixo/ao lado do nome, formando bloco visual único
- Endereço da CEMIG aparece separado, próximo ao logo (ex: "BELO HORIZONTE", "SANTO AGOSTINHO", CEP "30190-131")

CAMPOS (extrair APENAS da área do nome do cliente):
- rua: Nome da rua SEM o número. Se encontrar "RUA EXEMPLO 140", extraia apenas "RUA EXEMPLO". 
  O número vai separado no campo "numero". NUNCA inclua o número no campo rua.
- numero: Número do endereço (apenas o número, sem a rua). Exemplo: se encontrar "RUA EXEMPLO 140", 
  então rua = "RUA EXEMPLO" e numero = "140"
- complemento: Apto, bloco, caixa postal, etc. Use "" se não houver
- bairro: Nome do bairro (linha separada entre rua e cidade). Exemplo: "SEVERINA I", "OLIVEIRAS", "AREA RURAL"
- cidade: Nome da cidade na última linha do endereço, antes do estado. Exemplo: "DIVINOPOLIS", "RIBEIRÃO DAS NEVES"
- estado: Sigla 2 letras após cidade. Exemplo: "MG"
- cep: Formato "00000-000" ou "00000000", geralmente na mesma linha da cidade/estado

VALIDAÇÃO: Antes de preencher qualquer campo, verifique se está na mesma área do nome do cliente. Se estiver em área separada (próximo ao logo CEMIG), é dado da distribuidora - NÃO USE.

==========================
OUTRAS REGRAS
==========================

- distribuidora: sempre "CEMIG"
- tensao_nominal: procurar por "Tensão Nominal" ou "Tensão"
- cod_cliente: sempre null
- conta_contrato: sempre null
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
