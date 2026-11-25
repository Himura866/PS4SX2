# HIMURA SWITCH PS4 — R07: usar bases que ja rodam no PS4

Data: 2026-11-25
Branch de estudo: `himura-switch-base-eden4`
Branch existente preservada: `himura-switch-ps4` (R06)
PS2: nao alterar a branch principal, nem seus arquivos.

## Decisao tecnica

Nao recriar emulacao Switch do zero. O nosso script R06 ja parte do
`MrKitsune9/Orbis-EDEN` no commit `c9a26c80d3b7a8b47f68b5a247fcee6d6d17707d`.
Ele traz Eden, patches especificos do PS4, OpenOrbis e Mesa RADV.

Mantemos R06 como referencia de compilacao, pois ja houve avanco em `libcxx18`,
mas nao temos ainda o ELF/PKG final nem teste de boot local.

Abrimos um caminho independente para avaliar **Eden4** e importar apenas
melhorias comprovadas depois de reproduzir a compilacao e os testes.
Nao substituir componentes da R06 cegamente: as bases usam LLVM/SDK/driver
e gerenciadores de memoria diferentes.

## Comparativo verificado nos repositorios

| Base | Evidencia documentada | Pontos uteis | Risco/limite |
|---|---|---|---|
| [Orbis Eden](https://github.com/MrKitsune9/Orbis-EDEN) | Relata jogos abrindo no PS4 Pro; Mario Kart 8 Deluxe 13-16 fps em corrida na v0.1.0 | Ja usada pela R06, patches especificos PS4, LLVM18 | Cores, travamentos ao fechar, memoria, limite de CPU |
| [Eden4](https://github.com/xatyy/Eden4) | Build PKG experimental e testes declarados no PS4 Pro em modo base | HOME, varios controles, retorno ao menu, gestao de memoria, JIT e diagnostico | Compilacao diferente (LLVM21/PacBrew/Mesa26), modo Pro GPU nao suportado, funcionalidade nem toda confirmada |
| [ps4-switch-emu](https://github.com/ps4-switch-emu/ps4-switch-emu) | Codigo e instrucoes de build, pacote experimental | Ferramentas de benchmark NRO, overlay FPS, logs e menus | Docker, dependencias especificas; ainda necessita validacao no console do usuario |
| [NX on Orbis](https://github.com/alechurri/nx-on-orbis) | Historico de 29 testes, jogo em corrida | Referencia original e diagnosticos | Projeto original descontinuado; desempenho limitado |

Fontes de detalhes:
- [Orbis Eden README](https://github.com/MrKitsune9/Orbis-EDEN/blob/main/README.md)
- [Eden4 README](https://github.com/xatyy/Eden4/blob/main/README.md)
- [Eden4 building](https://github.com/xatyy/Eden4/blob/main/docs/BUILDING.md)
- [Eden4 known issues](https://github.com/xatyy/Eden4/blob/main/docs/KNOWN_ISSUES.md)
- [ps4-switch-emu README](https://github.com/ps4-switch-emu/ps4-switch-emu/blob/main/README.md)

## Proximos marcos verificaveis

1. Preservar a R06 e obter o primeiro erro real do `libcxx18` na nova execucao CircleCI.
2. Obter codigo Eden4 no commit fixado
   `fab246cbac93c7995aaf451dca83ae93ba0bd234` usando
   `bash ci/prepare-eden4-base.sh`. A operacao **apenas prepara o codigo**,
   nao cria PKG nem altera R06.
3. Preparar job independente, com a toolchain LLVM 21 e PacBrew prevista no Eden4,
   antes de adaptar o launcher; testar requisitos e limitacoes do executor CI.
4. Gerar um ELF e PKG experimentais apenas quando a compilacao estiver realmente verde.
5. Testar no PS4 Pro **em modo base para Eden4**; medir boot, tela, controles, audio,
   menu de retorno, crashes e FPS. Nao ligar modo GPU Pro do Eden4 sem suporte.
6. So apos resultados reais integrar as funcoes necessarias na versao HIMURA e
   trocar branding/identificador de pacote sem sobrescrever instalacoes existentes.
7. Rodar homebrew/testes de GPU/controle/audio antes de jogos comerciais,
   depois jogos leves. Desempenho de 30 fps e uma meta, nao uma garantia.

## Regras de integracao e distribuicao

Eden/Orbis Eden/Eden4/ps4-switch-emu usam GPLv3 (ou posterior), com outros
componentes que mantem as proprias licencas e creditos. Preservar avisos e
disponibilizar o codigo-fonte correspondente ao distribuir uma versao modificada.
Nao incluir chaves, firmware, jogos ou arquivos proprietarios no PKG.

**Status R07:** fonte e estrategia selecionadas; branch experimental e script
de checkout preparados. Nenhum novo PKG compilado ou testado a partir da R07.
