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

3. tipo_instalacao

- Normalmente aparece próximo a "Tipo de fornecimento".
- Exemplos possíveis: MONOFÁSICO, BIFÁSICO, TRIFÁSICO.

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
- grupo_tarifario: procurar por "Grupo Tarifário".
- tipo_instalacao, classificacao e grupo_tarifario normalmente aparecem próximos no mesmo bloco visual.
- NÃO invente valores.  
  Se não encontrar um campo, use string vazia ("") ou null conforme o tipo.
