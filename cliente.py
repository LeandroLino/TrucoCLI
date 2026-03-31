import socket
import pickle
import time
import sys
import tty
import termios
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from rich.text import Text

from config import *
from utils import debug_log, get_parceiro, e_carta_vermelha, criar_barra_progresso, get_emoji_posicao, e_manilha, get_nome_manilha, formatar_carta_para_select
from stats import GameStats

console = Console()

class TrucoClient:
    def __init__(self, host=CLIENT_HOST, port=SERVER_PORT):
        """Inicializa o cliente de Truco"""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        
        # Estado do jogo
        self.meu_id = None
        self.minha_mao = []
        self.vira = None
        self.manilha = None
        self.nicks = {}
        self.placar = {team: 0 for team in TIMES}
        self.meu_time = None
        self.minha_posicao = None
        self.mesa_jogadas = []
        self.historico_pontos = []
        
        # Contador de quedas na mão atual
        self.quedas_vencidas = {"A": 0, "B": 0}
        
        # Estatísticas
        self.stats = GameStats() if ENABLE_STATS else None
        
    def conectar(self):
        """Conecta ao servidor"""
        try:
            self.client.connect((self.host, self.port))
            return True
        except (ConnectionRefusedError, OSError) as e:
            console.print(f"[red]Erro ao conectar ao servidor: {e}[/]")
            return False
    
    def enviar_nick(self):
        """Envia nick do jogador ao servidor"""
        try:
            nick = console.input("[bold yellow]Seu Nick: [/]").strip()
            if not nick:
                nick = f"Jogador_{int(time.time())}"
                console.print(f"[yellow]Nick vazio! Usando: {nick}[/]")
            self.client.sendall(pickle.dumps(nick))
            return True
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Conexão cancelada pelo usuário[/]")
            return False
    
    def mostrar_lobby(self, estado):
        """Mostra interface do lobby"""
        console.clear()
        
        sala_id = estado.get("sala_id", "????")
        jogadores = estado.get("jogadores", [])
        team_a_count = estado.get("team_a_count", 0)
        team_b_count = estado.get("team_b_count", 0)
        total = estado.get("total", 0)
        
        # Header
        header = f"""
╔══════════════════════════════════════════════════════════╗
║                  🎴 LOBBY - TRUCO CLI                    ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  SALA: #{sala_id}                   Jogadores: {total}/4            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        console.print(header, style="bold cyan")
        
        # Times
        console.print("\n")
        
        # Time A
        time_a_status = "CHEIO" if team_a_count >= 2 else f"{team_a_count}/2"
        time_a_panel = []
        time_a_panel.append(f"[bold cyan]TIME A (🔵) [{time_a_status}][/]")
        time_a_panel.append("")
        
        jogadores_a = [j for j in jogadores if j["time"] == "A"]
        for i, jogador in enumerate(jogadores_a):
            pronto = "✓" if jogador["pronto"] else " "
            time_a_panel.append(f"[{pronto}] {jogador['nick']}")
        
        for _ in range(2 - len(jogadores_a)):
            time_a_panel.append("[ ] Aguardando...")
        
        # Time B
        time_b_status = "CHEIO" if team_b_count >= 2 else f"{team_b_count}/2"
        time_b_panel = []
        time_b_panel.append(f"[bold magenta]TIME B (🔴) [{time_b_status}][/]")
        time_b_panel.append("")
        
        jogadores_b = [j for j in jogadores if j["time"] == "B"]
        for i, jogador in enumerate(jogadores_b):
            pronto = "✓" if jogador["pronto"] else " "
            time_b_panel.append(f"[{pronto}] {jogador['nick']}")
        
        for _ in range(2 - len(jogadores_b)):
            time_b_panel.append("[ ] Aguardando...")
        
        # Exibe times lado a lado
        table = Table.grid(padding=2)
        table.add_column()
        table.add_column()
        
        table.add_row(
            Panel("\n".join(time_a_panel), border_style="cyan"),
            Panel("\n".join(time_b_panel), border_style="magenta")
        )
        
        console.print(table)
        
        # Jogadores sem time
        sem_time = [j for j in jogadores if j["time"] is None]
        if sem_time:
            console.print("\n[yellow]Aguardando escolha de time:[/]")
            for j in sem_time:
                console.print(f"  • {j['nick']}")
        
        # Instruções
        console.print("\n" + "─" * 60)
        console.print("[bold yellow]Comandos:[/]")
        console.print("  [A] - Entrar no Time A")
        console.print("  [B] - Entrar no Time B")
        console.print("  [S] - Sair do time atual")
        console.print("  [R] - Marcar como Pronto")
        
        # Aviso se times estão cheios
        if team_a_count >= 2 and team_b_count >= 2:
            console.print("\n[dim]ℹ️  Ambos os times estão cheios (2x2).[/]")
            console.print("[dim]   Use [S] para sair e liberar vaga.[/]")
        
        console.print("─" * 60)
    
    def processar_lobby(self):
        """Processa fase de lobby"""
        console.clear()
        console.print("[bold cyan]Conectando ao lobby...[/]")
        
        # Recebe mensagem de entrada no lobby
        data = self.receber_mensagem()
        if data is None or data.get("tipo") != "LOBBY_JOINED":
            console.print("[red]Erro ao entrar no lobby[/]")
            return False
        
        sala_id = data.get("sala_id")
        console.print(f"[green]{data.get('msg', '')}[/]")
        console.print(f"[bold cyan]Sala: #{sala_id}[/]")
        time.sleep(0.5)
        
        ultimo_estado = None
        
        # Loop do lobby
        while True:
            # Verifica se há mensagens do servidor com timeout curto
            self.client.settimeout(0.5)
            try:
                raw_data = self.client.recv(BUFFER_SIZE)
                if not raw_data:
                    console.print("[red]Servidor desconectado[/]")
                    return False
                
                data = pickle.loads(raw_data)
                tipo = data.get("tipo")
                
                if tipo == MsgType.LOBBY_STATE:
                    estado = data.get("estado", {})
                    if estado != ultimo_estado:
                        self.mostrar_lobby(estado)
                        ultimo_estado = estado
                
                elif tipo == MsgType.LOBBY_START:
                    console.clear()
                    console.print("[bold green]🎮 Iniciando partida...[/]")
                    time.sleep(1)
                    self.client.settimeout(None)
                    return True
                
                elif tipo == "ERROR":
                    console.print(f"[red]{data.get('msg', 'Erro')}[/]")
                    time.sleep(0.5)
            
            except socket.timeout:
                # Timeout normal - permite input do usuário
                try:
                    import select
                    if select.select([sys.stdin], [], [], 0)[0]:
                        escolha = input().upper().strip()
                        
                        if escolha == "A":
                            self.client.sendall(pickle.dumps({
                                "tipo": MsgType.LOBBY_JOIN_TEAM,
                                "time": "A"
                            }))
                        elif escolha == "B":
                            self.client.sendall(pickle.dumps({
                                "tipo": MsgType.LOBBY_JOIN_TEAM,
                                "time": "B"
                            }))
                        elif escolha == "S":
                            self.client.sendall(pickle.dumps({
                                "tipo": MsgType.LOBBY_LEAVE_TEAM
                            }))
                        elif escolha == "R":
                            self.client.sendall(pickle.dumps({
                                "tipo": MsgType.LOBBY_READY
                            }))
                
                except Exception:
                    pass
            
            except Exception as e:
                console.print(f"[red]Erro no lobby: {e}[/]")
                return False
        
        return False
    
    def receber_mensagem(self):
        """Recebe mensagem do servidor"""
        try:
            raw_data = self.client.recv(BUFFER_SIZE)
            if not raw_data:
                console.print("[red]Servidor desconectado[/]")
                return None
            return pickle.loads(raw_data)
        except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
            console.print(f"[red]Erro de conexão: {e}[/]")
            return None
    
    def enviar_resposta(self, resposta):
        """Envia resposta ao servidor"""
        try:
            self.client.sendall(pickle.dumps(resposta))
            return True
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            console.print(f"[red]Erro ao enviar: {e}[/]")
            return False
    
    def draw_screen(self, msg=""):
        """Desenha a tela principal do jogo"""
        try:
            console.clear()
        except Exception:
            pass
        
        # Header com Placar Melhorado
        self.draw_placar()
        
        # Informações do Jogador e Time
        if self.meu_id is not None:
            self.draw_info_jogador()
        
        # Vira e Manilha
        if self.vira:
            self.draw_vira()
        
        # Log da rodada
        if self.mesa_jogadas:
            self.draw_log_rodada()
        
        # Mão do Jogador
        self.render_cards(self.minha_mao)
        
        if msg:
            console.print(f"\n[bold reverse] {msg} [/]")
    
    def draw_placar(self):
        """Desenha placar com barra de progresso"""
        table = Table(show_header=False, expand=True, border_style="blue", padding=(0, 2))
        
        # Time A
        barra_a = criar_barra_progresso(self.placar['A'], PONTOS_VITORIA, largura=15)
        quedas_a = "●" * self.quedas_vencidas["A"] + "○" * (2 - self.quedas_vencidas["A"])
        col_a = f"[bold {COR_TIME_A}]TIME A: {self.placar['A']}/12[/]\n{barra_a}\n[dim]Quedas: {quedas_a}[/]"
        
        # Time B  
        barra_b = criar_barra_progresso(self.placar['B'], PONTOS_VITORIA, largura=15)
        quedas_b = "●" * self.quedas_vencidas["B"] + "○" * (2 - self.quedas_vencidas["B"])
        col_b = f"[bold {COR_TIME_B}]TIME B: {self.placar['B']}/12[/]\n{barra_b}\n[dim]Quedas: {quedas_b}[/]"
        
        table.add_row(col_a, col_b)
        console.print(table)
        
        # Histórico de pontos (últimos 5)
        if self.historico_pontos:
            historico_str = " → ".join(self.historico_pontos[-5:])
            console.print(f"[dim]Histórico: {historico_str}[/]")
    
    def draw_info_jogador(self):
        """Desenha informações do jogador"""
        parceiro_id = get_parceiro(self.meu_id)
        parceiro_nome = self.nicks.get(parceiro_id, "???")
        time_color = COR_TIME_A if self.meu_time == "A" else COR_TIME_B
        adversarios_time = "B" if self.meu_time == "A" else "A"
        
        info_texto = (
            f"[{time_color}]{ICON_PONTOS} TIME {self.meu_time}[/]: "
            f"[bold]{self.nicks.get(self.meu_id, '???')}[/] "
            f"[{self.minha_posicao}] + {parceiro_nome} | "
            f"[dim]Adversários: TIME {adversarios_time}[/]"
        )
        console.print(Panel(info_texto, border_style=time_color, expand=False))
    
    def draw_vira(self):
        """Desenha vira e explicação de manilha"""
        naipe_simbolo = NAIPE_SIMBOLOS.get(self.vira[1], self.vira[1][0])
        cor_vira = "red" if e_carta_vermelha(self.vira[1]) else "white"
        
        # Calcula a manilha
        if self.manilha is None:
            idx_vira = ORDEM_CARTAS.index(self.vira[0])
            self.manilha = ORDEM_CARTAS[(idx_vira + 1) % len(ORDEM_CARTAS)]
        
        nome_manilha = get_nome_manilha(self.manilha)
        
        vira_text = (
            f"VIRA: [bold yellow]{self.vira[0]}[/][{cor_vira}]{naipe_simbolo}[/] "
            f"| {ICON_MANILHA} MANILHA: [bold green]{self.manilha}[/] ({nome_manilha})"
        )
        console.print(Panel(vira_text, expand=True, style="white"))
    
    def draw_log_rodada(self):
        """Desenha log da rodada com carta vencedora animada"""
        logs_formatados = []
        jogadas_validas = [j for j in self.mesa_jogadas if j["forca"] > 0]
        forca_maxima = max([j["forca"] for j in jogadas_validas]) if jogadas_validas else -1
        
        for jog in self.mesa_jogadas[-5:]:
            linha = jog["msg"]
            # Animação na carta vencedora
            if jog["forca"] > 0 and jog["forca"] == forca_maxima:
                linha += f" [{COR_VENCEDOR}]← {ICON_CARTA_ALTA} FAZENDO[/]"
            logs_formatados.append(linha)
        
        console.print(Panel(
            "\n".join(logs_formatados),
            title=f"[bold blue]📝 LOG DA RODADA[/]",
            border_style="blue"
        ))
    
    def render_cards(self, cards, title="🎴 SUA MÃO"):
        """Renderiza as cartas em formato visual"""
        if not cards:
            return
        
        cols = []
        for i, carta in enumerate(cards):
            naipe_simbolo = NAIPE_SIMBOLOS.get(carta[1], carta[1][0])
            cor_naipe = "red" if e_carta_vermelha(carta[1]) else "white"
            
            card_content = f"[bold]{carta[0]}[/]\n[{cor_naipe}]{naipe_simbolo}[/]"
            
            cols.append(Panel(
                card_content,
                title=f"[{i}]",
                expand=False,
                border_style="cyan"
            ))
        console.print(Panel(Columns(cols), title=title, border_style="cyan"))
    
    def selecionar_carta_interativo(self, n_queda):
        """Seleção interativa de carta com setas do teclado"""
        opcoes = []
        
        # Monta lista de opções
        for i, carta in enumerate(self.minha_mao):
            opcoes.append({
                "tipo": "carta",
                "index": i,
                "label": formatar_carta_para_select(carta, i, self.manilha),
                "virada": False
            })
        
        # Adiciona opção de virar (se permitido)
        if n_queda > 1:
            for i, carta in enumerate(self.minha_mao):
                opcoes.append({
                    "tipo": "virada",
                    "index": i,
                    "label": f"[{i}] Virar carta 🔄",
                    "virada": True
                })
        
        # Adiciona opção de truco
        opcoes.append({
            "tipo": "truco",
            "label": f"{ICON_TRUCO} Pedir Truco",
            "virada": False
        })
        
        # Adiciona comandos
        opcoes.append({
            "tipo": "comando",
            "comando": CMD_AJUDA,
            "label": "❓ Ajuda"
        })
        opcoes.append({
            "tipo": "comando",
            "comando": CMD_STATS,
            "label": "📊 Estatísticas"
        })
        
        selecionado = 0
        
        console.print("\n")  # Espaço antes do menu
        
        while True:
            # Monta o menu
            menu_lines = ["[bold cyan]Use ↑/↓ para navegar, ENTER para selecionar:[/]"]
            menu_lines.append("")
            
            for i, opcao in enumerate(opcoes):
                if i == selecionado:
                    menu_lines.append(f"[bold green]► {opcao['label']}[/]")
                else:
                    menu_lines.append(f"  {opcao['label']}")
            
            # Mostra o menu
            for line in menu_lines:
                console.print(line)
            
            # Captura tecla
            tecla = self.get_key()
            
            # Limpa o menu (volta N linhas e limpa)
            for _ in range(len(menu_lines)):
                # Move cursor para cima e limpa linha
                sys.stdout.write('\033[F\033[K')
            sys.stdout.flush()
            
            if tecla == '\x1b':  # ESC sequence
                next_key = self.get_key()
                if next_key == '[':
                    arrow = self.get_key()
                    if arrow == 'A':  # Seta para cima
                        selecionado = (selecionado - 1) % len(opcoes)
                    elif arrow == 'B':  # Seta para baixo
                        selecionado = (selecionado + 1) % len(opcoes)
            
            elif tecla == '\r' or tecla == '\n':  # ENTER
                # Limpa o menu uma última vez
                for _ in range(len(menu_lines)):
                    sys.stdout.write('\033[F\033[K')
                sys.stdout.flush()
                break
        
        # Processa a opção escolhida
        opcao_escolhida = opcoes[selecionado]
        
        if opcao_escolhida["tipo"] == "truco":
            console.print(f"[bold yellow]{ICON_TRUCO} Pedindo Truco![/]")
            return ACAO_TRUCO
        
        elif opcao_escolhida["tipo"] == "comando":
            cmd = opcao_escolhida["comando"]
            if cmd == CMD_AJUDA:
                console.print(MSG_AJUDA)
                console.input("\n[yellow]Pressione ENTER para continuar...[/]")
                self.draw_screen("Sua vez!")
                return self.selecionar_carta_interativo(n_queda)
            elif cmd == CMD_STATS:
                if self.stats:
                    console.print(self.stats.get_stats_formatadas())
                    console.print(self.stats.get_stats_sessao())
                else:
                    console.print("[yellow]Estatísticas desabilitadas[/]")
                console.input("\n[yellow]Pressione ENTER para continuar...[/]")
                self.draw_screen("Sua vez!")
                return self.selecionar_carta_interativo(n_queda)
        
        else:  # carta normal ou virada
            idx = opcao_escolhida["index"]
            virada = opcao_escolhida["virada"]
            carta = self.minha_mao.pop(idx)
            
            if virada:
                console.print(f"[bold yellow]🔄 Virando carta {idx}![/]")
            else:
                carta_fmt = formatar_carta_para_select(carta, idx, self.manilha)
                console.print(f"[bold green]✓ Jogando {carta_fmt}[/]")
            
            if self.stats:
                self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=virada)
            
            return (carta, virada)
    
    def get_key(self):
        """Captura uma tecla do teclado"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def pedir_jogada(self, n_queda):
        """Pede ao jogador para fazer uma jogada"""
        debug_log(f"Pedindo input ao jogador {self.meu_id}...")
        
        # Modo interativo
        if USE_INTERACTIVE_SELECT:
            try:
                return self.selecionar_carta_interativo(n_queda)
            except Exception as e:
                console.print(f"[yellow]Erro no modo interativo: {e}. Usando modo texto.[/]")
                # Fallback para modo texto
        
        # Modo texto (fallback ou desabilitado)
        opcoes = f"\n[green]Carta (0-{len(self.minha_mao)-1})"
        if n_queda > 1:
            opcoes += " | 'V[num]' para Virar"
        opcoes += f" | 'T' para {ICON_TRUCO}Truco | '/ajuda' para ajuda: [/]"
        
        debug_log(f"Pedindo input ao jogador {self.meu_id}...")
        
        try:
            inp = console.input(opcoes).upper().strip()
            debug_log(f"Input recebido: '{inp}'")
            
            # Comandos especiais
            if inp in [CMD_AJUDA, "/AJUDA"]:
                console.print(MSG_AJUDA)
                console.input("\n[yellow]Pressione ENTER para continuar...[/]")
                self.draw_screen("Sua vez!")
                return self.pedir_jogada(n_queda)
            
            if inp in [CMD_STATS, "/STATS"]:
                if self.stats:
                    console.print(self.stats.get_stats_formatadas())
                    console.print(self.stats.get_stats_sessao())
                else:
                    console.print("[yellow]Estatísticas desabilitadas[/]")
                console.input("\n[yellow]Pressione ENTER para continuar...[/]")
                self.draw_screen("Sua vez!")
                return self.pedir_jogada(n_queda)
            
            # Truco
            if inp == "T":
                debug_log("TRUCO enviado")
                if self.stats:
                    self.stats.registrar_truco()
                return ACAO_TRUCO
            
            # Carta virada
            elif inp.startswith("V") and n_queda > 1:
                try:
                    idx = int(inp[1]) if len(inp) > 1 and inp[1].isdigit() else 0
                    idx = min(max(0, idx), len(self.minha_mao) - 1)
                    debug_log(f"Enviando carta virada (idx {idx})")
                    carta = self.minha_mao.pop(idx)
                    if self.stats:
                        self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=True)
                    return (carta, True)
                except (ValueError, IndexError):
                    console.print("[red]Índice inválido! Jogando carta 0 virada.[/]")
                    time.sleep(1)
                    carta = self.minha_mao.pop(0)
                    if self.stats:
                        self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=True)
                    return (carta, True)
            
            # Carta normal
            else:
                idx = int(inp)
                if 0 <= idx < len(self.minha_mao):
                    debug_log(f"Enviando carta normal (idx {idx})")
                    carta = self.minha_mao.pop(idx)
                    if self.stats:
                        self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=False)
                    return (carta, False)
                else:
                    console.print(f"[red]Carta inválida! Escolha entre 0-{len(self.minha_mao)-1}[/]")
                    time.sleep(1)
                    carta = self.minha_mao.pop(0)
                    if self.stats:
                        self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=False)
                    return (carta, False)
        
        except (ValueError, IndexError) as e:
            console.print(f"[red]Entrada inválida ({e})! Jogando carta 0 automaticamente.[/]")
            time.sleep(1)
            carta = self.minha_mao.pop(0)
            if self.stats:
                self.stats.registrar_carta(carta, e_manilha(carta, self.manilha), virada=False)
            return (carta, False)
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            console.print(f"[red]Erro de conexão: {e}[/]")
            return None
    
    def pedir_resposta_truco(self, msg):
        """Pede ao jogador para responder ao truco"""
        try:
            # Mensagem com confirmação
            console.print(f"\n[{COR_ALERTA}]{ICON_TRUCO} {msg}[/]")
            console.print("[dim]Digite 'S' para aceitar, 'N' para correr, 'A' para aumentar[/]")
            
            resp = console.input(f"[bold red]Sua resposta (S/N/A): [/]").upper().strip()
            
            # Confirmação antes de correr
            if resp == RESPOSTA_NAO:
                confirma = console.input("[yellow]⚠️  Tem certeza que quer CORRER? (S/N): [/]").upper().strip()
                if confirma != "S":
                    console.print("[green]Ok, vamos continuar![/]")
                    return self.pedir_resposta_truco(msg)
            
            if resp not in RESPOSTAS_VALIDAS:
                console.print("[yellow]Resposta inválida! Usando 'N' (correr)[/]")
                resp = RESPOSTA_NAO
            
            # Registra estatística
            if self.stats:
                if resp == RESPOSTA_SIM:
                    self.stats.registrar_truco(aceito=True)
                elif resp == RESPOSTA_NAO:
                    self.stats.registrar_truco(corrido=True)
                elif resp == RESPOSTA_AUMENTAR:
                    self.stats.registrar_truco()
            
            return resp
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Entrada cancelada! Usando 'N' (correr)[/]")
            if self.stats:
                self.stats.registrar_truco(corrido=True)
            return RESPOSTA_NAO
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            console.print(f"[red]Erro de conexão: {e}[/]")
            return None
    
    def processar_mensagem(self, data):
        """Processa mensagem recebida do servidor"""
        tipo = data["tipo"]
        debug_log(f"Recebeu: {tipo}")
        
        if tipo == MsgType.NICKS:
            self.nicks = data["lista"]
        
        elif tipo == MsgType.START:
            self.meu_id = data["id"]
            self.minha_mao = data["mao"]
            self.vira = data["vira"]
            self.mesa_jogadas = []
            self.meu_time = data.get("time", "?")
            self.minha_posicao = data.get("posicao", "???")
            # Reseta contador de quedas ao iniciar nova mão
            self.quedas_vencidas = {"A": 0, "B": 0}
            self.draw_screen("Nova mão iniciada!")
        
        elif tipo == MsgType.ONZE:
            self.draw_screen("MÃO DE ONZE!")
            self.render_cards(data["parceiro"], title=f"MÃO DO PARCEIRO ({data['nick_p']})")
            time.sleep(ONZE_DISPLAY_DELAY)
        
        elif tipo == MsgType.WAIT_TURN:
            debug_log(f"WAIT_TURN: aguardando jogador {data['player']}")
            self.draw_screen(f"Aguardando {self.nicks.get(data['player'])}...")
        
        elif tipo == MsgType.TURN:
            debug_log(f"TURN recebido para player {data['player']}, meu_id={self.meu_id}")
            if data["player"] == self.meu_id:
                self.draw_screen("Sua vez!")
                n_queda = data.get('n_queda', 1)
                
                jogada = self.pedir_jogada(n_queda)
                if jogada is None:
                    return False  # Erro de conexão
                
                if not self.enviar_resposta(jogada):
                    return False
                
                # Se for truco, aguarda processamento e nova TURN
                if jogada == ACAO_TRUCO:
                    debug_log("Aguardando processamento do truco...")
        
        elif tipo == MsgType.ASK_TRUCO:
            resp = self.pedir_resposta_truco(data['msg'])
            if resp is None or not self.enviar_resposta(resp):
                return False
        
        elif tipo == MsgType.CLEAR_LOGS:
            debug_log("CLEAR_LOGS processado - limpando mesa_jogadas")
            self.mesa_jogadas.clear()
        
        elif tipo == MsgType.UPDATE:
            self.mesa_jogadas.append({
                "msg": f"• {data['msg']}",
                "forca": data.get("forca", 0)
            })
            self.draw_screen()
        
        elif tipo == MsgType.UPDATE_POS:
            debug_log(f"UPDATE_POS: nova posição = {data['posicao']}")
            self.minha_posicao = data["posicao"]
            self.draw_screen()
        
        elif tipo == MsgType.RESULT:
            debug_log(f"RESULT recebido: {data['msg']}")
            
            # Extrai informação do vencedor da queda de forma mais robusta
            msg = data.get('msg', '')
            try:
                # Verifica se contém informação de time vencedor
                if "Time A" in msg or "(A)" in msg:
                    if "EMPATE" not in msg.upper():
                        self.quedas_vencidas["A"] += 1
                        debug_log("Time A ganhou esta queda")
                elif "Time B" in msg or "(B)" in msg:
                    if "EMPATE" not in msg.upper():
                        self.quedas_vencidas["B"] += 1
                        debug_log("Time B ganhou esta queda")
                elif "EMPATE" in msg.upper():
                    debug_log("Queda empatada - não contabiliza")
            except Exception as e:
                debug_log(f"Erro ao processar resultado da queda: {e}")
            
            self.mesa_jogadas.append({
                "msg": f"[bold magenta]>> {msg}[/]",
                "forca": -1
            })
            self.draw_screen()
            debug_log("RESULT processado, aguardando...")
            time.sleep(SCORE_DISPLAY_DELAY)
        
        elif tipo == MsgType.SCORE:
            placar_anterior = self.placar.copy()
            self.placar = data["placar"]
            
            # Registra no histórico quem pontuou
            for team in TIMES:
                if self.placar[team] > placar_anterior[team]:
                    diff = self.placar[team] - placar_anterior[team]
                    self.historico_pontos.append(f"{team}+{diff}")
            
            # Registra estatísticas
            if self.stats and "vencedor" in data:
                self.stats.registrar_mao(data["vencedor"])
            
            # Animação de pontuação
            self.draw_screen(f"{ICON_VITORIA} PONTUAÇÃO ATUALIZADA {ICON_VITORIA}")
            
            # Verifica fim de jogo
            if max(self.placar.values()) >= PONTOS_VITORIA:
                vencedor = "A" if self.placar["A"] >= PONTOS_VITORIA else "B"
                self.mostrar_fim_jogo(vencedor)
                if self.stats:
                    self.stats.registrar_partida(vencedor)
                    self.stats.salvar()
            
            time.sleep(SCORE_DISPLAY_DELAY)
        
        return True
    
    def mostrar_fim_jogo(self, vencedor):
        """Mostra tela de fim de jogo"""
        console.clear()
        
        if vencedor == self.meu_time:
            mensagem = f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              {ICON_VITORIA}  VITÓRIA! {ICON_VITORIA}                         ║
