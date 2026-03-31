# 📚 Documentação TrucoCLI

## Guias Rápidos

- [🎮 Sistema de Lobby](LOBBY.md) - Como escolher times
- [📖 Regras do Jogo](REGRAS.md) - Truco Paulista completo
- [⚙️ Configuração](CONFIG.md) - Debug, rede, customização

## Início Rápido

```bash
# Instalar
pip install rich

# Servidor
python3 servidor.py

# Cliente (4x)
python3 cliente.py
```

## Comandos

### Lobby
- `A/B` - Escolher time
- `S` - Sair do time  
- `R` - Pronto

### Jogo
- `0/1/2` - Jogar carta
- `T` - Truco
- `S/N/A` - Responder truco
- `V0/V1/V2` - Carta virada

### Especiais
- `/ajuda` - Ajuda
- `/stats` - Estatísticas
- `/sair` - Sair

## Arquivos do Projeto

```
TrucoCLI/
├── servidor.py        # Servidor do jogo
├── cliente.py         # Cliente (jogador)
├── config.py          # Configurações
├── utils.py           # Funções auxiliares
├── stats.py           # Estatísticas
├── debug.py           # Controle de debug
└── docs/              # Esta pasta
    ├── LOBBY.md       # Sistema de lobby
    ├── REGRAS.md      # Regras do jogo
    └── CONFIG.md      # Configuração
```

## Suporte

- Bugs? Abra uma issue no GitHub
- Dúvidas? Veja a documentação acima
- Contribuições? PRs são bem-vindos!
