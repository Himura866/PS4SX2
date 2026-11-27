# HIMURA SWITCH V15 — teste real do PS4 e recuperação das duas artes R13 (27/11/2026)

## Resultado relatado pelo proprietário (teste no PS4 Pro)

- O PKG experimental `HIMURA-SWITCH-V15-PARALLEL-TEST-NAO-HOMOLOGADO.pkg` instalou, mas **não iniciou**: o sistema mostrou "não é possível continuar usando o aplicativo; os dados do aplicativo estão corrompidos".
- O aplicativo experimental foi excluído após o erro.
- O New Eden 04.89 funcional **já tinha sido retirado do console e guardado separadamente** antes do teste. Portanto, não atribuir este erro a conflito entre instalações.
- A capa externa da V15 não era a versão samurai aprovada.

## Causa comprovada da capa externa ausente

O job privado chamou o builder com `--baseline-original --boot-fself-experiment --parallel-title-experiment`.
A ramificação `baseline_original` do builder original preservava o `sce_sys/icon0.png` do New Eden mesmo quando havia `--r13-icon`, gerando `r13_external_icon_sha256 = None`.
O job, inclusive, aceitava esse valor `None` como esperado. Assim, uma CI verde não verificava a capa aprovada.

A branch `himura-switch-v15-r13-icon-recovery` introduz:
1. Conversão e hash SHA-256 obrigatórios da **mesma** arte já aprovada: `assets/r11-approved-icon.webp`.
2. Inclusão de `sce_sys/icon0.png` no PKG experimental com identidade `HIMU00015`, sem tocar no ramo de baseline original puro.
3. Verificação do hash do ícone **extraído do PKG gerado**, bloqueando build se for diferente do arquivo preparado.
4. Teste isolado de conversão e rejeição de arte adulterada.

## Fundo interno (requisito visual ainda não concluído)

Manter a cena SAMURAI aprovada `assets/r11-approved-menu.webp`, incluindo lua vermelha, montanha, cores, enquadramento e proporções. O arquivo atual é uma captura composta com elementos fictícios: ainda não é um wallpaper livre de interface.

Ao integrar ao menu do motor real:
- Remover **somente** os botões falsos na parte de baixo e o **painel/fundo preto que aparece atrás e ao redor da capa do jogo selecionado quando ela aumenta de tamanho**. Não remover o efeito de foco/zoom: a capa selecionada deve continuar maior do que as outras, com destaque visual; mostrar o cenário samurai aprovado atrás dela, sem retângulo ou moldura preta opaca.
- Não confundir esse painel de seleção com o fundo inteiro da biblioteca: a paisagem deve permanecer visível e intacta também durante a seleção do jogo.
- Não alterar a paisagem aprovada nem substituir por outra ilustração.
- Controles funcionais **no topo**, navegação por DualShock 4 e biblioteca com capas reais sobre o fundo.
- Não confundir a capa PS4 (ícone externo) com o wallpaper interno.

## Bloqueio crítico ainda aberto

O PS4 **rejeitou a inicialização**, apesar do `pkg_validate`, comparação de metadados e estrutura do wrapper fSELF passarem. Portanto, **não** classificar como V15 instalável ou jogável.
Investigar em separado formatação e assinatura do PKG, SELF e integridade do conteúdo real; comparar com os arquivos e PKG comprovadamente funcionais da versão 04.89. Não editar ou substituir a cópia funcional guardada. Apenas depois de boot comprovado no console validar menu, áudio, jogo, retorno e desempenho.
