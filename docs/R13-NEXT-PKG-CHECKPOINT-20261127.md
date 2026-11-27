# CHECKPOINT — HIMURA SWITCH R13 / próximo PKG experimental (27/11/2026)

**Branch isolada:** `himura-switch-r13-next-pkg-integration-20261127`, baseada em `himura-switch-r13-functional-settings-20261127`. **Não modificar main nem o New Eden 04.89 original.** Esta nota é um checkpoint de fonte, NÃO um PKG homologado, e não comprova que jogos iniciem no PS4 Pro.

## Mudanças de código preparadas nesta revisão

- **Relógio removido** do HOME, independente do contador de FPS.
- **FPS ligável/desligável de verdade** em Configurações > Vídeo > Mostrar FPS. Usa a configuração real em `/data/EdenPS4/ps4.ini`; a sobreposição Vulkan obedece à chave. Passou preflight na branch-base.
- **USB 0 a USB 7:** verifica montagem real; detecta transição de conexão/desconexão a cada 3 segundos para reindexar arquivos sem copiar jogos e sem acessar symlink recursivamente. O navegador de pastas com DualShock já existia na R13 de base.
- **Firmware ZIP:** arquivo `ci/r13_firmware_zip.cpp` + header e `ci/patch-r13-firmware-zip.py`; menu Arquivos de jogos > Instalar firmware ZIP > USB/interno > escolher ZIP. Módulo nativo Zlib extrai NCAs compactados (stored/deflate), verifica tamanho e CRC32, rejeita ZIPs inseguros/ZIP64, monta staging e transfere arquivos novos à NAND sem sobrescrever saves, keys, firmware anterior, updates ou DLC. O importador executa em thread e exibe NCAs verificados; antes de iniciar jogo `PsHost::End` aguarda conclusão. A cópia só é tratada como concluída depois das verificações. **Versão interna real do firmware ainda não verificada no console.**
- **Biblioteca:** `ci/patch-r13-game-library-cleanup.py` não mostra NSPs marcados explicitamente como update/DLC ou cujo nome contém identificador de update; **não instala updates nem garante detectar todos pelo conteúdo NCA**. Os arquivos continuam no HD sem alterações.
- **Menu:** gera PNG derivado do mesmo WebP aprovado (SHA256 da arte original verificado no build); retira elementos estáticos impressos das amostras de capas, botões falsos, badge R11/R13 e prolonga cores da paisagem até y=1080; remove máscaras pretas do launcher e deixa capas/neon e dicas do controle como widgets funcionais. Conferir renderização real na TV para artefatos de interpolação; não chamar esta versão de arte homologada antes de vídeo do console.

## Resultados confirmados

- **Firmware ZIP — PASSOU** no CircleCI, teste `validar_r13_zip_firmware`, pipeline de commit `2b06700062b2f0efd74f17eb51d109e3f1fe062f`. Verificou NCAs *fictícios de teste*: CRC, ZIP malicioso, ZIP armazenado/deflate, rejeição de sobrescrita e diretórios no arquivo.
- **FPS ligado/desligado — PASSOU** preflight da branch funcional em commit `bd95ca6e37d27c24a25d31e359fc0a3c4a8b5b66`.
- **Preflight R13 integrado — FALHOU** em commits anteriores. Para localização do erro, CI agora separa `validar_r13_sintaxe`, `validar_r13_base_aplicacao`, `validar_r13_firmware_aplicacao`, `validar_r13_aplicacao_patches` e `validar_r11_antes_do_pkg`; nenhum resultado pode ser considerado sucesso antes do status verde.
- **Compilação PKG e gameplay:** ainda NÃO executadas/verificadas para a revisão integrada. Não confundir teste de extração ZIP com teste de PKG.

## Pendências que NÃO devem ser apresentadas como prontas

1. **Pokémon Legends: Arceus:** crash CE-34878-0 relatado antes da escolha do idioma na R13 atual; requer log `HIMURA_R13_GAME_STATUS.txt`, `eden.log` e comparação A/B com a R13 anterior e New Eden 04.89.
2. **Hollow Knight: Silksong e demais jogos:** carregamento longo, tela parada/erro, ainda não corrigidos; otimizações RADV/JIT e memória precisam de testes reais.
3. **Barra de carregamento horizontal com avanço REAL:** o boot atual gera imagem uma vez e a entrega ao swapchain em `loading_picture`. Uma simples barra estática seria falsa; é necessário instrumentar fases reais e atualizar exibição sem duas threads concorrerem pelo VideoOut. NÃO incluída nesta revisão.
4. **Instalador de updates/DLC com leitura do conteúdo:** filtro atual não é instalação; falta mecanismo seguro de importar updates para a NAND e associá-los ao título.
5. **Firmware real ZIP no PS4 Pro:** é obrigatório testar montagem, permissões de escrita, conteúdo NCA correto e detecção pelo núcleo.
6. **Arte:** obter captura 1080p após build, verificar remoção de símbolos estáticos, contraste do rodapé, capas limpas e desempenho da UI.

## Regras de segurança/entrega

- Não embutir firmware, keys, jogos, save data, DLCs ou títulos protegidos no GitHub/PKG.
- Manter `HIMU00011` / `01.13` como pacote experimental **apenas depois de pré-validação**; avisar que a instalação pode substituir a R13 existente pelo mesmo Title ID. Preservar o New Eden original.
- Somente CircleCI (nunca GitHub Actions). Não afirmar que PKG está pronto antes de build, checksum, artefato e teste de console.
- Prazo de compilação abaixo de 50 minutos é META, não promessa; usar cache de dependências sem mascarar falhas.
- Próximo checkpoint: resolver pré-validação integrada, compilar no CircleCI e confrontar Arceus/Silksong com New Eden.
