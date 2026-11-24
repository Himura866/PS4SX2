# HIMURA SWITCH PS4 — R03: correção libcxx18 (2026-11-24)

## Resultado observado no CircleCI

- Pipeline #31, `compilar_eden_ps4`, falhou.
- Instalação de dependências e checkout passaram (etapas verdes no print enviado).
- Etapa vermelha: `Construir Eden / ELF / PKG PS4 e registrar falhas`.
- Log final observado: `HIMURA SWITCH build result: stage=libcxx18 exit=1` e `CircleCI received exit code 1`.
- Nenhum PKG, ELF de Eden ou teste de jogo foi confirmado.

## Causa verificada no fonte

O script upstream `ci/30-libcxx.sh` procura `__linux__` nas primeiras 120 linhas de `deps/llvm-project/libcxx/src/filesystem/operations.cpp` antes de adicionar um guard. No LLVM `llvmorg-18.1.8`, o trecho em questão usa `#if __has_include(<sys/sendfile.h>)` (aprox. linha 40), sem o `__linux__` esperado. A etapa falha no patch de compatibilidade.

Fonte fixada: https://github.com/llvm/llvm-project/blob/llvmorg-18.1.8/libcxx/src/filesystem/operations.cpp

## Alteração aplicada

Commit: `fbaf783fcbd9a242257f566cf1e94c07adf363a4`.

Arquivo: `ci/himura-switch-build.sh` na branch `himura-switch-ps4`.

A R03 substitui a tentativa de localizar `__linux__` pelo ajuste do guard real:

```cpp
#if __has_include(<sys/sendfile.h>) && !defined(__ORBIS__)
```

A alteração é feita apenas na cópia temporária da fonte durante o build do CircleCI. Não alteramos a branch principal do projeto PS2, nem as fontes upstream.

## Próxima verificação

A correção foi salva no GitHub; ainda **não foi comprovada uma compilação R03 bem-sucedida**.
No CircleCI, conferir a execução mais recente de `fix(switch): corrigir guard sendfile libcxx18 no build Linux`.
Se falhar, informar a primeira mensagem `ERROR` no job e o estágio `stage=...` do arquivo `switch-build-reports/result.txt`.

## Checkpoints anteriores

- R01: pré-validação da fonte, verde.
- R02: configuração e scripts do build, salvos em GitHub e ZIP no Google Drive.
- R03: patch do libcxx18, commit acima, registrado neste arquivo.
