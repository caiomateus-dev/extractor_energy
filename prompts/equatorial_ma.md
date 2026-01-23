Concessionária: EQUATORIAL

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA VERMELHA DESTACADA no canto SUPERIOR DIREITO da fatura, rotulada como "Unidade Consumidora".
   - Formato: números simples sem máscara
   - Aparece sempre em uma caixa vermelha destacada no topo direito
   - NUNCA use código de barras do rodapé

2. cod_cliente: Procure em uma CAIXA LARANJA/AMARELA DESTACADA logo abaixo do "Unidade Consumidora", rotulada como "Parceiro de Negócio".
   - Formato: números simples sem máscara
   - Aparece sempre em uma caixa laranja/amarela destacada no topo direito
   - Se não encontrar explicitamente, use null

3. classificacao: Procure próximo a "Classificacao:" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer formato composto, extraia apenas a classificação principal
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Grupo e Subgrupo de Tensao:" na seção de dados do cliente.
   - Valores comuns: "B1 / MONO", "B1 / BIF", "B1 / TRI"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - Mapeamento: "MONO" → "MONOFASICO", "BIF" → "BIFASICO", "TRI" → "TRIFASICO"
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure em uma CAIXA AMARELA no lado esquerdo, próximo a "Conta mês".
   - Formato: "MM/AAAA" (sempre numérico, com zero à esquerda se necessário)
   - Exemplo: "7/2025" → "07/2025"
   - NUNCA use formato abreviado de mês

6. valor_fatura: Procure em uma CAIXA VERMELHA GRANDE no centro da fatura, próximo a "Total a pagar".
   - Remova "R$" e separadores de milhar
   - Formato: número float
   - Use ponto como separador decimal no JSON

7. vencimento: Procure em uma CAIXA AMARELA no lado direito, próximo a "Vencimento".
   - Formato: "DD/MM/AAAA"

8. proximo_leitura: Procure na seção "Datas das Leituras", na linha "Próxima Leitura".
   - Formato: "DD/MM/AAAA"
   - Se não encontrar explicitamente, use null

9. aliquota_icms: Procure na tabela "Datas das Leituras", na coluna "Aliquota ICMS(%)".
   - Converta porcentagem para número float
   - Se não encontrar, use null

10. tensao_nominal: Procure próximo a "Tensão Nom.:" na seção de dados do cliente.
    - Formato: número seguido de "V" (ex: "220 V", "127 V")
    - Se não encontrar, use ""

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer "BAIXA RENDA" ou "TARIFA SOCIAL" na classificação
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA" ou "Tipo de Tarita: BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ONDE PROCURAR:
- Procure APENAS na seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" ou "DÉBITOS ANTERIORES"
- Na seção "REAVISO DE VENCIMENTO", procure por linhas como:
  - "NOTIFICAÇÃO: X FATURA(S)" ou "NOTIFICACAO: X FATURA(S)"
  - "UNIDADE VENCIDA: MES X/AAAA VALOR TOTAL: R$ XXX,XX"
  - "MES X/AAAA VALOR TOTAL: R$ XXX,XX"
  - "FATURA VENCIDA: MES X/AAAA VALOR TOTAL: R$ XXX,XX"
- Esta seção geralmente aparece no meio ou rodapé da fatura, muitas vezes destacada em vermelho ou com fundo colorido
- ATENÇÃO: A seção pode aparecer escrita como "REAVISO DE VENCIMENTO", "REAVISO", "NOTIFICAÇÃO", "NOTIFICACAO" (sem acento)
- NUNCA use valores de outras seções da fatura (como aliquota_icms, valores faturados, tabelas de consumo, etc.)
- NUNCA invente valores se a seção não existir ou estiver vazia

VALIDAÇÃO OBRIGATÓRIA - SIGA ESTES PASSOS EM ORDEM:

