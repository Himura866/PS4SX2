# HIMURA SWITCH PS4 R14 — migração do núcleo (26/11/2026)

## Decisão de arquitetura
A R13 usa Eden4 fab246cbac93c7995aaf451dca83ae93ba0bd234. Nos testes do proprietário:
- Silksong: entra no menu, passa pela introdução, congela a ~0 FPS e depois fecha na transição para o gameplay.
- BMX City Run: permanece em Loading e não inicia.
- Mario Kart 8 Deluxe: permanece na tela de título.

A R14 usa o Orbis Eden inteiro como nova base, em vez de copiar patches incompatíveis:
- Upstream: https://github.com/MrKitsune9/Orbis-EDEN (GPL-3.0)
- Commit PS4: f004df1c7a812cc65703d8f937d0bd12a6d06a58 (v1.01, 25/11/2026).
- Núcleo Eden: 5f142c7926d0c7fcbbd0ce30794d72f638a43b2a.
- Patches PS4: série patches/eden (CPU, memória, GPU, inicialização e compatibilidade).

Ainda não foi comprovado que este Orbis Eden seja o mesmo "New Eden 0.4.89" dos vídeos.

## Integração versionada na branch R14
- ci/r14/prepare-orbis-r14.sh: obtém o Orbis Eden no commit fixado e aplica as personalizações da R14 num diretório isolado, falhando se o destino já existe.
- ci/r14/patch-frontend.py: adapta frontend/menu/rom_menu.cpp para biblioteca com até dez cartões reais de jogos por página; setas movimentam foco, X inicia, Triângulo altera idioma. Português é o padrão inicial, mas idiomas salvos permanecem válidos.
- ci/r14/build-branding.py: reutiliza as artes samurai originais verificadas por SHA-256 pela rotina já existente da R13 e converte a imagem limpa para BGRA 1920x1080. O rodapé fictício foi removido no processo de arte anterior. O novo desenho do menu cobre as setas fictícias, indicadores e o selo R13 que ainda constam na imagem.
- package-eden.sh (no checkout descartável): Title ID HIMU00014, versão 01.14, imagem de fundo empacotada e ícone samurai aprovado.
- frontend/ps4_platform.h (no checkout descartável): diretório /data/himura_switch_r14, isolado do Orbis Eden original e da R13.
- ci/r14/preflight.sh: verifica os scripts, a arte, a navegação, o pacote e garante que o núcleo CPU/JIT/Vulkan/memória original não foi alterado pelo tema.
- .circleci/config.yml: job de validação de fonte e arte exclusivo da nova ramificação R14; não gera PKG.

Os cartões da interface exibem nomes de jogos reconhecidos pelo Orbis Eden. As capas dinâmicas, telas secundárias antigas da R13 e o contador de FPS sobre o gameplay AINDA NÃO FORAM PORTADOS. O Orbis Eden mantém seus próprios logs de FPS e memória.

## Evidências e limites
- Orbis Eden documenta Mario Kart 8 Deluxe em corridas a cerca de 13–16 FPS e menus a 40–60 FPS em testes anteriores. Não equivale a 60 FPS em corrida.
- Ainda NÃO há compilação completa da R14, PKG instalável validado, ou teste dela no PS4 Pro.
- O build original Orbis Eden usa LLVM18/OpenOrbis/Mesa com caminhos e scripts Windows/Git Bash. A cadeia Ubuntu/LLVM21/Eden4 da R13 não é compatível por simples substituição de pasta; precisa de adaptação e teste independente.
- Ainda não há evidência de gameplay do Silksong ou BMX City Run nesta nova base.
- R14 usa pasta de dados separada: quem testar deverá colocar ali, por conta própria, seus arquivos permitidos. Nunca adicionar jogos, keys, firmware, saves ou arquivos proprietários ao repositório.

## Próximas portas
1. Preflight R14 no CI: fonte do Orbis fixada, aplicação de patches e arte, sem SDK.
2. Toolchain: adaptar/validar compilação ELF e empacotamento PS4 no ambiente disponível.
3. PS4 Pro: instalar o PKG apenas após gerar e validar; verificar menu, controles, arte e jogo selecionado.
4. Compatibilidade: Mario Kart, Silksong e BMX com boot.log, mesa.log, uso de memória, tempos até os primeiros quadros e FPS real de gameplay.
5. Depois: acrescentar carregamento de capas, demais telas e FPS na tela, preservando estabilidade.

R13, PS4SX2 PS2 e outras ramificações não são alteradas nesta migração.
