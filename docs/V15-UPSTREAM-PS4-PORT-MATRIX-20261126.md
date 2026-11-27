# HIMURA SWITCH V15 — matriz de integração Eden/New Eden no PS4 Pro

**Checkpoint de pesquisa: 26/11/2026. Não representa PKG ou compatibilidade de jogos comprovados.**

## Nome da versão
O usuário confirmou: quando houver novo PKG que realmente inicie e execute jogos no PS4 Pro com a interface HIMURA, seu nome visível será **HIMURA SWITCH V15**. **R13** identifica somente a versão cujo menu/arte servem de referência; **New Eden 04.89** é a referência técnica que o usuário testou executando Silksong. Não anunciar V15 como pronta até teste de hardware, incluindo gameplay.

## Fontes GitHub auditadas — não supor equivalência binária
1. **New Eden 04.89 original do usuário**, que ele confirmou iniciar e jogar Silksong, **não tem código-fonte correspondente comprovadamente localizado**. O arquivo `eboot.bin` exportado tem SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381` e a árvore app0 tem 15 membros verificáveis. A implementação de menu original está compilada no executável.
2. **PS4 Switch Emu** — https://github.com/ps4-switch-emu/ps4-switch-emu, HEAD de `main` auditado `1c6066e8685829df884ba6de0bce39c45a663bbb` (13/10/2026). Seu submódulo `eden` aponta para https://github.com/ps4-switch-emu/ps4-switch-emu-core, HEAD auditado `68e15e05f5c3bc19d20bd09fb2f32ce4fecc2e9c`. Este é **outro port experimental**, não identificado como fonte exata do New Eden 04.89. PS4 Switch Emu usa ID `SWEM00001` e diretório `/data/switch-emu`.
3. **Eden4** — https://github.com/xatyy/Eden4, HEAD `fab246cbac93c7995aaf451dca83ae93ba0bd234` (19/10/2026). Port Orbis experimental com menu, JIT e GPU RADV; diretório `/data/EdenPS4`. Não é um plugin que possa ser colado no executável 04.89.
4. **Orbis-EDEN** — https://github.com/MrKitsune9/Orbis-EDEN, cadeia de **46 patches** em `patches/eden/`, originalmente vinculada ao Eden `5f142c79`. Documenta PS4 Pro firmware 13.52 e patches para áudio, JIT, memória, textura, cores e Miis. Todos exigem avaliação da base/fonte antes de aplicar; não transplantar patches binários entre ELFs de versões diferentes.
5. **HIMURA R13** — branch `Himura866/PS4SX2/himura-switch-r13-stability-staging` em `08c93c95904bbf56d1677d5d8ebd203cae1e5e7e`. O usuário confirmou que o menu personalizado abriu, mas essa evidência não demonstra que o motor R13 rode Silksong como o New Eden 04.89.

## Elementos transferíveis — status: candidatos, NÃO integrados

| Prioridade | Recurso candidato | Origem verificada | Condição de integração e validação |
|---|---|---|---|
| P0 | **Empacotamento PS4 executável válido** | `ps4-switch-emu/scripts/package-eden.sh`: `create-fself-git --eboot`, verificador `check-oelf.cmake`, `make-pkg.sh` | Comparar estrutura do `eboot.bin` original e PKG refeito, autenticação / forma de SELF, tipo do ELF, SFO, keystone, ID e orçamento de memória; **não assumir que uma cópia ELF + GP4 basta**. A diferença é uma hipótese de CE-30081, não causa confirmada. |
| P0 | **Preservar o 04.89 que roda Silksong** | Original com SHA acima | Não sobrescrever executável original, nem o app instalado. Testar repack sem alterações e jogo no PS4 em ambiente seguro antes de personalizar. |
| P1 | **Vulkan Mesa RADV / memória PS4** | PS4 Switch Emu, Eden4, Orbis-EDEN | Comparar versões de driver, API, níveis de GPU e limite de memória. Não instalar a configuração de outro port sem compatibilidade comprovada. |
| P1 | **JIT Dynarmic / fastmem / CPU Jaguar** | Eden4 e Orbis-EDEN patches 0003, 0005, 0007, 0008 | Depende de fonte equivalente, ABI e layout PS4. Testar boot, regressão e cache com dados observáveis. |
| P1 | **Áudio PS4** | Orbis-EDEN patch 0002, PS4 Switch Emu AudioOut | Manter áudio original como baseline, testar em jogo; não afirmar eliminação de chiado sem captura. |
| P1 | **Controle DualShock 4 e voltar ao menu** | `ps4-switch-emu-core/externals/ps4sup/ps4_launcher.h` (`ps4_status_draw_home`, `ps4_launcher_show`) | Interface pública específica daquele port; não chamar diretamente do 04.89 sem símbolos exportados/ABI. |
| P1 | **Fontes do menu interativo (R13) e cena samurai** | R13 `assets/r11-approved-menu.webp` e `assets/r11-approved-icon.webp` | Arte R13 original tem botões e capas pré-renderizados, limpar apenas elementos falsos e painel escuro; usar controles de UI reais com foco DualShock 4. **Não colocar screenshot composta como fundo do New Eden.** |
| P2 | **Menus PT-BR e nome HIMURA SWITCH V15** | Orbis-EDEN menu de seleção de idioma, R13 UI, New Eden strings existentes | Só aplicar depois que a base repacotada funcionar; traduzir lógica e avisos sem editar textos binários às cegas. Usuário quer textos em PT-BR, **sem voz/narração**. |
| P2 | **FPS real e diagnósticos** | New Eden 04.89 já possui `show_fps_overlay`; PS4 Switch Emu tem overlay/frame times | Preferir contador já funcional na base; não usar números fixos/decorativos. Criar logs de primeiro frame, crash e áudio com nomenclatura que não invada saves. |
| P2 | **Compatibilidade de jogos** | Orbis-EDEN patches 0031–0034 (Miis/system-data) e 0009/0010 GPU | Em Mario Kart, separar tela Mii de erro NCA, validar dumps legítimos e firmware; patches são hipóteses técnicas, não correções comprovadas. |

## Divergência de identidades, dados e risco
- New Eden original: `EDNP00001`, `IV0000-EDNP00001_00-EDENPS4000000000`, APP_VER `04.89`, diretórios `/data/eden-ps4`.
- PS4 Switch Emu: `SWEM00001`, `/data/switch-emu`; Eden4: `/data/EdenPS4`; HIMURA R13: `HIMU00011`. Esses caminhos e IDs não são intercambiáveis.
- Alterar `APP_VER`, `eboot.bin`, `param.sfo`, `keystone`, formato fSELF ou roteamento de saves antes do primeiro boot independente cria múltiplas hipóteses e impede saber qual modificação quebrou o pacote.
- Conjunto de chaves, firmware, NSP/XCI, saves e backups **não deve** ser publicado no repositório público. Não colocar app0 proprietário do usuário no repo público; preservar apenas no privado.
- Os projetos externos são código de terceiros sob licenças, com autores, avisos e condições a manter. O projeto resultante não pode ser apresentado como oficial de Eden ou Nintendo.

## Gates V15
1. **P0:** classificar o pacote de origem (tipo de SELF/ELF), metadata e receita de PKG; a validação `pkg_validate` testa estrutura, não autenticação/boot em PS4. Registrar comparação sem modificar a base.
2. **P0:** gerar PKG com arquivos originais, sem SFO, ícone ou texto alterado, em identidade de teste que não sobreponha o original **somente quando a mudança de identidade for demonstrada segura**. Se não houver instalação segura paralela, não recomendar instalar.
3. **P0:** teste real do console: app abre, menu responde, Silksong entra em gameplay. Se falhar, capturar erro e logs, comparar com PKG original.
4. **P1:** uma mudança de UI por iteração, comparar boot e jogo. Corrigir botões fictícios e fundo preto com componentes reais, não máscaras.
5. **P2:** PT-BR integral, menu e configurações, overlay FPS, retorno e compatibilidade ampliada, cada um com teste de regressão.
6. **Entrega:** PKG marcado `V15` **apenas após** boot e jogo comprovados pelo usuário. CI verde sem gameplay fica `experimento / não homologado`.

## Próximo trabalho no código
Criar verificador de formato PS4 fSELF e comparação do empacotamento original vs recriado **sem tentar re-assinar ELF por substituição simples**. Identificar se é viável reconstruir o **mesmo código-fonte** do New Eden original; se não for, o port mais recente precisará ser adaptado e validado como um novo motor separado, nunca descrito como transplante exato do 04.89.
