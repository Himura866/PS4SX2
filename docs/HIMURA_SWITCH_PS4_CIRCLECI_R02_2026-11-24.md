# HIMURA SWITCH PS4 — CircleCI R02 (24/11/2026)

## Estado preservado

- Execucao R01: verde, acesso ao codigo-fonte validado e tres TXT publicados (informado pelo usuario).
- Checkpoint anterior: docs/HIMURA_SWITCH_PS4_CI_CHECKPOINT_2026-11-24.md.
- Nova R02 isolada em Himura866/PS4SX2, branch `himura-switch-ps4`.
- A branch principal do PS4SX2 NAO foi alterada.

## R02 — o que foi preparado

- Workflow `tentar_compilacao_switch` em `.circleci/switch-config.yml`.
- Script `ci/himura-switch-build.sh`: baixa Orbis Eden num commit fixo, confere SHA-256 do SDK publico, adapta caminhos Windows em arquivos selecionados no workspace Linux, instala OpenOrbis e invoca scripts upstream de libc++18, OpenSSL, FFmpeg, Eden e packaging.
- Commit Orbis Eden fixado: `c9a26c80d3b7a8b47f68b5a247fcee6d6d17707d`.
- SDK v1 sha256: `f4f079a4df334b46a76996f895283904283d6a006f97102aafaa53d4ecfc9622` (igual ao tar recebido nesta conversa).
- Resultados esperados: artifacts `switch-build-reports` (build.log, source-commit.txt, result.txt) e, APENAS SE TUDO COMPILAR, `switch-build-pkgs` (ELF, PKG).
- Esta nova tentativa NAO foi executada nem validada em ambiente de CircleCI na presente etapa. O port Linux upstream pode precisar de ajustes adicionais; falhas ficam nos logs.

## Como executar somente a branch Switch (sem repetir a validação R01)

1. CircleCI > PS4SX2 > Oleodutos (Pipelines) > Pipeline de gatilho (Trigger).
2. Selecione o projeto PS4SX2 e o pipeline HIMURA-SWITCH-PS4.
3. Config Source e Checkout Source: `himura-switch-ps4` nas duas.
4. Execute uma vez e abra `tentar_compilacao_switch` / `compilar_eden_ps4`.
5. Se falhar: em Etapas, abra o primeiro erro; em Artefatos, abra `switch-build-reports/build.log` e `result.txt`. Compartilhe o trecho de erro.
6. Caso haja PKG: preserve SHA, ELF e arquivos de log e teste no PS4 Pro antes de alegar compatibilidade com jogos.

## Riscos abertos

- Ainda falta comprovar se `ci/30-libcxx.sh`, `40-openssl-ffmpeg.sh`, `60-eden.sh` e `70-package.sh` compilam de ponta a ponta em Ubuntu 24.04.
- O código público originalmente usa Windows/Git Bash. A migração foi preparada, mas não verificada pelo CircleCI até o proximo run.
- Build de ELF/PKG nao prova boot, shaders ou suporte a jogos Switch.
- Nunca incluir jogos, firmware ou chaves proprietárias no repositório.
