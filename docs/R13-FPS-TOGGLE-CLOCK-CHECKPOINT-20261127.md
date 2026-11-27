# HIMURA SWITCH R13 — FPS opcional e relógio removido (27/11/2026)

**Estado:** código commitado em branch isolada, pré-validação automatizada habilitada. Não há PKG nem teste de hardware confirmados.

## Mudanças no código de verdade
- Script `ci/patch-r13-fps-toggle-no-clock.py`, aplicado **depois** da tradução PT-BR.
- Opção na categoria **Vídeo → Mostrar FPS** com **Ligado / Desligado**; padrão Ligado para não mudar o comportamento de builds anteriores.
- Valor salvo junto das opções reais em `/data/EdenPS4/ps4.ini` (`fps_overlay=on` ou `fps_overlay=off`), carregado na inicialização e aplicado a `Common::PS4Diagnostics::r13_fps_overlay_enabled` via `ApplyOptions`.
- O desenho do FPS em `vk_present_manager.cpp` só ocorre quando a opção estiver ligada. Quando desligada, a sobreposição não é copiada para a imagem do jogo. A medição existente de FPS e logs continua disponível para diagnóstico.
- **Relógio/hora removido somente do HOME**: linha `canvas.Text(host.Clock(), 1840, 220, 30, p.text, Align::Right);` eliminada do launcher gerado. Não confundir com FPS.
- A configuração é feita no menu e passa a valer para o próximo jogo executado; isto não cria um menu sobreposto dentro do gameplay.

## Controles para não incluir botão falso
- `ci/r11-preflight.sh` verifica entrada, gravação e carregamento de configuração, ligação com a flag atômica de GPU, função real de desenho de FPS preservada e ausência de `host.Clock()` desenhado.
- `.circleci/config.yml` inclui a branch no fluxo **preflight somente**, sem liberar compilação PKG antes da integração com os outros pedidos (firmware ZIP, correção de crash, visual).
- Esta alteração **não resolve** a inicialização de Arceus ou Silksong, nem instala firmware ou updates. Estes continuam como etapas independentes.

**Regra:** jamais declarar funcional no PS4 Pro sem passar preflight, compilar, instalar e observar o toggle em Ligado/Desligado. Manter a R13 atual e o New Eden 04.89 intactos.
