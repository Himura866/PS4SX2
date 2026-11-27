# Checkpoint HIMURA SWITCH — Silksong pós-introdução e identidade (27/11/2026)

## Relato confirmado pelo usuário
- Na R13 experimental já instalada, Hollow Knight: Silksong inicia, abre menu, aceita idioma e reproduz vídeo/introdução.
- Na passagem do vídeo para o gameplay, o PS4 Pro fecha o emulador com tela azul (código exato desta tentativa ainda não confirmado).
- Outros jogos leves também fecham, enquanto o New Eden original 04.89 tem resultados melhores.
- A identidade visível do aplicativo, de suas configurações e das pastas no PS4 deverá ser **HIMURA SWITCH**; não mostrar Eden como nome do produto ou das pastas, mas manter créditos legais para bibliotecas de terceiros.

## Contexto técnico
- Transição vídeo -> gameplay pode aumentar demanda de Vulkan/GPU, shaders, RAM, serviços ou CPU emulada. Sintoma sozinho NÃO identifica a falha; **não declarar RADV ou falta de firmware como causa comprovada**.
- A R13 anterior registra checkpoints em `/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt`, `/data/EdenPS4/eden.log` e `crash.log`. O exportador do launcher pode gravar no USB `EdenPS4-HIMURA_R13_GAME_STATUS.txt`, `EdenPS4-eden.log`, `EdenPS4-crash.log` quando disponíveis; alternativa: PS4 Explorer 2.0 para copiar os arquivos de `/data/EdenPS4/`.
- Comparação A/B com a versão mais antiga que abre jogos e com New Eden 04.89, com mesmo NSP/XCI, saves, keys/firmware e configuração de resolução, é necessária para afirmar correção.

## Código desta ramificação
- Origem: `himura-switch-r13-next-pkg-integration-20261127`; mantido integralmente o build ativo `95a863987a93742c069aac751ba9f65f527af67b` sem novos commits.
- Script `ci/patch-r13-gameplay-trace-brand.py`, incluído no final do pipeline de patches.
- Checkpoint de runtime reduzido de 10 s para 2 s, gravando estágio atual de vídeo/CPU e contador de callbacks de memória para localizar o último estado antes do crash; nunca escrever por frame.
- Renomeia a descrição em `SystemInfo` para `Dados do HIMURA SWITCH (legado preservado)` e nomes dos relatórios de USB para `HIMURA-SWITCH-...`.
- **NÃO executa renomeação física do diretório** `/data/EdenPS4` nesta etapa. Esse diretório pode abrigar saves, firmware, keys e arquivos usados por outras versões. Mover, sobrescrever ou desvincular sem inventário e migração segura pode perder os dados e quebrar o New Eden original.
- Política para futuro diretório `/data/HIMURA_SWITCH`: inventariar tamanho, solicitar autorização explícita para migrar dados existentes, copiar de forma verificável sem sobrescrever, testar leitura pelo loader e manter legado intacto até homologação; preservar logs, opções, saves, game cache e diretórios de firmware. Também atualizar definição `PS4_RUNTIME_DATA_DIR` e outros caminhos do código na mesma transição. O nome do produto pode ser alterado agora; textos de atribuição a autores terceiros precisam continuar nos créditos/licenças.

## Estado de testes
- Ainda sem evidência de que este patch diagnóstico resolve crashes. Ele deve somente melhorar o rastreamento e remover marcas de produto nas superfícies selecionadas.
- A pré-validação CircleCI deve passar nesta branch antes de considerar fusão.
- O PKG integrado do commit `95a8639` possui oito validações anteriores aprovadas e compilação separada pendente na última consulta. Não instalar a branch diagnóstica sem compilar e testar.

## Próxima evidência necessária para corrigir gameplay
1. Usuário executar Silksong na R13 que já tem e reproduzir crash.
2. Voltar ao menu da R13, conectar HD/pendrive na USB e pressionar **Triângulo** em **Arquivos de jogos** para exportar logs. Enviar os arquivos se existirem. Caso falhe, copiar com PS4 Explorer 2.0 diretamente de `/data/EdenPS4/`.
3. Comparar `HIMURA_R13_GAME_STATUS.txt`, `eden.log` e `crash.log` com a sequência de vídeo, frames compostos, flips, heap e último estágio. Só então selecionar patch de GPU/CPU ou loader com base concreta.
