# V15 — bloqueio de pacote inseguro e validação antes de compilar

## Estado confirmado (26/11/2026)

- Arquivo de origem do usuário: `NewEden-04.89.pkg`, **SHA-256 `06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd`**, tamanho **69.337.088 bytes**, `TITLE_ID=EDNP00001`.
- Executável extraído **exatamente desse jogo instalado**: `eboot.bin`, **SHA-256 `5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381`**, tamanho **78.376.440 bytes**.
- Cópia experimental de tradução V15 (15 rótulos, **131 bytes modificados somente em regiões de texto**): SHA-256 `bab383c0271c2a7a3efa119c5e25b73459ad06d79c848f7d1c147e288e45bb6b`.
- Verificação local de SHA-256, tamanho, cabeçalho PS4 ELF/PKG, modificações fora de slots, não sobrescrever original, entrada errada e saída ausente. **Quatro testes negativos/de políticas aprovados, e validação positiva do executável real.**
- Pacote de scripts, testes e relatórios **no Drive privado**: [HIMURA_NEWEDEN_V15_ETAPA03_SAFETY_TESTS.zip](https://drive.google.com/file/d/1uMkYTibff3JTRoqGetbjmXt07-liYc61/view).
- Plano de compatibilidade [HIMURA_NEWEDEN_V15_PLANO_COMPATIBILIDADE_PS4_PRO.md](https://docs.google.com/document/d/1tzZ-c7YnWwtYcFGdFyvQQCU24SGyEm-q/edit).

## REGRA PARA EVITAR ERROS E PACOTES CORROMPIDOS

1. **Não iniciar novos builds longos do CircleCI** até existir fonte reproduzível ou processo de repack comprovado para a **mesma** revisão 04.89. O projeto Orbis-EDEN usado noutra branch não é equivalente ao PKG do usuário.
2. A verificação rápida do script e hashes deve rejeitar versões incompletas/misturadas, qualquer alteração fora dos bytes autorizados e qualquer tentativa de sobrescrever a única cópia.
3. Antes de um PKG de teste, conferir `eboot.bin`, `sce_sys/param.sfo`, `sce_sys/icon0.png`, integridade de arquivos e estrutura do pacote, IDs e versões coerentes, licenças e relatórios.
4. **Não alterar código de inicialização de jogos/JIT/CPU/Vulkan, áudio, memória, chaves, saves**, nem fazer port de otimizações Android/ARM diretamente para PS4 AMD/x86-64 sem adaptação e testes.
5. Otimizações candidatas (já oferecidas em alguma forma pelo executável): cache de shader, shaders assíncronos, GPU precision, CPU, resolução, frame pacing, FPS real, NSP/XCI/firmware e perfis por jogo. **Não afirmar suporte pleno/ganho de FPS sem teste real**.
6. Matriz de regressão no PS4 Pro: Silksong (abre, relato do usuário), Mario Kart 8 Deluxe (problemas), título de bicicleta (falha), outro título (falha). Registrar passo de boot, erro, FPS medido, áudio, save, retorno/saída e indicadores. Sem testes hardware, manter `NÃO TESTADO`.
7. Menus internos PT-BR, V15 em Sobre + créditos, controles reais no topo, News e Temas removidos funcionalmente, carrossel sem painel preto, capa externa e fundo interno separados; essas alterações **ainda não estão implementadas por completo** neste executável.
8. Guardar cada checkpoint e resultado em `HIMURA SWITCH PS4 - CHECKPOINTS E BACKUPS`, sem apagar os anteriores.

## Status de liberação

**BLOQUEADO PARA INSTALAÇÃO.** Não existe PKG V15 compilado/testado. A cópia binária experimental de tradução é **NÃO-INSTALAR**. A validação de bytes não substitui testes no PS4.

**Observação sobre o CircleCI:** as verificações desta etapa rodaram localmente; **nenhum job CircleCI foi disparado por este documento**. Alterar pipelines só após revisão de sintaxe/YAML para evitar outro erro de configuração.
