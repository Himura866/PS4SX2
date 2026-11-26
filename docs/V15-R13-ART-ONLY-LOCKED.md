# HIMURA SWITCH PS4 V15 — reaproveitar SOMENTE as artes da R13

**Confirmação explícita do usuário, 26/11/2026.** A V15 deve usar o **New Eden 04.89 original** como base de execução, e trazer **somente** duas artes aprovadas da R13:

1. **Capa externa PS4:** `assets/r11-approved-icon.webp` da branch `himura-switch-r13-stability-staging`, Git blob `304e9d695563027452b65bd7c66a0f369b6b8d1d`, SHA-256 `ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778`. Render 512×512 para `sce_sys/icon0.png`. A capa HIMURA SWITCH PS4 com samurai e controle azul/vermelho aparece **só no mosaico de aplicativos PS4**, nunca no interior do emulador.
2. **Papel de parede samurai:** `assets/r11-approved-menu.webp` da MESMA branch R13, Git blob `e054dcc7e88bba273508abc60100cb5148cfd08c`, SHA-256 `b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058`. Esta imagem é uma **referência composta**, NÃO um wallpaper puro. Ela já contém botões falsos, títulos, mock covers, setas e instruções no rodapé. É proibido simplesmente colocar essa captura por trás de widgets reais, porque duplicaria controles e capas.

## Correção do erro na R13

O script `ci/patch-r11-approved-menu.py` da R13 desenhava coberturas pretas opacas sobre cinco capas fictícias e a faixa de atalhos desenhada sobre a arte, causando os retângulos pretos e sobreposição. A correção deve preservar os elementos de cenário samurai e monte Fuji, criando um **wallpaper sem UI impressa**, e desenhar a barra superior e carrossel por **elementos de interface operacionais**, não por pixels de fundo.

**Não copiar o núcleo, as telas estáticas, as máscaras pretas nem os botões falsos de R13.** Também não substituir a arte aprovada por ilustração samurai gerada sem correspondência.

## Integração segura

- Manter `EDNP00001` e versão técnica `04.89`; `V15` é rótulo da personalização.
- Separar `sce_sys/icon0.png` de qualquer `/app0/skin/...`; não usar o arquivo de capa do PS4 como menu do emulador.
- A R13 tinha funções de toolbar/carrossel reais em outra revisão de código, mas o `eboot.bin` recebido da versão 04.89 é um executável compilado e **NÃO é compatível automaticamente com os patches de código R13**.
- `ci/prepare-neweden-v15-r13-art.py` fornece somente o ícone externo validado; mantém o screenshot composto em `reference-only`, com `runtime_wallpaper_ready=false`, e nenhum PKG. `ci/test-neweden-v15-r13-art.py` rejeita arte alterada.
- Job CircleCI `validar_neweden_v15_r13_assets` compila/testa somente esse recurso gráfico, salvando icon0 e manifesto como artefatos; **não é um build PKG**, e não há status de execução confirmado.
- A funcionalidade completa do menu com botões reais no topo, carrossel sem painel preto, português, News/Temas removidos, FPS e créditos exige nova implementação específica na base `04.89` e teste no PS4 Pro.

Aprovado como requisito; **não confundir documentação/asset com integração de runtime pronta**.


## Correção obrigatória do escopo pelo usuário (18:33 BRT, 26/11/2026)

**O papel de parede da R13 deve manter EXATAMENTE o mesmo aspecto visual**: cenário samurai, lua, montanha, paleta, posição de elementos, composição e proporções. **Não usar** a nova ilustração alternativa que havia sido criada como substituição.

A edição solicitada na arte interna é **MÍNIMA**:
- Retirar os **botões fictícios desenhados na faixa INFERIOR** do papel de parede. Os botões funcionais da interface devem permanecer no TOPO, mantendo o estilo visual antigo, mas implementados como ações reais do controlador.
- Retirar o **fundo/painel preto colocado ABAIXO das capas dos jogos**, mostrando a cena no lugar dessa faixa. **Não desenhar outros retângulos escuros para esconder erros**.
- **Todo o restante da arte da R13 deve ficar igual**, e a capa externa R13 continua exclusiva do mosaico de aplicativos do PS4.

A imagem de referência aprovada ainda contém controles/capas e títulos incorporados aos pixels; por isso a implementação do menu deve evitar duplicar elementos reais sobre elementos fictícios. A fidelidade visual **não implica usar a própria captura como interface clicável**. A separação correta dos elementos deve ser testada visualmente antes de empacotar, sem reprojetar a cena.

**Estado desta exigência:** documentação aprovada; arte limpa e integração funcional ao executável 04.89 ainda não validadas no PS4. Não divulgar PKG incompleto como funcional.