║                                                          ║
║          TIME {vencedor} VENCEU A PARTIDA!                       ║
║                                                          ║
║              Placar Final: {self.placar['A']} x {self.placar['B']}                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
            console.print(f"[{COR_SUCESSO}]{mensagem}[/]")
        else:
            mensagem = f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              {ICON_DERROTA}  DERROTA  {ICON_DERROTA}                        ║
║                                                          ║
║          TIME {vencedor} VENCEU A PARTIDA                        ║
║                                                          ║
║              Placar Final: {self.placar['A']} x {self.placar['B']}                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
            console.print(f"[{COR_ERRO}]{mensagem}[/]")
        
        # Mostra estatísticas se habilitado
        if self.stats:
            console.print(self.stats.get_stats_sessao())
        
        console.input("\n[yellow]Pressione ENTER para sair...[/]")
    
    def run(self):
        """Loop principal do cliente"""
        if not self.conectar():
            return
        
        if not self.enviar_nick():
            self.client.close()
            return
        
        # Fase de lobby
        if not self.processar_lobby():
            self.client.close()
            return
        
        # Loop de jogo
        while True:
            debug_log("Aguardando próxima mensagem do servidor...")
            
            data = self.receber_mensagem()
            if data is None:
                break
            
            if not self.processar_mensagem(data):
                break
        
        self.client.close()
        console.print("\n[bold cyan]Conexão encerrada. Até a próxima![/]")

if __name__ == "__main__":
    try:
        client = TrucoClient()
        client.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Desconectado pelo usuário[/]")
    except Exception as e:
        console.print(f"\n[red]Erro inesperado: {e}[/]")
