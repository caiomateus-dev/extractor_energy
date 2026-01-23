Concessionária: ENERGISA

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA AZUL DESTACADA no canto SUPERIOR DIREITO da fatura, rotulada como "CÓDIGO DA INSTALAÇÃO".
   - Formato: números simples sem máscara
   - Aparece sempre em uma caixa azul destacada no topo direito
   - NUNCA use código de barras do rodapé

2. cod_cliente: Procure em uma CAIXA AZUL DESTACADA no canto SUPERIOR DIREITO, rotulada como "CÓDIGO DO CLIENTE".
   - Formato: pode conter barra
   - Aparece sempre em uma caixa azul destacada no topo direito
   - Se não encontrar explicitamente, use null

3. classificacao: Procure próximo a "Classificação" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer formato composto, extraia apenas a classificação principal
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Tipo de Fornecimento" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure na BANDA AZUL HORIZONTAL destacada, próximo a "REF: MÊS / ANO".
   - Formato: "MM/AAAA" (sempre numérico)
   - Converta meses abreviados para números:
     - JAN = 01, FEV = 02, MAR = 03, ABR = 04, MAI = 05, JUN = 06
     - JUL = 07, AGO = 08, SET = 09, OUT = 10, NOV = 11, DEZ = 12

6. valor_fatura: Procure na BANDA AZUL HORIZONTAL destacada, próximo a "TOTAL A PAGAR".
   - Remova "R$" e separadores de milhar
   - Formato: número float
   - Use ponto como separador decimal no JSON

7. vencimento: Procure na BANDA AZUL HORIZONTAL destacada, próximo a "VENCIMENTO".
   - Formato: "DD/MM/AAAA"

8. proximo_leitura: Procure na tabela "Datas de Leituras", na linha "Próxima Leitura".
   - Formato: "DD/MM/AAAA"
   - Se não encontrar explicitamente, use null

9. aliquota_icms: Procure na tabela "ITENS DA FATURA" ou "Tributo", na coluna de alíquota ICMS.
   - Converta porcentagem para número float
   - Se não encontrar, use null

10. tensao_nominal: Procure próximo a "TENSÃO NOMINAL" na seção de dados do cliente.
    - Formato: número seguido de "V" (ex: "127V", "220V")
    - Se não encontrar, use ""

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true apenas se aparecer EXATAMENTE "BAIXA RENDA" na classificação (não confundir com "BAIXA TENSÃO")
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- faturas_venc: true se aparecer "DÉBITOS ANTERIORES" ou "FATURAS EM ATRASO"
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

consumo_lista: Procure na seção "CONSUMO FATURADO" (tabela ou gráfico).
- Extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- Se aparecer formato abreviado, converta meses para números
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "ENERGISA"
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
