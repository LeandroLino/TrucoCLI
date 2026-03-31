# 🎮 Sistema de Lobby

## Como Funciona

1. **4 jogadores conectam** ao servidor
2. **Escolhem times** (A ou B) livremente
3. **Marcam "pronto"** quando decidirem
4. **Jogo inicia** quando 4 estiverem prontos em times 2x2

## Comandos

- `A` - Entrar no Time A (🔵)
- `B` - Entrar no Time B (🔴)
- `S` - Sair do time atual
- `R` - Marcar como pronto

## Exemplo de Uso

```
Sala: #AB42

TIME A (🔵) [1/2]        TIME B (🔴) [2/2]
[ ] João                 [✓] Pedro
[ ] Aguardando...        [✓] Lucas

Aguardando escolha de time:
  • Maria

Comandos:
  [A] - Entrar no Time A
  [B] - Entrar no Time B
  [S] - Sair do time atual
  [R] - Marcar como Pronto
```

## Trocar de Time

Se os times estão cheios (2x2):

1. Digite `S` para sair do seu time
2. Aguarde alguém do outro time sair
3. Digite `A` ou `B` para entrar

## Regras

- Máximo 2 jogadores por time
- Precisa estar em um time para marcar pronto
- Ao sair do time, perde status de "pronto"
- Jogo só inicia com 4 jogadores prontos (2x2)
