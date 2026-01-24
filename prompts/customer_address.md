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

O campo "cep" aparece sempre com 8 números. Formatos: XXXXX-XXX, XX.XXX-XXX ou XXXXXXXX.

NUNCA use "99999", "00000", "12345678" ou qualquer CEP inventado ou genérico.
Se você NÃO enxergar na imagem um CEP com exatamente 8 dígitos, use "" (string vazia).
CEP inválido ou inventado é pior que cep vazio.

==========================
REGRA ABSOLUTA - CAMPO RUA
==========================

O campo "rua" SEMPRE começa com uma destas palavras: "RUA", "AVENIDA", "ESTRADA", "RODOVIA".

SE O PRIMEIRO TEXTO DO ENDEREÇO NÃO COMEÇAR COM UMA DESSAS PALAVRAS, VOCÊ ESTÁ ERRADO.

PROCURE NO INÍCIO DO ENDEREÇO por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA".

NUNCA coloque no campo "rua":
- Nome de bairro (Centro, Área Rural, córrego, loteamento, etc.)
- Nome de cidade
- Qualquer texto que NÃO começa com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA"

Rua = via. Bairro e cidade vão nos seus campos. Rua SEMPRE começa com RUA/AVENIDA/ESTRADA/RODOVIA.

==========================
REGRA ABSOLUTA - CAMPO NÚMERO
==========================

NUNCA use "99999", "00000" ou número inventado no campo "numero".
Se não houver número na imagem → use "S/N". Se houver número → extraia o valor real.
Numero inventado é ERRO GRAVE.

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

Exemplo genérico: "..., [bairro], [CEP], [cidade], [UF]"
  → bairro = o nome entre complemento e CEP/cidade
  → cidade = o nome imediatamente antes da sigla do estado

Se você colocou o mesmo valor em bairro e cidade: você repetiu um. São dois campos distintos. Identifique a posição de cada um na imagem.

Exceção: se na imagem existir apenas UM nome entre complemento e estado, use esse nome em cidade e bairro="".

==========================
LAYOUT EM LINHAS
==========================

Em muitas faturas o endereço vem em 2 ou 3 linhas:
- Linha 1: Rua, número, complemento (sempre começa com RUA/AVENIDA/ESTRADA/RODOVIA)
- Linha 2 (se existir): BAIRRO – nome do bairro, loteamento, Área Rural, etc.
- Linha 3: CIDADE-ESTADO ou CEP + CIDADE-ESTADO

O que está na LINHA ENTRE a rua e a linha "CIDADE-ESTADO" (ou "cidade-UF") é o BAIRRO.
A CIDADE é o nome imediatamente antes do hífen ou da sigla do estado (MG, SP, etc.).

NUNCA use o nome da cidade como bairro. Bairro e cidade são campos diferentes; não repita o mesmo valor.

==========================
EXTRAÇÃO PASSO A PASSO
==========================

1. rua: 
   - Procure no INÍCIO do endereço por uma palavra que começa com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA"
   - Use "RUA SEM NOME" APENAS se a fatura disser explicitamente "Sem Nome" ou "S/N" para a via. NUNCA use como padrão ou se não tiver certeza.
   - Extraia essa palavra e tudo até a primeira vírgula
   - Se não encontrar uma palavra começando com "RUA"/"AVENIDA"/"ESTRADA"/"RODOVIA" no início, você está ERRADO
   - NÃO inclua Quadra (Q.), Lote (L.), número, apartamento, bairro, cidade no campo rua

2. numero: 
   - Se aparecer "S/N" ou "Sem Número" → use "S/N"
   - Se aparecer um número explícito de endereço → extraia esse número
   - NUNCA use 99999, 00000 ou qualquer número inventado. Se não enxergar número → "S/N"
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
   - Em layout em linhas: a linha ENTRE rua e "CIDADE-ESTADO" é o bairro. Extraia esse texto.
   - Bairros podem ser Centro, Jardim X, Área Rural, córrego, loteamento, etc. "Área Rural" / "Area Rural" é válido. NUNCA use o nome da cidade como bairro.
   - Extraia exatamente como está. Bairro NÃO começa com "RUA" ou "AVENIDA".

5. cidade: 
   - Nome IMEDIATAMENTE ANTES da sigla do estado (MG, SP, etc.) ou antes do hífen em "CIDADE-ESTADO". Segunda posição.
   - Extraia exatamente como está. APENAS da linha do endereço do cliente.
   - NUNCA use o mesmo valor que bairro.

6. estado: 
   - Sigla de 2 letras maiúsculas após a cidade
   - Formato: "GO", "MG", "SP", etc.
   - Extraia APENAS da linha do endereço do cliente

7. cep: 
   - Números após "CEP:" ou "CEP" na linha do endereço. Extraia apenas os 8 dígitos (pode manter formatação XX.XXX-XXX ou XXXXX-XXX).
   - Se NÃO enxergar 8 dígitos na imagem, use "".
   - NUNCA use 99999, 00000, 12345678 ou similares. NÃO invente CEP.
   - NÃO use CEPs de outras partes da fatura.

==========================
VALIDAÇÃO OBRIGATÓRIA
==========================

ANTES DE RETORNAR O JSON, VERIFIQUE:

1. rua: DEVE começar com "RUA", "AVENIDA", "ESTRADA" ou "RODOVIA"
   - Se não começar com uma dessas palavras → ERRO GRAVE
   - NÃO deve conter bairro, cidade, Quadra, Lote, número, apartamento

2. numero: "S/N" ou número de endereço (lido na imagem). NUNCA 99999, 00000 ou inventado.
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

6. estado: APENAS da linha do endereço do cliente.
7. cep: Exatamente 8 dígitos lidos na imagem, ou "". NUNCA 99999, 00000 ou inventados.

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
- Se você não encontrar um campo explicitamente na imagem, use "" (string vazia) ou "S/N" (apenas para numero)
- NÃO invente nomes de rua, números, complementos, bairros, cidades, estados ou CEPs
- NUNCA CEP 99999, 00000, 12345678 ou genéricos. CEP = 8 dígitos lidos na imagem; senão "".
- NUNCA numero 99999, 00000 ou inventado. Numero = "S/N" ou número lido na imagem; senão "S/N".
- Nomes de bairro (Centro, Área Rural, etc.) vão em bairro, nunca em rua. Rua começa com RUA/AVENIDA/ESTRADA/RODOVIA.
- Use "RUA SEM NOME" apenas se o documento disser explicitamente isso para a via.
- NÃO use valores de outras partes da fatura
- É MELHOR retornar campos vazios do que inventar valores incorretos

IMPORTANTE: 
- Esta imagem contém APENAS dados do endereço do cliente
- NÃO extraia o nome do cliente nesta análise - apenas o endereço
- Se não encontrar algum campo, use "" (string vazia)
