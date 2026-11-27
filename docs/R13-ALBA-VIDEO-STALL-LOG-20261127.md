# Checkpoint factual — R13: travamento de vídeo em Alba (27/11/2026)

## Origem
Arquivo de diagnóstico fornecido pelo proprietário: `HIMURA_R13_GAME_STATUS.txt` (24 linhas presentes; não publicar aqui o caminho completo do NSP nem a origem de aquisição). Este checkpoint **não é log do Silksong**.

## O que o arquivo comprova
- A R13 inicia a execução de **Alba: A Wildlife Adventure**.
- Os checkpoints `guest system initialized`, `container load returned`, `GPU start returned`, `guest CPU ready` e `guest emulation running` estão presentes.
- Nos 5 primeiros registros periódicos (cadência declarada no log de 10 s), `quadros_compostos=0` e `video=0`; `audio` passa de 0 para 2660. No estágio seguinte aparecem `first guest frame reached renderer` e `first game frame submitted to TV`.
- Contadores de `quadros_compostos` e `video` atingem 53, em seguida 186, **permanecem em 186 por cinco registros consecutivos** enquanto `audio` cresce de 4551 para 9245. No último registro aparecem 187 quadros, `audio=10185`.
- `memoria_extra_mib` cresce de 0 a 248 MiB. Esse contador isolado **não comprova OOM**; tampouco os contadores comprovam que o usuário ouviu áudio corretamente.
- O arquivo termina sem `caught launch exception`, sem `emulation shutdown complete` e **sem exceção do PS4, stack trace ou código de erro**. Isso é compatível com travamento/fechamento abrupto, mas **não estabelece a causa**.

## Interpretação operacional
Há evidência **forte de estagnação no caminho de vídeo/apresentação** após alguns quadros com a emulação ou rotina de áudio continuando por vários checkpoints. Possíveis explicações incluem GPU Vulkan, fila de apresentação, espera por sincronização, CPU convidada bloqueada ou falha de estado do jogo; nenhuma delas está estabelecida apenas por esse arquivo.

## Próxima prova
1. Reproduzir a falha especificamente no **Hollow Knight: Silksong** na mesma versão R13. O arquivo `HIMURA_R13_GAME_STATUS.txt` é reiniciado no início de cada `RunGame`; exportar **imediatamente após o Silksong fechar**, antes de iniciar qualquer outro jogo.
2. Enviar também `eden.log` e `crash.log` da mesma execução, se existirem. Exportação via Arquivos de jogos > Triângulo para USB ou copiar de `/data/EdenPS4/` via FTP/PS4 Explorer 2.0.
3. Priorizar no código instrumentação persistente por fase: `GPU start`, primeiro quadro, fila Vulkan/present, último flip, memória, callbacks de memória e exceção. Comparar com New Eden 04.89 sem tocar no PKG original.
4. Se os contadores de vídeo pararem novamente após o vídeo introdutório, investigar especificamente a transição de cutscene para gameplay. **Não afirmar correção sem gameplay testado no PS4**.

## Estado CircleCI (última consulta)
- `95a8639` (revisão integrada anterior): preflight aprovado; compilação PKG ainda pendente.
- `d753cce` (ramificação de diagnóstico pós-Silksong): preflight falhou; **não liberar PKG dessa ramificação** até corrigir.
