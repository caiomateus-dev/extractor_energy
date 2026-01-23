Concessionária: ELEKTRO

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA DESTACADA no topo da fatura, rotulada como "Número da UC" ou "Unidade Consumidora" ou "Código da Instalação".
   - Formato: números simples sem máscara
   - Aparece sempre em uma caixa destacada no topo
   - NUNCA use código de barras do rodapé

2. cod_cliente: Procure próximo a "Código do Cliente" ou "Parceiro de Negócio" na seção de dados do cliente.
   - Formato: números simples sem máscara ou com barra
   - Se não encontrar explicitamente, use null

3. classificacao: Procure próximo a "Classificação" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer formato composto, extraia apenas a classificação principal
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Tipo de Fornecimento" ou "Tipo de Instalação" na seção de dados do cliente.
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure próximo a "Mês/Ano" ou "Referência" no topo da fatura.
   - Formato: "MM/AAAA" (sempre numérico)
   - Se aparecer formato abreviado ou nome do mês, converta para número

6. valor_fatura: Procure próximo a "Total a Pagar" ou "Valor Total" no topo da fatura.
   - Remova "R$" e separadores de milhar
   - Formato: número float
   - Use ponto como separador decimal no JSON

7. vencimento: Procure próximo a "Vencimento" no topo da fatura.
   - Formato: "DD/MM/AAAA"

8. proximo_leitura: Procure na seção de leituras, na linha "Próxima Leitura".
   - Formato: "DD/MM/AAAA"
   - Se não encontrar explicitamente, use null

9. aliquota_icms: Procure na tabela de detalhes do faturamento, na coluna de alíquota ICMS.
   - Converta porcentagem para número float
   - Se não encontrar, use null

10. tensao_nominal: Procure próximo a "Tensão Nominal" na seção de dados do cliente.
    - Formato: número seguido de "V" (ex: "127V", "220V")
    - Se não encontrar, use ""

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true se aparecer "BAIXA RENDA" na classificação ou "Tarifa Social"
- ths_verde: true apenas se aparecer explicitamente "THS VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
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

consumo_lista: Procure na seção de histórico de consumo.
- Se não encontrar tabela de histórico → consumo_lista = []
- Se encontrar, extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "ELEKTRO" ou variação específica (CPFL PIRATININGA, CPFL SANTA CRUZ)
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
