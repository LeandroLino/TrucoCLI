import socket, pickle, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

console = Console()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect(('127.0.0.1', 5555))
except (ConnectionRefusedError, OSError) as e:
    console.print(f"[red]Erro ao conectar ao servidor: {e}[/]")
    exit(1)

try:
    nick_local = console.input("[bold yellow]Seu Nick: [/]").strip()
    if not nick_local:
        nick_local = f"Jogador_{int(time.time())}"
        console.print(f"[yellow]Nick vazio! Usando: {nick_local}[/]")
    client.sendall(pickle.dumps(nick_local))
except (KeyboardInterrupt, EOFError):
    console.print("\n[red]Conexão cancelada pelo usuário[/]")
    client.close()
    exit(0)

meu_id, minha_mao, vira, mesa, nicks, placar = None, [], None, [], {}, {"A": 0, "B": 0}
meu_time, minha_posicao = None, None
mesa_jogadas = []  # Lista de dicionários com info de cada jogada

# Símbolos dos naipes
NAIPE_SIMBOLOS = {
    "Ouros": "♦",
    "Espadas": "♠", 
    "Copas": "♥",
    "Paus": "♣"
}

def draw_screen(msg=""):
    """Desenha a tela principal do jogo"""
    try:
        console.clear()
    except Exception:
        pass  # Ignora erro de limpeza de tela em ambientes sem TTY
    
    # Header com Placar
    table = Table(show_header=False, expand=True, border_style="blue", padding=(0, 2))
    table.add_row(f"[bold cyan]TIME A: {placar['A']}[/]", f"[bold magenta]TIME B: {placar['B']}[/]")
    console.print(table)
    
    # Informações do Jogador e Time
    if meu_id is not None:
        parceiro_id = (meu_id + 2) % 4
        parceiro_nome = nicks.get(parceiro_id, "???")
        time_color = "cyan" if meu_time == "A" else "magenta"
        
        info_texto = (
            f"[{time_color}]TIME {meu_time}[/]: "
            f"[bold]{nicks.get(meu_id, '???')}[/] [{minha_posicao}] + "
            f"{parceiro_nome} | "
            f"[dim]Adversários: TIME {'B' if meu_time == 'A' else 'A'}[/]"
        )
        console.print(Panel(info_texto, border_style=time_color, expand=False))

    if vira:
        naipe_vira = NAIPE_SIMBOLOS.get(vira[1], vira[1][0])
        cor_vira = "red" if vira[1] in ["Ouros", "Copas"] else "white"
        console.print(Panel(f"VIRA: [bold yellow]{vira[0]}[/][{cor_vira}]{naipe_vira}[/]", expand=True, style="white"))

    # Mesa (mostra os logs com indicador de carta vencedora inline - sempre atualizado)
    if mesa_jogadas:
        logs_formatados = []
        # Calcula qual carta está ganhando até agora (ignora mensagens de resultado)
        jogadas_validas = [j for j in mesa_jogadas if j["forca"] > 0]
        forca_maxima = max([j["forca"] for j in jogadas_validas]) if jogadas_validas else -1
        
        for jog in mesa_jogadas[-5:]:
            linha = jog["msg"]
            # Marca como "Fazendo" se for a carta com maior força até agora
            if jog["forca"] > 0 and jog["forca"] == forca_maxima:
                linha += " [bold green]← Fazendo[/]"
            logs_formatados.append(linha)
        console.print(Panel("\n".join(logs_formatados), title="LOG DA RODADA", border_style="blue"))

    # Mão do Jogador
    render_cards(minha_mao)
    if msg: console.print(f"\n[bold reverse] {msg} [/]")

def render_cards(cards, title="SUA MÃO"):
    """Renderiza as cartas em formato visual"""
    cols = []
    for i, c in enumerate(cards):
        naipe_simbolo = NAIPE_SIMBOLOS.get(c[1], c[1][0])
        cor_naipe = "red" if c[1] in ["Ouros", "Copas"] else "white"
        cols.append(Panel(f"[bold]{c[0]}[/]\n[{cor_naipe}]{naipe_simbolo}[/]", title=f"[{i}]", expand=False))
    console.print(Panel(Columns(cols), title=title, border_style="cyan"))

