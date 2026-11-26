# HIMURA SWITCH PS4 R13 — testes reais do usuário (26/11/2026)

## Ambiente
- PS4 Pro desbloqueado com GoldHEN.
- Emulador HIMURA SWITCH PS4 R13 instalado para teste.
- Este relatório registra sintomas relatados e observáveis; ainda não estabelece causa-raiz.

## Casos observados
| Jogo | Resultado | Confirmação |
| --- | --- | --- |
| Hollow Knight: Silksong | Menu e introdução aparecem. Na transição para gameplay: tela preta, ~0 FPS por longo período; depois o aplicativo fecha. | Relato direto do testador. |
| BMX City Run | Fica em "Loading" por pelo menos 36 s no vídeo; não chegou a abrir mesmo após gravação. | Vídeo e confirmação posterior do testador. |
| Mario Kart 8 Deluxe | Permanece na tela de título com o nome do jogo sem seguir para os menus ou corridas. | Relato direto do testador. |
| Terceira gravação 20261126_123041.mp4 | Aproximadamente 31,55 s, TV sem gameplay visível; indicador FPS 0,0 em diversos momentos. | Revisão de frames do vídeo. Jogo exato não identificável na gravação. |

## Hipóteses a verificar, NÃO correções confirmadas
1. Guest CPU/JIT ou um serviço do sistema esperando permanentemente numa fase de boot.
2. Renderização/VideoOut ou fila Vulkan travada após troca de cena.
3. Erro no carregamento de recursos, jogo/update/DLC/firmware ou configurações.
4. Pressão de memória direta do PS4 Pro durante compilação de shaders ou transição para gameplay.
5. Referências úteis: Orbis Eden usa outra revisão do núcleo do Eden e documenta Mario Kart 8 Deluxe chegando às corridas com ~13–16 FPS, porém ainda com demora de carregamento e uso alto de RAM; essas métricas não são comparáveis diretamente à nossa R13. Código-fonte: https://github.com/MrKitsune9/Orbis-EDEN

## Diagnóstico requerido antes de alterar núcleo
- Reproduzir em apenas um jogo por vez e exportar logs via opção do emulador.
- Arquivos úteis: `/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt`, `eden.log`, `crash.log`, `samples.log`, `boot-trace.log`.
- Não compartilhar arquivos de chaves `prod.keys` ou `title.keys`.
- Comparar contadores a cada 10 s: `quadros_compostos`, `video`, `audio`, `memoria_extra_mib`.
- Se composições avançam mas VideoOut não, investigar apresentação. Se tudo estaciona, investigar guest CPU, deadlock, erro/timeout de serviço ou carregamento.
- Confirmar em qual commit e PKG o problema foi reproduzido e registrar versão do jogo, atualizações e se NSP ou XCI.
- Comparar a solução com código upstream pontualmente; evitar substituição em bloco sem testes.

## Estado das correções
- A correção dos controles fictícios no papel de parede foi **preparada** na branch `himura-switch-r13-user-tests-staging` e **ainda não comprovada em PKG**.
- Uma adaptação Mii para alguns jogos, inclusive Mario Kart, existe em outra ramificação `himura-switch-r13-mii-compat-staging`; **não comprova solução da tela de título**, que ocorre antes da seleção Mii.
- Nenhuma correção dos congelamentos foi comprovada ainda em execução real no console.