PASSO 1: LOCALIZE a seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" ou "DÉBITOS ANTERIORES"
- Se NÃO encontrar essa seção → valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 2: VERIFIQUE se a seção está VAZIA:
- Se a seção existir mas não tiver NENHUMA informação de fatura vencida listada
- Se não houver nenhum mês/ano e valor listados na seção
→ valores_em_aberto = [], faturas_venc = false → PARE AQUI

PASSO 3: Se a seção tiver FATURAS VENCIDAS LISTADAS:
   → Para cada fatura vencida EXPLICITAMENTE listada na seção:
     - mes_ano: formato "MM/AAAA" (deve aparecer na linha, ex: "MES 5/2025" → "05/2025", "MES 05/2025" → "05/2025")
     - valor: número float do valor do débito em R$ (deve aparecer na mesma linha, ex: "VALOR TOTAL: R$ 506,94" → 506.94, "R$ 506,94" → 506.94)
   → VALIDAÇÃO CRÍTICA: O valor deve ser um valor de FATURA (geralmente dezenas ou centenas de reais)
   → Compare mes_ano com mes_referencia:
     - Se forem IGUAIS → IGNORE completamente (é a fatura atual)
     - Se for ANTERIOR → adicione em valores_em_aberto
     - Se for FUTURO → IGNORE
   → Se houver ao menos um débito anterior válido → faturas_venc = true
   → Se todos forem da fatura atual ou nenhum válido → valores_em_aberto = [], faturas_venc = false
   
EXEMPLO PRÁTICO:
- Se mes_referencia = "06/2025" e encontrar "MES 5/2025 VALOR TOTAL: R$ 506,94" na seção REAVISO DE VENCIMENTO:
  → valores_em_aberto = [{"mes_ano": "05/2025", "valor": 506.94}]
  → faturas_venc = true

VALIDAÇÃO FINAL OBRIGATÓRIA - ANTES DE RETORNAR O JSON, VERIFIQUE:

1. Se você não encontrou uma seção "REAVISO DE VENCIMENTO" ou "NOTIFICAÇÃO" com débitos listados → valores_em_aberto = [] e faturas_venc = false

2. Se a seção existir mas estiver VAZIA → valores_em_aberto = [] e faturas_venc = false

3. Se valores_em_aberto contiver o mes_referencia atual → valores_em_aberto = [] e faturas_venc = false (isso está ERRADO)

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false
- É melhor retornar vazio do que retornar valores errados
- NUNCA invente valores

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na seção de histórico de consumo (geralmente não aparece em todas as faturas).
- Se não encontrar tabela de histórico com múltiplos meses → consumo_lista = []
- Se encontrar, extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- consumo: número inteiro em kWh

==========================
ENDEREÇO - REGRAS ESPECÍFICAS EQUATORIAL
==========================

REGRA CRÍTICA PARA ENDEREÇOS EQUATORIAL:

- rua: Nome completo da rua/avenida. Se aparecer "RUA" ou "AVENIDA" seguido de números, esses números fazem parte do nome da rua. NÃO extraia esses números como campo `numero`.
- numero: Se aparecer "S/N" ou "Sem Número" no endereço, coloque "S/N" no campo `numero` (NUNCA em `complemento`). Se houver um número de endereço explícito, extraia-o.
- complemento: Use para informações como Quadra (Q.), Lote (L.), Bloco, Apto, etc. Se aparecer "S/N" junto com complemento, extraia apenas o complemento (sem o S/N).
- bairro: Nome completo do bairro incluindo prefixos como "VILA", "JARDIM", "CONJUNTO", etc.
- cep: Procure por "CEP:" seguido de números. Extraia apenas os números (sem formatação). NÃO use valores de outras partes da fatura.
- cidade: Nome da cidade que aparece ANTES da sigla do estado. NÃO confunda com outras cidades que possam aparecer na fatura.
- estado: Sigla de 2 letras que aparece após o nome da cidade.
==========================
CONTA CONTRATO
==========================

conta_contrato: Procure por "Conta Contrato" ou similar na fatura.
- Se encontrar explicitamente, extraia o valor
- Se não encontrar, use null
- NÃO invente valores

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "EQUATORIAL"
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
