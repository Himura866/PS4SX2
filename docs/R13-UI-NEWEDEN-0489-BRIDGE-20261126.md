# HIMURA SWITCH — ponte R13 visual + New Eden 04.89 (experimento isolado)

## Decisão técnica — 26/11/2026
O usuário quer **a interface navegável da R13** e **a execução de jogos do New Eden 04.89**, sem regredir a inicialização. Referência R13: `himura-switch-r13-stability-staging` @ `08c93c95904bbf56d1677d5d8ebd203cae1e5e7e`; CI da R13 (validação e PKG) retornou *success*, mas isso não demonstra execução estável de jogos. Referência do New Eden: pacote que o usuário testou rodando até parte do Silksong; app0 original exportado do console. Esta branch parte de `himura-switch-v15-baseline-original` @ `0fc22505dbc6356e54a5bce40c13783f6130fc12`. Não substituir branches existentes.

## O que pode e não pode ser unido
- **NÃO** copiar `eboot.bin` da R13 sobre o New Eden: o executável da R13 contém *frontend e núcleo Eden4*; não é um módulo de interface plugável. Há diferenças de identidade/versão e ABI/estrutura interna não verificada. Tampouco combinar os dois ELFs por concatenação.
- **SIM** reutilizar desenho, fluxo de navegação, assets aprovados e lógica de interface R13 como **especificação de uma camada de frontend**, implementada para o New Eden 04.89 somente quando houver código-fonte compatível ou um mecanismo seguro e testado de integração; não afirmar que o código-fonte Eden4 equivale ao eboot original 04.89.
- Os símbolos do app0 04.89 mapeiam Ui::HomeMenu::DrawHome, DrawRetroHome, DrawSettings, Navigate, SettingItems, DrawBottomBar, DrawHeader. Isso ajuda localizar implementação, mas NÃO entrega um frontend de alto nível que possa ser trocado.
- Preservar integralmente eboot 04.89 até um teste independente do reempacotamento puro. SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381`. Baseline de PKG original: `06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd`.
- Manter dados legados de New Eden, TITLE_ID `EDNP00001` e APP_VER `04.89` na prova de inicialização, sem misturar com TITLE_ID R13 `HIMU00011`.

## Prioridades e critérios verificáveis
1. **Boot puro**: export app0 original sem mudanças, SFO e ícone originais, todos os hashes de 15 arquivos intactos; empacotamento com GP4/LibOrbisPkg; conferir `pkg_validate`; teste PS4 real. Se CE-30081 persistir no repack idêntico, concentrar no formato/identificação/autorização do pacote, não no layout.
2. **Capa externa**: ícone R13 aprovado, apenas sce_sys/icon0.png, sem tocar no eboot; alterar um componente por pacote e revalidar boot.
3. **Interface R13**: manter lua vermelha, samurai, montanha e a mesma composição; criar asset de fundo sem os botões/capas desenhados nos pixels. Desenhar barra superior e carrossel com widgets reais. Não usar mascaramento preto (há 5 FillRoundRect na receita R13). Preservar navegação DS4, neon vermelho e seleção/início do jogo.
4. **Português Brasil**: rótulos, submenus e mensagens reais; não adicionar dublagem, pois o usuário confirmou apenas tradução escrita. Não substituir strings no binário sem teste de offsets, tamanhos e execução.
5. **Configurações reais**: reaproveitar renderer, resolução, cache, contador de FPS, modo TV/portátil e controles *já presentes* na base, adicionando atalhos somente quando vinculados ao estado interno. Não inventar recursos ou FPS.
6. **Regressão**: menu, XMB, scan USB NSP/XCI, boot de Silksong, áudio, salvar/voltar ao menu e saída. Indicar PASSA / FALHA / NÃO TESTADO para cada etapa. Preservar builds antigas como fallback.

## Estado nesta branch
Checkpoint **de integração planejada e isolada**, não PKG pronto: nenhum eboot substituído, nenhum motor R13 usado, nenhuma mudança de interface instalada, nenhum teste no PS4 realizado a partir desta branch. CI verde não é prova de boot. Não agendar compilação longa apenas para documentação.

## Bloqueio técnico
O código-fonte exato correspondente ao eboot do New Eden 04.89 ainda não foi identificado neste checkpoint; possuímos o ELF e símbolos. Sem ele ou interface de plugin suportada, não é seguro prometer o transplante direto da UI R13. O objetivo imediato é confirmar o repack byte-a-byte da base 04.89 com teste no console, e só depois prosseguir com a integração incremental.
