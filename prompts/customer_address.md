Analise esta imagem que contém APENAS o endereço do cliente de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "rua": "",
  "numero": "",
  "complemento": "",
  "bairro": "",
  "cidade": "",
  "estado": "",
  "cep": ""
}

==========================
EXTRAÇÃO PASSO A PASSO
==========================

SIGA ESTA ORDEM EXATA para extrair os campos do endereço:

1. rua: Primeira parte do endereço que SEMPRE começa com "RUA", "AVENIDA", "ESTRADA", "RODOVIA", etc.
   - CRÍTICO: O campo rua SEMPRE começa com uma dessas palavras: "RUA", "AVENIDA", "ESTRADA", "RODOVIA"
   - Se aparecer "RUA SEM NOME" → extraia "RUA SEM NOME" completo (NÃO "PARQUE NAPOLIS")
   - Se aparecer "RUA 01" → extraia "RUA 01" completo (o número faz parte do nome)
   - Se aparecer "AVENIDA X" → extraia "AVENIDA X" completo
   - CRÍTICO: Pare na primeira vírgula. Tudo antes da primeira vírgula é a rua.
   - CRÍTICO: Se a primeira palavra NÃO for "RUA", "AVENIDA", "ESTRADA", "RODOVIA", você está ERRADO. Procure novamente.
   - NÃO inclua Quadra (Q.), Lote (L.), número (S/N), apartamento, bairro, etc. no campo rua
   - NÃO confunda bairro com rua. Bairro vem DEPOIS do complemento na linha do endereço

2. numero: Número do endereço ou "S/N"
   - Se aparecer "S/N" ou "Sem Número" → use "S/N"
   - Se aparecer um número explícito de endereço (ex: "123", "505") → extraia esse número
   - CRÍTICO: "S/N" SEMPRE vai no campo numero, NUNCA em complemento

3. complemento: Tudo que vem após a rua e antes do bairro (Quadra, Lote, Apartamento, etc.)
   - Se aparecer "Q. 4, L. 11, APART-106, RESIDENCIAL OURENSE" → extraia TUDO: "Q. 4, L. 11, APART-106, RESIDENCIAL OURENSE"
   - Se aparecer "Q. 11, L. 22" → extraia "Q. 11, L. 22" completo
   - CRÍTICO: Inclua TODOS os elementos do complemento (Q., L., APART., RESIDENCIAL, etc.)
   - Se aparecer "S/N" junto com complemento, NÃO inclua o "S/N" no complemento (ele vai em numero)
   - Se não houver complemento, use "" (string vazia)

4. bairro: Nome completo do bairro que aparece DEPOIS do complemento na linha do endereço
   - CRÍTICO: O bairro vem DEPOIS do complemento, NÃO antes. Se você colocou bairro em rua, está ERRADO.
   - Se aparecer "PARQUE NAPOLIS A" → extraia "PARQUE NAPOLIS A" completo (incluindo o "A")
   - Se aparecer "JARDIM PRIMAVERA" → extraia "JARDIM PRIMAVERA" completo
   - Se aparecer "VILA NOVA" → extraia "VILA NOVA" completo
   - CRÍTICO: Extraia EXATAMENTE como aparece na fatura, incluindo letras, números e prefixos
   - CRÍTICO: O bairro NÃO começa com "RUA" ou "AVENIDA". Se você colocou algo que começa com "RUA" em bairro, está ERRADO.

5. cidade: Nome da cidade que aparece ANTES da sigla do estado
   - Extraia APENAS da linha do endereço do cliente
   - NÃO use cidade da distribuidora ou outras seções

6. estado: Sigla de 2 letras após a cidade
   - Formato: "GO", "MG", "SP", etc.
   - Extraia APENAS da linha do endereço do cliente

7. cep: Números após "CEP:" na linha do endereço
   - Extraia apenas os 8 dígitos (sem formatação)
   - Se aparecer "CEP: 72885173" → extraia "72885173"
   - NÃO use CEPs de outras partes da fatura

==========================
EXEMPLO PRÁTICO
==========================

Se o endereço for: "RUA SEM NOME, Q. 4, L. 11, S/N, APART-106, RESIDENCIAL OURENSE PARQUE NAPOLIS A CEP: 72885173 CIDADE OCIDENTAL GO"

EXTRAÇÃO CORRETA:
- rua: "RUA SEM NOME"
- numero: "S/N"
- complemento: "Q. 4, L. 11, APART-106, RESIDENCIAL OURENSE"
- bairro: "PARQUE NAPOLIS A"
- cidade: "CIDADE OCIDENTAL"
- estado: "GO"
- cep: "72885173"

EXEMPLO DE ERRO GRAVE (NUNCA FAÇA ISSO):
- rua: "PARQUE NAPOLIS" → ERRADO! Rua deve começar com "RUA", "AVENIDA", etc.
- bairro: "RUA SEM NOME" → ERRADO! Bairro não começa com "RUA"
- Se você extraiu "PARQUE NAPOLIS" como rua, você está ERRADO. Procure por "RUA SEM NOME" no início do endereço.

==========================
VALIDAÇÃO OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE:

1. rua: Deve conter apenas o nome da rua/avenida (até a primeira vírgula)
   - CRÍTICO: Deve SEMPRE começar com "RUA", "AVENIDA", "ESTRADA", "RODOVIA"
   - NÃO deve conter Quadra, Lote, número, apartamento, bairro
   - Se aparecer "RUA SEM NOME" → rua = "RUA SEM NOME" (NÃO "PARQUE NAPOLES", NÃO "PARQUE NAPOLIS")
   - Se você colocou algo que NÃO começa com "RUA"/"AVENIDA" em rua → ERRO GRAVE. Procure novamente.

2. numero: Deve ser "S/N" ou um número de endereço
   - "S/N" NUNCA vai em complemento

3. complemento: Deve conter TODOS os elementos após a rua e antes do bairro
   - Inclua Q., L., APART., RESIDENCIAL, etc. se aparecerem
   - NÃO inclua "S/N" no complemento

4. bairro: Deve ser o nome completo do bairro como aparece na fatura
   - CRÍTICO: O bairro vem DEPOIS do complemento na linha do endereço
   - CRÍTICO: O bairro NÃO começa com "RUA" ou "AVENIDA"
   - Inclua prefixos (PARQUE, JARDIM, VILA, etc.) e sufixos (letras, números)
   - NÃO confunda bairro com rua. Se você colocou bairro em rua, está ERRADO.

5. cidade, estado, cep: Devem vir APENAS da linha do endereço do cliente

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NÃO use valores de outras partes da fatura (como cidade da distribuidora, CEPs de outras seções, etc.)
- Se a imagem estiver ilegível ou um campo não estiver visível, use "" (string vazia)
- É MELHOR retornar campos vazios do que inventar valores incorretos
- NUNCA invente ou adivinhe valores baseado em contexto ou outras informações

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente. NÃO inclua dados da distribuidora.
- NÃO extraia o nome do cliente nesta análise - apenas o endereço.
- Se não encontrar algum campo, use "" (string vazia).
