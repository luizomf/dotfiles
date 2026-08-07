# dotfiles

Fiz os testes no Ubuntu 24.04 e no macOS Sequoia (ambos ARM). Todos os testes
foram feitos com uma instalação limpa dos sistemas operacionais.

Não detectei erros até o momento.

Mesmo assim, recomendo que você abra o arquivo `install.sh` e execute os
comandos linha a linha observando o que cada linha vai fazer. Se você executar
esse script no seu sistema, ele vai rodar direto e não para mais, então ele
sairá sobrescrevendo, apagando, criando e instalando tudo de uma vez (pra mim é
mais fácil assim).

Se mesmo com o aviso ainda quer rodar, faça isso com o git instalado:

```bash
git clone git@github.com:luizomf/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

**⚠️ Vai sobrescrever teus arquivos. Tamo junto.**

## Pi Coding Agent

The installer links the static configuration under `pi/agent/` into
`~/.pi/agent/` with relative targets that assume this repository is cloned at
`~/dotfiles`. Credentials, sessions, trust decisions, generated model state,
and machine-specific model configuration remain local.

Skills and extensions are maintained separately in
[omskills](https://github.com/luizomf/omskills) and
[ompi](https://github.com/luizomf/ompi).

---

Feito com ódio, café e um toque de amor.

---
