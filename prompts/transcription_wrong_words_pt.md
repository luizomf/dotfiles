<instructions>
Você está recebendo uma transcrição automática de um vídeo em PT-BR (português
do brasil).

O tema é Claude Code e Remote Control rodando em um servidor VPS da Hostinger. O
tutorial é técnico e apresenta comandos. Tais comandos são complicados para o
Whisper transcrever.

A transcrição costuma falhar exatamente nos termos mais técnicos, comandos,
marcas, palavras estrangeiras, sinais como "--" (menos menos), "++" (mais mais)
e outros.

Seu trabalho é fazer o seu melhor para detectar palavras que possam estar
erradas. Alguns erros são muito visíveis, outros muito sutis. Você precisará
compreender o contexto geral da transcrição para concluir a tarefa.

Retorne no seguinte formato, uma correção por linha:

"Termo incorreto exato" -> "Termo correto" | probabilidade

Onde probabilidade deve ser apenas uma destas palavras: baixa, média, alta

Exemplo de erros comuns do Whisper:

- "git bear" -> "git bare" | alta
- "get bar" -> "git bare" | média
- "gite shell" -> "git-shell" | alta
- "menos menos ber" -> "--bare" | média
- "cloud" -> "Claude" | média
- "rough" -> "ruff" | alta
- "hosting" -> "hostinger" | alta
- "Te max" -> "tmux" | alta

Este vídeo pode conter os erros abaixo:

- "Claudio" -> "Claude" | alta
- "Temux" -> "tmux" | alta
- "Cloud Code" -> "Claude Code" | alta
- "Cloud" -> "Claude" | alta
- "barra Remote Control" -> "/remote-control" | alta
- "Remote Control" -> "--remote-control" | alta
- "OpenCLO" -> "OpenClaw" | média
- "LearnMux" -> "learn-tmux" | média
- "LearnTMUX" -> "learn-tmux" | média
- "search mais manager" -> "search and manager" | média
- "clipe" -> "cli" | média
- "TMUX LS" -> "tmux ls" | alta
- "TMUX" -> "tmux" | alta
- "Tmux" -> "tmux" | alta
- "INSTALTEMUX" -> "install tmux" | alta
- "Cláudio" -> "Claude" | alta
- "comando remoto do Cloud" -> "comando remote-control do Claude" | média
- "testando traço VPS" -> "testando-vps" | média
- "Cloud Clicks" -> "Claude CLI" | média
- "Traffic" -> "Traefik" | alta
- "clipe" -> "cli" | alta
- "CTRL B, D de dado" -> "Ctrl+B, D" | média
- "barra rename" -> "/rename" | alta
- "extra alto" -> "extra-high" | alta
- "3DS" -> "Three.js" | alta
- "Remote Control Multithread" -> "remote-control multithread" | média
- "VIE" -> "VPS" | média

Este é um script automatizado, portanto siga as regras abaixo.

Regras:

- Não incluir notas, cumprimentos, perguntas ou explicações.
- Não inclua markdown (texto puro apenas).
- Não liste termos já corretos.
- Não inclua correções gramaticais comuns.
- Se não encontrar erros prováveis, retorne apenas: NENHUM_ERRO_PROVAVEL

O texto está envelopado entre `<content>` e `</content>` e virá a seguir:

Use sua capacidade máxima de raciocínio para pensar bem antes de concluir. Assim
evitamos retrabalho.  
</instructions>
