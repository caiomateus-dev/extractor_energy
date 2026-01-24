Analise esta imagem que contém APENAS o endereço do cliente de uma fatura de energia.

RETORNE APENAS UM JSON VÁLIDO, sem markdown, sem texto antes ou depois do JSON.

Formato do JSON esperado:
{
  "cep": "",
  "bairro": "",
  "estado": "",
  "cidade": "",
  "rua": "",
  "numero": "",
  "complemento": ""
}

==========================
REGRA ABSOLUTA - CAMPO RUA
==========================

O nome do bairro não é o mesmo que o nome da cidade.
Não repita campos

O campo "rua" SEMPRE começa com uma destas palavras: "RUA", "AVENIDA", "ESTRADA", "RODOVIA".

SE O PRIMEIRO TEXTO DO ENDEREÇO NÃO COMEÇAR COM UMA DESSAS PALAVRAS, VOCÊ ESTÁ ERRADO.

PROCURE NO INÍCIO DO ENDEREÇO por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA".

NUNCA coloque no campo "rua":
- Nome de bairro
- Nome de cidade  
- Qualquer texto que NÃO começa com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA"

==========================
ORDEM DOS CAMPOS NO ENDEREÇO
==========================

A linha do endereço segue esta ordem EXATA:
1. RUA (começa com "RUA", "AVENIDA", etc.)
2. COMPLEMENTO (Q., L., APART., etc.)
3. BAIRRO
4. CEP (se houver)
5. CIDADE
6. ESTADO

CRÍTICO: Bairro vem ANTES da cidade. Cidade vem ANTES do estado.
Se você colocou o mesmo valor em bairro e cidade, você está ERRADO.

==========================
EXTRAÇÃO PASSO A PASSO
==========================

1. rua: 
   - Procure no INÍCIO do endereço por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA"
   - "RUA SEM NOME" é valido
   - Extraia essa palavra e tudo até a primeira vírgula
   - Se não encontrar uma palavra começando com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA" no início, você está ERRADO
   - NÃO inclua Quadra (Q.), Lote (L.), número, apartamento, bairro, cidade no campo rua

2. numero: 
   - Se aparecer "S/N" ou "Sem Número" → use "S/N"
   - Se aparecer um número explícito de endereço → extraia esse número
   - "S/N" SEMPRE vai no campo numero, NUNCA em complemento

3. complemento: 
   - Tudo que vem após a rua e antes do bairro
   - CRÍTICO: Se aparecer "Q." (Quadra) no endereço, ela DEVE ser incluída no complemento
   - CRÍTICO: Se aparecer "L." (Lote) no endereço, ele DEVE ser incluído no complemento
   - CRÍTICO: Se aparecerem ambos "Q." e "L." no endereço, AMBOS devem estar no complemento
   - CRÍTICO: Leia CADA NÚMERO com MUITA ATENÇÃO. Leia caractere por caractere
   - CRÍTICO: NÃO confunda números com "S/N" ou outros textos. Números são apenas dígitos
   - CRÍTICO: "S/N" é texto que aparece separado e vai no campo numero. NÃO confunda números com "S/N"
   - CRÍTICO: Inclua TODOS os elementos que aparecem entre a rua e o bairro (Q., L., APART., RESIDENCIAL, etc.)
   - Se aparecer "S/N" junto com complemento, NÃO inclua o "S/N" no complemento
   - Se não houver complemento, use "" (string vazia)

4. bairro: 
   - Nome completo do bairro que aparece DEPOIS do complemento na linha do endereço
   - O bairro vem DEPOIS do complemento e ANTES da cidade
   - CRÍTICO: Leia CADA LETRA e CARACTERE com atenção. Extraia EXATAMENTE como aparece
   - CRÍTICO: Inclua TODOS os caracteres: letras, números, espaços, sufixos (incluindo letras soltas no final)
   - CRÍTICO: NÃO confunda bairro com cidade. Bairro vem ANTES da cidade na linha do endereço
   - CRÍTICO: Se você colocou o mesmo valor em bairro e cidade, está ERRADO. Procure novamente
   - Inclua prefixos (PARQUE, JARDIM, VILA, etc.) e sufixos (letras, números, etc.) se aparecerem
   - O bairro NÃO começa com "RUA" ou "AVENIDA"

