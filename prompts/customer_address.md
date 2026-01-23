Analise esta imagem que contém APENAS o endereço do cliente de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "cep": "",
  "estado": "",
  "cidade": "",
  "bairro": "",
  "rua": "",
  "numero": "",
  "complemento": ""
}

==========================
REGRA ABSOLUTA - CAMPO RUA
==========================

O campo "rua" SEMPRE começa com uma destas palavras: "RUA", "AVENIDA", "ESTRADA", "RODOVIA".

SE O PRIMEIRO TEXTO DO ENDEREÇO NÃO COMEÇAR COM UMA DESSAS PALAVRAS, VOCÊ ESTÁ ERRADO.

PROCURE NO INÍCIO DO ENDEREÇO por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA".

NUNCA coloque no campo "rua":
- Nome de bairro
- Nome de cidade  
- Qualquer texto que NÃO começa com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA"

==========================
EXTRAÇÃO PASSO A PASSO
==========================

1. rua: 
   - Procure no INÍCIO do endereço por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA"
   - Extraia essa palavra e tudo até a primeira vírgula
   - Se não encontrar uma palavra começando com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA" no início, você está ERRADO
   - NÃO inclua Quadra (Q.), Lote (L.), número, apartamento, bairro, cidade no campo rua

2. numero: 
   - Se aparecer "S/N" ou "Sem Número" → use "S/N"
   - Se aparecer um número explícito de endereço → extraia esse número
   - "S/N" SEMPRE vai no campo numero, NUNCA em complemento

3. complemento: 
   - Tudo que vem após a rua e antes do bairro
   - "Q." (Quadra) e "L." (Lote) são complementos válidos e devem ser incluídos
   - Inclua Quadra (Q.), Lote (L.), Apartamento, Bloco, etc. se aparecerem
   - Inclua TODOS os elementos do complemento (Q., L., APART., RESIDENCIAL, etc.)
   - Se aparecer "S/N" junto com complemento, NÃO inclua o "S/N" no complemento
   - Se não houver complemento, use "" (string vazia)

4. bairro: 
   - Nome completo do bairro que aparece DEPOIS do complemento na linha do endereço
   - O bairro vem DEPOIS do complemento, NÃO antes
   - Extraia EXATAMENTE como aparece na fatura, incluindo prefixos (PARQUE, JARDIM, VILA, etc.) e sufixos (letras, números)
   - O bairro NÃO começa com "RUA" ou "AVENIDA"

5. cidade: 
   - Nome da cidade que aparece ANTES da sigla do estado na linha do endereço
   - Extraia APENAS da linha do endereço do cliente
   - NÃO use cidade da distribuidora ou outras seções

6. estado: 
   - Sigla de 2 letras maiúsculas após a cidade
   - Formato: "GO", "MG", "SP", etc.
   - Extraia APENAS da linha do endereço do cliente

7. cep: 
   - Números após "CEP:" na linha do endereço
   - Extraia apenas os 8 dígitos (sem formatação)
   - NÃO use CEPs de outras partes da fatura

==========================
VALIDAÇÃO OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE:

1. rua: DEVE começar com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA"
   -  "RUA SEM NOME" é valido
   - Se não começar com uma dessas palavras → ERRO GRAVE
   - NÃO deve conter bairro, cidade, Quadra, Lote, número, apartamento

2. numero: "S/N" ou número de endereço
   - "S/N" NUNCA vai em complemento

3. complemento: Elementos após rua e antes do bairro
   - "Q." (Quadra) e "L." (Lote) são complementos válidos e devem ser incluídos
   - Inclua todos os elementos (Q., L., APART., RESIDENCIAL, etc.)
   - NÃO inclua "S/N"

4. bairro: Nome completo como aparece na fatura
   - Vem DEPOIS do complemento
   - NÃO começa com "RUA" ou "AVENIDA"

5. cidade, estado, cep: APENAS da linha do endereço do cliente

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NÃO use valores de outras partes da fatura
- É MELHOR retornar campos vazios do que inventar valores incorretos

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente
- NÃO extraia o nome do cliente nesta análise - apenas o endereço
- Se não encontrar algum campo, use "" (string vazia)
