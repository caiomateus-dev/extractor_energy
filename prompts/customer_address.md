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
REGRA ABSOLUTA - CAMPO CEP
==========================

O campo "cep" aparece sempre com 8 números. XXXXX-XXX ou XX.XXX-XXX ou XXXXXXXX

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
BAIRRO vs CIDADE - POSIÇÃO NA IMAGEM
==========================

Na linha do endereço, a ORDEM é: ... complemento → BAIRRO → CEP (se houver) → CIDADE → ESTADO.

- O nome que vem DEPOIS do complemento e ANTES do CEP/cidade é o BAIRRO. Extraia esse.
- O nome que vem IMEDIATAMENTE ANTES da sigla do estado (MG, SP, etc.) é a CIDADE. Extraia esse.

São dois campos em posições diferentes. Extraia o valor correto de cada posição.

Exemplo: "..., Centro, 30100-000, Belo Horizonte, MG"
  → bairro = "Centro" (entre complemento e CEP)
  → cidade = "Belo Horizonte" (antes de MG)

Se você colocou o mesmo valor em bairro e cidade: você repetiu um. Olhe de novo a ordem na imagem, identifique o primeiro nome (bairro) e o segundo (cidade), e extraia cada um corretamente.

Exceção: se na imagem existir apenas UM nome entre complemento e estado, use esse nome em cidade e bairro="".

==========================
LAYOUT EM LINHAS (FATURAS CEMIG etc.)
==========================

Em várias faturas o endereço vem em 2 ou 3 LINHAS:
- Linha 1: Rua, número, complemento (ex.: RUA RIO DE JANEIRO 122 CS)
- Linha 2: BAIRRO (ex.: ANTONIO SECRETARIO, Centro, Jardim X)
- Linha 3: CIDADE-ESTADO ou CEP + CIDADE-ESTADO (ex.: VAZANTE-MG)

O que está na LINHA ENTRE a rua e a linha "CIDADE-ESTADO" é o BAIRRO, 
"Vila tal" – no contexto do endereço, isso é bairro. Extraia em "bairro".
A CIDADE é o nome antes do hífen ou da sigla (MG, SP). Ex.: "VAZANTE-MG" → cidade="Vazante", estado="MG".

NUNCA use o nome da cidade como bairro. Se a linha 2 existe e tem texto (ex.: ANTONIO SECRETARIO), esse texto é o bairro.

Exemplo real:
  RUA RIO DE JANEIRO 122 CS
  ANTONIO SECRETARIO
  VAZANTE-MG
→ bairro = "ANTONIO SECRETARIO", cidade = "Vazante", estado = "MG". NUNCA bairro = "Vazante".

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
   - Nome que aparece DEPOIS do complemento e ANTES da linha "CIDADE-ESTADO" (ou CEP/cidade). Primeira posição.
   - Se o endereço está em linhas: a linha ENTRE rua e "CIDADE-ESTADO" é o bairro (ex.: ANTONIO SECRETARIO). Extraia esse texto.
   - Bairros podem ter nomes como "Antonio Secretario", "Centro", "Jardim X". NUNCA use o nome da cidade como bairro.
   - Extraia exatamente como está. NÃO começa com "RUA" ou "AVENIDA".

5. cidade: 
   - Nome IMEDIATAMENTE ANTES da sigla do estado (MG, SP) ou antes do hífen em "CIDADE-ESTADO" (ex.: VAZANTE-MG → "Vazante"). Segunda posição.
   - Extraia exatamente como está. APENAS da linha do endereço do cliente.
   - NUNCA use o mesmo valor que bairro.

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

4. bairro: Primeiro nome entre complemento e estado (antes do CEP/cidade). bairro != cidade.
5. cidade: Segundo nome, o que vem logo antes da sigla (MG, SP). cidade != bairro.

6. estado, cep: APENAS da linha do endereço do cliente

==========================
VALIDAÇÃO FINAL OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE ESTAS REGRAS CRÍTICAS:

1. complemento: Se aparecer "Q." ou "L." no endereço, eles DEVEM estar no complemento
   - Se você não incluiu "Q." ou "L." no complemento mas eles aparecem no endereço → ERRO GRAVE

2. bairro e cidade: Dois campos, duas posições, dois valores
   - Em layout em linhas: linha entre rua e "CIDADE-ESTADO" = bairro; nome antes de MG/SP = cidade.
   - Primeiro nome (após complemento, antes CEP/cidade) = bairro. Segundo (antes do estado) = cidade.
   - Se bairro == cidade → ERRO. Você repetiu um. Nunca use o nome da cidade como bairro.

REGRA ABSOLUTA - NÃO INVENTE VALORES:
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NÃO use valores de outras partes da fatura
- É MELHOR retornar campos vazios do que inventar valores incorretos

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente
- NÃO extraia o nome do cliente nesta análise - apenas o endereço
- Se não encontrar algum campo, use "" (string vazia)
