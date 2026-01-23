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

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na seção de histórico de consumo (geralmente não aparece em todas as faturas).
- Se não encontrar tabela de histórico com múltiplos meses → consumo_lista = []
- Se encontrar, extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "EQUATORIAL"
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
