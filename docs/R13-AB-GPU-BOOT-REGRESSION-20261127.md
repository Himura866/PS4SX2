# HIMURA SWITCH R13 — teste A/B do crash de inicialização (27/11/2026)

## Objetivo
Isolar a regressão relatada no Pokémon Legends: Arceus: a R13 Experimental atual fecha com CE-34878-0 antes da tela de idioma; uma revisão anterior avançava até a seleção de idioma. O mesmo projeto tem travamentos no Silksong. **Não presumir que a causa é RADV, o código de erro sozinho não identifica a origem.**

## Alteração executada
- Branch experimental isolada: `himura-switch-r13-ab-gpu-baseline-20261127`, derivada de `himura-switch-r13-ptbr-usb-20261127`.
- Mantidos: base Eden4 fixa, todos os patches de estabilidade/diagnóstico, launcher, USB e PT-BR, configurações existentes, registro `HIMURA_R13_GAME_STATUS.txt`.
- **Única alteração funcional do motor nesta ramificação:** não aplicar `ci/patch-r13-ps4-radv-safe-path.py` na geração do PKG, para comparar contra a versão com proteção do comando de draw indireto e remoção de extensões Vulkan.
- Preflight alterado para verificar que **o caminho experimental não aparece** no código gerado; teste unitário do patch RADV permanece independente.
- CI desta branch habilitada para preflight e build, sem promover um PKG como release ou sobrescrever instalação original.

## Validação e limites
Preflight automático e compilação não equivalem a teste no PS4 Pro. Usar mesmo jogo, mesma cópia, mesmo modo de console, mesmas keys/firmware, e idealmente mesmo cache desativado nas duas versões. Recolher versão exata e hash dos PKGs para não misturar a R13 baixada pelo usuário com branches que ainda não foram instaladas.

Comparações mínimas:
1. **Arceus**: tempo da seleção do jogo até `container load returned`, `GPU start returned`, primeiro frame, seleção de idioma e gameplay. Capturar `HIMURA_R13_GAME_STATUS.txt`, `eden.log`, `crash.log` se ocorrer erro.
2. **Silksong**: ultrapassa vídeo de abertura? fechamento ao apertar X ou mesmo sem apertar? FPS e áudio se entrar no jogo.
3. **New Eden 04.89 original**: referência externa sem editar seu motor, comparar tempos e até onde cada jogo vai.
4. Se a variante A/B piorar, manter RADV safe-path; se melhorar, localizar incompatibilidade e testar patch mínimo corrigido em branch separada. Não substituir uma correção por superstição.

## Pedidos do usuário mantidos em fila (não incluídos nesta comparação controlada)
- Importação real de firmware ZIP: seleção de arquivo em USB/interno, extração segura sem traversal e com limites, validação de arquivos NCA/estrutura, estágio temporário e rollback, instalação atômica e reinicialização/consulta da versão, sem sobrescrever keys/saves.
- Updates/DLCs devem ir à NAND e ficar fora do carrossel da biblioteca.
- Configurações com efeito real e persistência, incluindo perfil de jogo/diagnóstico e opções cuja API/driver PS4 seja realmente funcional.
- Fundo original expandido até rodapé, sem faixa opaca nem máscara preta, sem "R13" decorativo; manter botões de verdade, PT-BR, capa com neon e barra de carregamento horizontal verificável.
- Evitar builds de release e testes no console antes de integrar e validar as funções solicitadas. Esta compilação de A/B é somente diagnóstica.

## Estado de entrega
**Código e receita da comparação criados. CI status deve ser consultado antes de afirmar êxito. Nenhum PKG foi verificado como pronto nem executado no PS4 Pro nesta etapa.** Preservar o New Eden e a R13 original.
