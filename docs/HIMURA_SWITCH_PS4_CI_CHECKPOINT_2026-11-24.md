# HIMURA SWITCH PS4 — checkpoint CI — 2026-11-24

## Confirmado pelo teste no CircleCI

- Projeto: Himura866/PS4SX2, branch isolada `himura-switch-ps4`.
- Configuração usada: `.circleci/switch-config.yml` (`validar_base_switch` > `verificar_fonte_switch`).
- Resultado relatado pelo testador: etapas verdes e três artefatos: `arquivos-disponiveis.txt`, `commit-fonte.txt`, `status.txt`.
- O job baixa a árvore pública de `MrKitsune9/Orbis-EDEN` e verifica os scripts `configure-eden.sh` e `package-eden.sh`.
- **Não é uma compilação do emulador, não produziu EBOOT nem PKG.**

## Fonte pública inspecionada

- https://github.com/MrKitsune9/Orbis-EDEN
- Sequência de scripts: `ci/05-prepare.sh`, `10-linuxify.sh`, `20-sdk.sh`, `30-libcxx.sh`, `40-openssl-ffmpeg.sh`, `60-eden.sh`, `70-package.sh`.
- O README afirma testes reais de jogos em PS4 Pro, mas a compilação Linux via CircleCI ainda não foi testada neste projeto.
- A documentação de compilação descreve um build Windows 11/Git Bash com caminhos absolutos da máquina original.
- `configure-eden.sh` e `tools/env-build.sh` ainda contêm caminhos Windows `C:/nxorbis/repo` e `/c/nxorbis/repo`; `ci/10-linuxify.sh` não adapta todos esses caminhos, portanto é necessário corrigir antes do build Linux.
- `ci/70-package.sh` exige ferramentas Linux `create-fself`, `create-gp4` e `PkgTool.Core`/DLL, ainda não verificadas no executor. Sem elas o PKG não pode ser empacotado.
- `eboot.bin` no repositório público raiz tem tamanho 0 e **não** é executável final.
- SDK/LLVM enviados anteriormente são insumos e devem ter disponibilidade e layout confirmados na infraestrutura de build.

## Próximo marco (não executado)

1. Adaptar os caminhos, flags e ferramenta host para Linux, preservando a branch do PS2 `main`.
2. Resolver dependências e executar build do alvo `eden-ps4` via CircleCI.
3. Somente após um ELF válido, gerar PKG com ferramentas disponíveis.
4. Guardar logs, SHA, ELF exato, PKG e instruções de teste; validar boot e carregamento de um homebrew real no PS4 Pro.
5. Somente depois testar jogos leves e medir FPS reais.

Nenhuma afirmação de jogo jogável pode ser extraída da primeira execução de pré-validação.