while True:
    try:
        print(f"[DEBUG-CLI] Aguardando próxima mensagem do servidor...")
        raw_data = client.recv(4096)
        if not raw_data:
            console.print("[red]Servidor desconectado[/]")
            break
        data = pickle.loads(raw_data)
        print(f"[DEBUG-CLI] Recebeu: {data['tipo']}")
        
        if data["tipo"] == "NICKS": nicks = data["lista"]
        elif data["tipo"] == "START":
            meu_id, minha_mao, vira, mesa_jogadas = data["id"], data["mao"], data["vira"], []
            meu_time = data.get("time", "?")
            minha_posicao = data.get("posicao", "???")
            draw_screen("Nova mão iniciada!")
        elif data["tipo"] == "ONZE":
            draw_screen("MÃO DE ONZE!")
            render_cards(data["parceiro"], title=f"MÃO DO PARCEIRO ({data['nick_p']})")
            time.sleep(3)
        elif data["tipo"] == "WAIT_TURN":
            print(f"[DEBUG-CLI] WAIT_TURN: aguardando jogador {data['player']}")
            draw_screen(f"Aguardando {nicks.get(data['player'])}...")
        elif data["tipo"] == "TURN":
            print(f"[DEBUG-CLI] TURN recebido para player {data['player']}, meu_id={meu_id}")
            if data["player"] == meu_id:
                draw_screen("Sua vez!")
                n_queda = data.get('n_queda', 1)
                opcoes = f"\n[green]Carta (0-{len(minha_mao)-1})"
                if n_queda > 1: opcoes += " | 'V[num]' para Virar (ex: V0)"
                opcoes += " | 'T' para Truco: [/]"
                
                print(f"[DEBUG-CLI] Pedindo input ao jogador {meu_id}...")
                try:
                    inp = console.input(opcoes).upper().strip()
                    print(f"[DEBUG-CLI] Input recebido: '{inp}' - Enviando para servidor...")
                    
                    if inp == "T":
                        client.sendall(pickle.dumps("TRUCO"))
                        print(f"[DEBUG-CLI] TRUCO enviado, continuando loop...")
                        continue
                    elif inp.startswith("V") and n_queda > 1:
                        try:
                            idx_virar = int(inp[1]) if len(inp) > 1 and inp[1].isdigit() else 0
                            idx_virar = min(max(0, idx_virar), len(minha_mao) - 1)
                            print(f"[DEBUG-CLI] Enviando carta virada (idx {idx_virar})...")
                            client.sendall(pickle.dumps((minha_mao.pop(idx_virar), True)))
                        except (ValueError, IndexError):
                            console.print(f"[red]Índice inválido! Jogando carta 0 virada.[/]")
                            time.sleep(1)
                            client.sendall(pickle.dumps((minha_mao.pop(0), True)))
                    else:
                        idx_carta = int(inp)
                        if 0 <= idx_carta < len(minha_mao):
                            print(f"[DEBUG-CLI] Enviando carta normal (idx {idx_carta})...")
                            client.sendall(pickle.dumps((minha_mao.pop(idx_carta), False)))
                        else:
                            console.print(f"[red]Carta inválida! Escolha entre 0-{len(minha_mao)-1}[/]")
                            time.sleep(1)
                            client.sendall(pickle.dumps((minha_mao.pop(0), False)))
                except (ValueError, IndexError) as e:
                    console.print(f"[red]Entrada inválida ({e})! Jogando carta 0 automaticamente.[/]")
                    time.sleep(1)
                    client.sendall(pickle.dumps((minha_mao.pop(0), False)))
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    console.print(f"[red]Erro de conexão: {e}[/]")
                    break
        elif data["tipo"] == "ASK_TRUCO":
            try:
                resp = console.input(f"\n[bold red]{data['msg']} (S/N/A): [/]").upper().strip()
                if resp not in ["S", "N", "A"]:
                    console.print("[yellow]Resposta inválida! Usando 'N' (não aceitar)[/]")
                    resp = "N"
                client.sendall(pickle.dumps(resp))
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Entrada cancelada! Usando 'N' (não aceitar)[/]")
                client.sendall(pickle.dumps("N"))
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                console.print(f"[red]Erro de conexão: {e}[/]")
                break
        elif data["tipo"] == "CLEAR_LOGS":
            print(f"[DEBUG-CLI] CLEAR_LOGS processado - limpando mesa_jogadas")
            mesa_jogadas.clear()
            print(f"[DEBUG-CLI] mesa_jogadas limpa, tamanho agora: {len(mesa_jogadas)}")
            # Não redesenha aqui - será redesenhado no próximo UPDATE ou TURN
        elif data["tipo"] == "UPDATE":
            mesa_jogadas.append({"msg": f"• {data['msg']}", "forca": data.get("forca", 0)})
            draw_screen()
        elif data["tipo"] == "UPDATE_POS":
            print(f"[DEBUG-CLI] UPDATE_POS: nova posição = {data['posicao']}")
            minha_posicao = data["posicao"]
            draw_screen()  # Redesenha para mostrar nova posição
            print(f"[DEBUG-CLI] UPDATE_POS processado, tela redesenhada")
        elif data["tipo"] == "RESULT":
            print(f"[DEBUG-CLI] RESULT recebido: {data['msg']}")
            mesa_jogadas.append({"msg": f"[bold magenta]>> {data['msg']}[/]", "forca": -1})
            draw_screen()
            print(f"[DEBUG-CLI] RESULT processado, iniciando sleep 1.5s...")
            time.sleep(1.5)
            print(f"[DEBUG-CLI] Sleep concluído, voltando ao loop principal")
        elif data["tipo"] == "SCORE":
            placar = data["placar"]
            draw_screen("PONTUAÇÃO ATUALIZADA")
            time.sleep(1.5)
    except (EOFError, ConnectionResetError, BrokenPipeError, OSError) as e:
        console.print(f"\n[red]Erro de conexão: {e}[/]")
        break
    except KeyboardInterrupt:
        console.print("\n[yellow]Desconectado pelo usuário[/]")
        break
    except Exception as e:
        console.print(f"\n[red]Erro inesperado: {e}[/]")
        break

client.close()
console.print("\n[bold cyan]Conexão encerrada. Até a próxima![/]")