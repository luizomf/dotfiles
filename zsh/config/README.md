# .zsh - Configuração ZSH modular por @luizomf

Este repositório contém meu setup completo de ZSH, totalmente modularizado.
Criei esse esquema anos atrás e, honestamente, fiquei surpreso comigo mesmo quando redescobri, então agora está de volta, repaginado e funcional.

---

## Como usar

Adicione isso ao seu `~/.zshrc`:

```zsh
source "${HOME}/.zsh/use_this_to_load"
```

Isso vai carregar automaticamente todos os arquivos da pasta `.zsh`.

---

## 📁 Estrutura dos arquivos

- `aliases`: comandos úteis para Git, Docker, pip, macOS cleanup, ffmpeg e mais
- `config`: otimizações de histórico e comportamento do ZSH
- `exports`: variáveis de ambiente e PATH (pyenv, nvm, openssl, etc)
- `functions`: funções personalizadas (como `componentTs`, `aula_c`, `addtocspell`, etc)
- `keybinds`: binds extras, como opção+seta para navegar palavras
- `use_this_to_load`: script que orquestra o carregamento modular com verificação de arquivos

---

## Curiosidade

Esse setup nasceu por necessidade e preguiça de usar frameworks gigantes como Oh My Zsh ou Prezto.
Hoje em dia, virou um pequeno legado pessoal. Modular, limpo e fácil de versionar.

Se você quiser um setup leve, personalizável e fácil de entender: use isso como base.
Se quebrar tudo, a culpa é sua. Se funcionar lindamente, fui eu que fiz 😎

---

## Restauração com Brewfile (macOS)

Se um dia eu cismar de formatar meu Mac (o que não acontece há uns 5 anos), esse repositório serve como base para restaurar todo o ambiente de desenvolvimento com Homebrew.

### Passo a passo (para eu mesmo)

1. Instale o Homebrew (caso tenha perdido até isso):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Clone este repositório de dotfiles:

```bash
git clone https://github.com/luizomf/.zsh.git ~/.zsh
```

3. Rode o comando de restauração com o Brewfile:

```bash
brew bundle --file=~/.zsh/Brewfile
```

Isso vai instalar:

- Fórmulas (`brew`) como `pyenv`, `ffmpeg`, `htop`, `tree`, etc.
- Casks (`apps`) como `sublime-text`, `insomnia`, `losslesscut`, etc.
- Fontes e extensões do VS Code (sim, até isso tá salvo)

4. Recarregue o `.zshrc`:

```bash
source ~/.zshrc
```

### Atualizar Brewfile

Se instalar pacotes novos e quiser atualizar o backup:

```bash
brew bundle dump --file=~/.zsh/Brewfile --describe --force
```

---

## License

MIT (só me dá um star se curtir).

👨‍🚀 Criado por Luiz Otávio Miranda — [@luizomf](https://github.com/luizomf)
