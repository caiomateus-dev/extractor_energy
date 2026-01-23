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

1. rua: Primeira parte do endereço até a primeira vírgula (ou até encontrar "Q.", "L.", "S/N", etc.)
   - Se aparecer "RUA SEM NOME" → extraia "RUA SEM NOME" completo
   - Se aparecer "RUA 01" → extraia "RUA 01" completo (o número faz parte do nome)
   - Se aparecer "AVENIDA X" → extraia "AVENIDA X" completo
   - CRÍTICO: Pare na primeira vírgula. Tudo antes da primeira vírgula é a rua.
   - NÃO inclua Quadra (Q.), Lote (L.), número (S/N), apartamento, etc. no campo rua

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

4. bairro: Nome completo do bairro incluindo prefixos
   - Se aparecer "PARQUE NAPOLIS A" → extraia "PARQUE NAPOLIS A" completo (incluindo o "A")
   - Se aparecer "JARDIM PRIMAVERA" → extraia "JARDIM PRIMAVERA" completo
   - Se aparecer "VILA NOVA" → extraia "VILA NOVA" completo
   - CRÍTICO: Extraia EXATAMENTE como aparece na fatura, incluindo letras, números e prefixos

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

==========================
VALIDAÇÃO OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE:

1. rua: Deve conter apenas o nome da rua/avenida (até a primeira vírgula)
   - NÃO deve conter Quadra, Lote, número, apartamento, bairro
   - Se aparecer "RUA SEM NOME" → rua = "RUA SEM NOME" (NÃO "PARQUE NAPOLES")

2. numero: Deve ser "S/N" ou um número de endereço
   - "S/N" NUNCA vai em complemento

3. complemento: Deve conter TODOS os elementos após a rua e antes do bairro
   - Inclua Q., L., APART., RESIDENCIAL, etc. se aparecerem
   - NÃO inclua "S/N" no complemento

4. bairro: Deve ser o nome completo do bairro como aparece na fatura
   - Inclua prefixos (PARQUE, JARDIM, VILA, etc.) e sufixos (letras, números)
   - NÃO confunda bairro com rua

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
