Concessionária: CEMIG

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Área superior direita, próximo a "Nº da Instalação" ou "N.º DA UNIDADE CONSUMIDORA". 
   - Formato simples: "3006585726" (8-12 dígitos)
   - Formato UNIDADE CONSUMIDORA: "11.297.214.018-25" (preserve máscara com pontos e hífen)
   - NUNCA use código de barras do rodapé (4+ grupos separados por espaços)

2. classificacao: Próximo a "Classificação" ou "Classe". Saída: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS

3. tipo_instalacao: Próximo a "Tipo de fornecimento". Saída: MONOFASICO, BIFASICO ou TRIFASICO

4. mes_referencia: Próximo a "Referência". Formato: "MM/AAAA"

5. vencimento: Próximo a "Vencimento". Formato: "DD/MM/AAAA"

6. proximo_leitura: Próximo a "Próxima Leitura". Se aparecer só "DD/MM", complete o ano baseado no mes_referencia

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

Procure seção "REAVISO DE CONTAS VENCIDAS" ou "DÉBITOS ANTERIORES":
- Se não existir ou estiver vazia → valores_em_aberto = [], faturas_venc = false
- Se tiver débitos listados:
  → Para cada débito, compare mes_ano com mes_referencia
  → Se forem IGUAIS → IGNORE (é a fatura atual)
  → Se for ANTERIOR → adicione em valores_em_aberto
  → Se houver ao menos um débito anterior válido → faturas_venc = true
  → Se todos forem da fatura atual → valores_em_aberto = [], faturas_venc = false

EXEMPLO: Se mes_referencia = "12/2025", então valores_em_aberto NUNCA pode conter "12/2025". Apenas "11/2025", "10/2025", etc.

==========================
ENDEREÇO DO CLIENTE
==========================

REGRA ABSOLUTA: Extraia APENAS o endereço que está na mesma área visual do nome do cliente. IGNORE endereço da CEMIG (aparece próximo ao logo/título no topo).

COMO IDENTIFICAR:
- Nome do cliente aparece no topo esquerdo
- Endereço do cliente está logo abaixo/ao lado do nome, formando bloco visual único
- Endereço da CEMIG aparece separado, próximo ao logo (ex: "BELO HORIZONTE", "SANTO AGOSTINHO", CEP "30190-131")

CAMPOS (extrair APENAS da área do nome do cliente):
- rua: Nome da rua (sem número). Exemplo: "RUA DEZESSETE" (não "RUA DEZESSETE 251")
- numero: Número do endereço. Exemplo: "251"
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
