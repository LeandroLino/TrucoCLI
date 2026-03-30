import socket
import pickle
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from config import *
from utils import debug_log, get_parceiro, e_carta_vermelha

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
        self.nicks = {}
        self.placar = {time: 0 for time in TIMES}
        self.meu_time = None
        self.minha_posicao = None
        self.mesa_jogadas = []
        
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
            pass  # Ignora erro de limpeza em ambientes sem TTY
        
        # Header com Placar
        table = Table(show_header=False, expand=True, border_style="blue", padding=(0, 2))
        table.add_row(
            f"[bold cyan]TIME A: {self.placar['A']}[/]",
            f"[bold magenta]TIME B: {self.placar['B']}[/]"
        )
        console.print(table)
        
        # Informações do Jogador e Time
        if self.meu_id is not None:
            parceiro_id = get_parceiro(self.meu_id)
            parceiro_nome = self.nicks.get(parceiro_id, "???")
            time_color = COR_TIME_A if self.meu_time == "A" else COR_TIME_B
            adversarios_time = "B" if self.meu_time == "A" else "A"
            
            info_texto = (
                f"[{time_color}]TIME {self.meu_time}[/]: "
                f"[bold]{self.nicks.get(self.meu_id, '???')}[/] [{self.minha_posicao}] + "
                f"{parceiro_nome} | "
                f"[dim]Adversários: TIME {adversarios_time}[/]"
            )
            console.print(Panel(info_texto, border_style=time_color, expand=False))
        
        # Vira
        if self.vira:
            naipe_simbolo = NAIPE_SIMBOLOS.get(self.vira[1], self.vira[1][0])
            cor_vira = "red" if e_carta_vermelha(self.vira[1]) else "white"
            console.print(Panel(
                f"VIRA: [bold yellow]{self.vira[0]}[/][{cor_vira}]{naipe_simbolo}[/]",
                expand=True,
                style="white"
            ))
        
        # Log da rodada
        if self.mesa_jogadas:
            logs_formatados = []
            jogadas_validas = [j for j in self.mesa_jogadas if j["forca"] > 0]
            forca_maxima = max([j["forca"] for j in jogadas_validas]) if jogadas_validas else -1
            
            for jog in self.mesa_jogadas[-5:]:
                linha = jog["msg"]
                if jog["forca"] > 0 and jog["forca"] == forca_maxima:
                    linha += " [bold green]← Fazendo[/]"
                logs_formatados.append(linha)
            
            console.print(Panel(
                "\n".join(logs_formatados),
                title="LOG DA RODADA",
                border_style="blue"
            ))
        
        # Mão do Jogador
        self.render_cards(self.minha_mao)
        
        if msg:
            console.print(f"\n[bold reverse] {msg} [/]")
    
    def render_cards(self, cards, title="SUA MÃO"):
        """Renderiza as cartas em formato visual"""
        if not cards:
            return
        
        cols = []
        for i, carta in enumerate(cards):
            naipe_simbolo = NAIPE_SIMBOLOS.get(carta[1], carta[1][0])
            cor_naipe = "red" if e_carta_vermelha(carta[1]) else "white"
            cols.append(Panel(
                f"[bold]{carta[0]}[/]\n[{cor_naipe}]{naipe_simbolo}[/]",
                title=f"[{i}]",
                expand=False
            ))
        console.print(Panel(Columns(cols), title=title, border_style="cyan"))
    
    def pedir_jogada(self, n_queda):
        """Pede ao jogador para fazer uma jogada"""
        opcoes = f"\n[green]Carta (0-{len(self.minha_mao)-1})"
        if n_queda > 1:
            opcoes += " | 'V[num]' para Virar (ex: V0)"
        opcoes += " | 'T' para Truco: [/]"
        
        debug_log(f"Pedindo input ao jogador {self.meu_id}...")
        
        try:
            inp = console.input(opcoes).upper().strip()
            debug_log(f"Input recebido: '{inp}'")
            
            # Truco
            if inp == "T":
                debug_log("TRUCO enviado")
                return ACAO_TRUCO
            
            # Carta virada
            elif inp.startswith("V") and n_queda > 1:
                try:
                    idx = int(inp[1]) if len(inp) > 1 and inp[1].isdigit() else 0
                    idx = min(max(0, idx), len(self.minha_mao) - 1)
                    debug_log(f"Enviando carta virada (idx {idx})")
                    return (self.minha_mao.pop(idx), True)
                except (ValueError, IndexError):
                    console.print("[red]Índice inválido! Jogando carta 0 virada.[/]")
                    time.sleep(1)
                    return (self.minha_mao.pop(0), True)
            
            # Carta normal
            else:
                idx = int(inp)
                if 0 <= idx < len(self.minha_mao):
                    debug_log(f"Enviando carta normal (idx {idx})")
                    return (self.minha_mao.pop(idx), False)
                else:
                    console.print(f"[red]Carta inválida! Escolha entre 0-{len(self.minha_mao)-1}[/]")
                    time.sleep(1)
                    return (self.minha_mao.pop(0), False)
        
        except (ValueError, IndexError) as e:
            console.print(f"[red]Entrada inválida ({e})! Jogando carta 0 automaticamente.[/]")
            time.sleep(1)
            return (self.minha_mao.pop(0), False)
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            console.print(f"[red]Erro de conexão: {e}[/]")
            return None
    
    def pedir_resposta_truco(self, msg):
        """Pede ao jogador para responder ao truco"""
        try:
            resp = console.input(f"\n[bold red]{msg} (S/N/A): [/]").upper().strip()
            if resp not in RESPOSTAS_VALIDAS:
                console.print("[yellow]Resposta inválida! Usando 'N' (não aceitar)[/]")
                resp = RESPOSTA_NAO
            return resp
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Entrada cancelada! Usando 'N' (não aceitar)[/]")
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
            self.mesa_jogadas.append({
                "msg": f"[bold magenta]>> {data['msg']}[/]",
                "forca": -1
            })
            self.draw_screen()
            debug_log("RESULT processado, aguardando...")
            time.sleep(SCORE_DISPLAY_DELAY)
        
        elif tipo == MsgType.SCORE:
            self.placar = data["placar"]
            self.draw_screen("PONTUAÇÃO ATUALIZADA")
            time.sleep(SCORE_DISPLAY_DELAY)
        
        return True
    
    def run(self):
        """Loop principal do cliente"""
        if not self.conectar():
            return
        
        if not self.enviar_nick():
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
