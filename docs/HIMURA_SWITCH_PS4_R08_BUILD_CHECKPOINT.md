# HIMURA SWITCH PS4 — R08: primeiro PKG experimental

## Objetivo verificável

Compilar a base Eden4 fixada no commit `fab246cbac93c7995aaf451dca83ae93ba0bd234` como um aplicativo experimental para PS4, usando **somente CircleCI**, sem alterar R06, R07, main ou qualquer projeto PS2.

- Branch exclusiva: `himura-switch-r08-pkg`.
- Identificador PS4 independente: `HIMU00008` (não substituir EDEN00002).
- Pacote esperado **apenas se a cadeia completa passar**: `switch-r08-pkgs/HIMURA_SWITCH_PS4_R08_EXPERIMENTAL.pkg`.
- Relatórios por etapa em `switch-r08-reports/`, incluindo `ERRO-PRINCIPAL.txt` em caso de falha, manifest e SHA-256.
- Todos os avisos de licença da base original devem acompanhar o pacote; a área de créditos da R07 é aplicada à cópia de trabalho.
- O arquivo PKG não é um resultado da CI do menu R07; depende de LLVM21, OpenOrbis/PacBrew, libc++, Mesa/RADV, Eden e ferramenta de empacotamento.
- A licença e o código correspondente devem ser disponibilizados de acordo com as licenças dos componentes incorporados.

## Critérios de aceite

1. CircleCI mostra `compilar_eden4_pkg_r08` concluído com sucesso e arquivos não vazios.
2. O empacotador valida o PKG; o `eboot.bin` e o `.oelf` são produzidos.
3. Conferir hashes e baixar o PKG **experimental**. Esse sucesso não confirma que abre no PS4.
4. Teste real no PS4 Pro: instalação, boot, tela inicial, créditos, controles, saída segura, homebrew livre, e apenas depois jogos próprios legalmente obtidos.
5. Registrar FPS, crash/logs e qualidade gráfica para comparar desempenho real.

## Limitações técnicas ainda abertas

- O modo PS4 Pro completo do RADV do Eden4 tem histórico de travamento; manter `EDEN_SFO_ATTRIBUTE=0` até validação em hardware.
- O pipeline de R08 exige ubuntu 26.04 x86-64, clang/LLVM21, ferramentas PacBrew e pode levar horas na primeira execução. Limites de créditos e tempo do CircleCI podem interromper a compilação.
- O CI não tem acesso ao PS4 do usuário; compatibilidade de jogos e desempenho ainda não são comprovados.
- Não incluir chaves, firmware, dumps comerciais ou módulos proprietários em arquivos públicos.
