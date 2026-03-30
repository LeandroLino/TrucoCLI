"""
Funções utilitárias compartilhadas
"""
from datetime import datetime
from config import DEBUG_MODE

def log(msg, nivel="INFO"):
    """Log com timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{nivel}] {msg}")

def debug_log(msg):
    """Log apenas se DEBUG_MODE estiver ativo"""
    if DEBUG_MODE:
        log(msg, "DEBUG")

def get_time_jogador(jogador_id):
    """Retorna o time (A ou B) baseado no ID do jogador"""
    return "A" if jogador_id % 2 == 0 else "B"

def get_adversarios(time):
    """Retorna lista de IDs dos adversários"""
    from config import TIME_A_JOGADORES, TIME_B_JOGADORES
    return TIME_B_JOGADORES if time == "A" else TIME_A_JOGADORES

def get_parceiro(jogador_id):
    """Retorna o ID do parceiro"""
    return (jogador_id + 2) % 4

def get_emoji_time(time):
    """Retorna emoji do time"""
    return "🔵" if time == "A" else "🔴"

def calcular_forca_carta(carta, manilha):
    """Calcula a força de uma carta"""
    from config import ORDEM_CARTAS, NAIPES
    valor, naipe = carta
    if valor == manilha:
        return 100 + NAIPES[naipe]
    return ORDEM_CARTAS.index(valor)

def e_carta_vermelha(naipe):
    """Verifica se o naipe é vermelho"""
    from config import NAIPES_VERMELHOS
    return naipe in NAIPES_VERMELHOS

def formatar_carta(carta, usar_simbolo=True):
    """Formata carta para exibição"""
    from config import NAIPE_SIMBOLOS
    valor, naipe = carta
    if usar_simbolo:
        return f"{valor}{NAIPE_SIMBOLOS.get(naipe, naipe[0])}"
    return f"{valor} de {naipe}"
