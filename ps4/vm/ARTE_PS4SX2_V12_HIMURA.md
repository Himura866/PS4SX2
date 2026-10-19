# Arte do PS4SX2 V12 — Pod do Himura

A nova arte usa a identidade azul de PlayStation 2, com PS4SX2 V12 e
**Pod do Himura** (com H).

## Arquivos do pacote de arte

- `icon0.png`: 512x512, imagem quadrada para o ícone do aplicativo no PS4.
- `pic1.png`: 1920x1080, fundo da apresentação do aplicativo.

Os PNGs estão no pacote `PS4SX2_V12_Himura_Capa.zip` fornecido na conversa.
**Ainda precisam ser copiados para o projeto/empacotador**. A integração não
pode ser considerada concluída apenas com este documento.

O PKG deve conter os arquivos finais em:
```
sce_sys/icon0.png
sce_sys/pic1.png
```

O código do menu já carrega `/app0/sce_sys/pic1.png` como imagem de fundo.
A etapa de empacotamento deve substituir as artes antigas por esses arquivos
antes de montar o PKG, sem alterar as configurações de execução ou os saves.

**Verificação obrigatória:** confirmar que os dois arquivos foram incluídos
no PKG, que o PKG foi produzido com sucesso e que o ícone aparece corretamente
no menu do PS4. Não confundir uma alteração de código com um pacote validado.