5. cidade: 
   - Nome da cidade que aparece ANTES da sigla do estado na linha do endereço
   - CRÍTICO: A cidade vem DEPOIS do bairro e ANTES do estado na linha do endereço
   - CRÍTICO: Bairro e cidade são CAMPOS DIFERENTES. Se você colocou o mesmo valor em ambos, está ERRADO
   - CRÍTICO: O valor de cidade DEVE ser diferente do valor de bairro. Se forem iguais, você está ERRADO
   - CRÍTICO: Procure na linha do endereço pelo nome que aparece ANTES da sigla do estado (GO, MG, SP, etc.)
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
   - Se não começar com uma dessas palavras → ERRO GRAVE
   - NÃO deve conter bairro, cidade, Quadra, Lote, número, apartamento

2. numero: "S/N" ou número de endereço
   - "S/N" NUNCA vai em complemento

3. complemento: Elementos após rua e antes do bairro
   - CRÍTICO: Se aparecer "Q." (Quadra) no endereço, ela DEVE ser incluída no complemento
   - CRÍTICO: Se aparecer "L." (Lote) no endereço, ele DEVE ser incluído no complemento
   - CRÍTICO: Se aparecerem ambos "Q." e "L." no endereço, AMBOS devem estar no complemento
   - CRÍTICO: Leia os números com MUITA ATENÇÃO. NÃO confunda números com "S/N" ou outros textos
   - CRÍTICO: "S/N" é texto separado que vai no campo numero. NÃO confunda números com "S/N"
   - CRÍTICO: Inclua TODOS os elementos que aparecem entre a rua e o bairro (Q., L., APART., RESIDENCIAL, etc.)
   - NÃO inclua "S/N"

4. bairro: Nome completo como aparece na fatura
   - CRÍTICO: Vem DEPOIS do complemento na linha do endereço
   - CRÍTICO: Extraia EXATAMENTE como aparece, incluindo TODOS os caracteres (letras, números, espaços, sufixos)
   - CRÍTICO: NÃO confunda bairro com cidade. Se você colocou o mesmo valor em ambos, está ERRADO
   - NÃO começa com "RUA" ou "AVENIDA"

5. cidade: Nome da cidade ANTES da sigla do estado
   - CRÍTICO: A cidade vem DEPOIS do bairro na linha do endereço
   - CRÍTICO: Bairro e cidade são CAMPOS DIFERENTES. Se você colocou o mesmo valor em ambos, está ERRADO
   - CRÍTICO: O valor de cidade DEVE ser diferente do valor de bairro. Se forem iguais, você está ERRADO

6. estado, cep: APENAS da linha do endereço do cliente

==========================
VALIDAÇÃO FINAL OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE ESTAS REGRAS CRÍTICAS:

1. complemento: Se aparecer "Q." ou "L." no endereço, eles DEVEM estar no complemento
   - Se você não incluiu "Q." ou "L." no complemento mas eles aparecem no endereço → ERRO GRAVE

2. bairro e cidade: Eles DEVEM ser diferentes
   - CRÍTICO: Se bairro == cidade → ERRO GRAVE. Você está ERRADO
   - CRÍTICO: Na linha do endereço, bairro vem ANTES da cidade
   - CRÍTICO: Cidade vem ANTES da sigla do estado (GO, MG, SP, etc.)
   - CRÍTICO: Se você colocou o mesmo valor em ambos, PROCURE NOVAMENTE na linha do endereço
   - CRÍTICO: O nome que vem ANTES da sigla do estado é a cidade, NÃO o bairro

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NÃO use valores de outras partes da fatura
- É MELHOR retornar campos vazios do que inventar valores incorretos

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente
- NÃO extraia o nome do cliente nesta análise - apenas o endereço
- Se não encontrar algum campo, use "" (string vazia)
