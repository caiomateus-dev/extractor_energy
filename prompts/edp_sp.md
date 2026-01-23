Concessionária: EDP

==========================
LOCALIZAÇÃO DOS CAMPOS
==========================

1. num_instalacao: Procure em uma CAIXA AZUL DESTACADA no topo direito da fatura, próximo ao valor total.
   - Formato: números simples sem máscara (ex: "0150393906")
   - Aparece sempre em uma caixa azul destacada no topo direito
   - NUNCA use código de barras do rodapé

2. cod_cliente: Procure próximo a "CÓD. IDENT" na seção de dados do cliente.
   - Formato: números simples sem máscara (ex: "03520649")
   - Se não encontrar explicitamente, use null

3. classificacao: Procure próximo a "Classificação" na seção de dados do cliente.
   - Valores comuns: "RESIDENCIAL - BAIXA RENDA PRESTAÇÃO CONTINU", "RESIDENCIAL"
   - Saída OBRIGATÓRIA em MAIÚSCULAS: RESIDENCIAL, COMERCIAL, INDUSTRIAL, RURAL ou OUTROS
   - Se aparecer formato composto, extraia apenas "RESIDENCIAL"
   - NUNCA use "Residencial" ou "Comercial" (minúsculas). SEMPRE MAIÚSCULAS.

4. tipo_instalacao: Procure próximo a "Tipo de Instalação" na seção de dados do cliente.
   - Valores comuns: "MONOFASICO", "BIFASICO", "TRIFASICO"
   - Saída OBRIGATÓRIA em MAIÚSCULAS e SEM ACENTO: MONOFASICO, BIFASICO ou TRIFASICO
   - NUNCA use "Monofásico", "Bifásico" ou "Trifásico". SEMPRE MAIÚSCULAS e SEM ACENTO.

5. mes_referencia: Procure próximo a "Conta do Mês" no topo da fatura.
   - Valores comuns: "Junho/2025", "Julho/2025"
   - Formato: "MM/AAAA" (sempre numérico)
   - Converta nomes de meses para números:
     - Janeiro = 01, Fevereiro = 02, Março = 03, Abril = 04, Maio = 05, Junho = 06
     - Julho = 07, Agosto = 08, Setembro = 09, Outubro = 10, Novembro = 11, Dezembro = 12
   - Exemplo: "Junho/2025" → "06/2025"

6. valor_fatura: Procure em uma CAIXA AZUL GRANDE no topo da fatura, próximo a "TOTAL A PAGAR".
   - Remova "R$" e separadores de milhar
   - Formato: número float (ex: 197.76)
   - Use ponto como separador decimal no JSON
   - Converta vírgula para ponto (ex: "197,76" → 197.76)

7. vencimento: Procure em uma CAIXA AZUL no topo direito, próximo a "VENCIMENTO".
   - Formato: "DD/MM/AAAA"
   - Exemplos: "04/07/2025"

8. proximo_leitura: Procure na seção de leituras ou medições.
   - Formato: "DD/MM/AAAA"
   - Se não encontrar explicitamente, use null

9. aliquota_icms: Procure na tabela "Detalhes do Faturamento", na coluna "ALIQ" ou "ALÍQUOTA".
   - Valores comuns: 12.00, 18.00, 25.00
   - Se houver múltiplos valores, use null
   - Se não encontrar, use null

10. tensao_nominal: Procure próximo a "TENSÃO NOMINA" na seção de dados do cliente.
    - Formato: "XXX-XXXV" ou "XXXV" (ex: "240-120V", "127V")
    - Se não encontrar, use ""

==========================
FLAGS BOOLEANAS
==========================

- baixa_renda: true se aparecer "BAIXA RENDA" na classificação ou "Tarifa Social" na fatura
- ths_verde: true apenas se aparecer explicitamente "THS VERDE" ou "Bandeira Tarifária Vigente: VERDE"
- tarifa_branca: true apenas se aparecer explicitamente "TARIFA BRANCA"
- Caso contrário: false

==========================
VALORES EM ABERTO
==========================

REGRA CRÍTICA: valores_em_aberto contém APENAS débitos de meses ANTERIORES ao mes_referencia.

ATENÇÃO: Na maioria das faturas, não há débitos anteriores. Se você não encontrar uma LISTA CLARA de débitos, então valores_em_aberto = [] e faturas_venc = false.

REGRA ABSOLUTA:
- Na dúvida, retorne valores_em_aberto = [] e faturas_venc = false

==========================
CONSUMO HISTÓRICO
==========================

consumo_lista: Procure na seção de histórico de consumo (geralmente não aparece em todas as faturas).
- Se não encontrar tabela de histórico → consumo_lista = []
- Se encontrar, extraia na ORDEM EXATA que aparece
- Formato mes_ano: "MM/AAAA"
- consumo: número inteiro em kWh

==========================
OBRIGATORIO
==========================

- distribuidora: sempre "EDP" ou "EDP SÃO PAULO"
- conta_contrato: sempre null
- complemento: sempre ""
- NÃO invente valores. Se não encontrar, use "" ou null conforme o tipo
