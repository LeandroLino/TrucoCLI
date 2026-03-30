import socket, pickle, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

console = Console()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

nick_local = console.input("[bold yellow]Seu Nick: [/]")
client.sendall(pickle.dumps(nick_local))

meu_id, minha_mao, vira, mesa, nicks, placar = None, [], None, [], {}, {"A": 0, "B": 0}

def draw_screen(msg=""):
    console.clear()
    # Header com Placar
    table = Table(show_header=False, expand=True, border_style="blue")
    table.add_row(f"[bold cyan]TIME A: {placar['A']}[/]", f"[bold magenta]TIME B: {placar['B']}[/]")
    console.print(table)

    if vira:
        console.print(Panel(f"VIRA: [bold yellow]{vira[0]} de {vira[1]}[/]", expand=True, style="white"))

    # Mesa (mostra as últimas 4 ações)
    if mesa:
        console.print(Panel("\n".join(mesa[-4:]), title="LOG DA RODADA", border_style="blue"))

    # Mão do Jogador
    render_cards(minha_mao)
    if msg: console.print(f"\n[bold reverse] {msg} [/]")

def render_cards(cards, title="SUA MÃO"):
    cols = [Panel(f"{c[0]}\n{c[1][0]}", title=f"[{i}]", expand=False) for i, c in enumerate(cards)]
    console.print(Panel(Columns(cols), title=title, border_style="cyan"))

while True:
    try:
        data = pickle.loads(client.recv(4096))
        
        if data["tipo"] == "NICKS": nicks = data["lista"]
        elif data["tipo"] == "START":
            meu_id, minha_mao, vira, mesa = data["id"], data["mao"], data["vira"], []
            draw_screen("Nova mão iniciada!")
        elif data["tipo"] == "ONZE":
            draw_screen("MÃO DE ONZE!")
            render_cards(data["parceiro"], title=f"MÃO DO PARCEIRO ({data['nick_p']})")
            time.sleep(3)
        elif data["tipo"] == "TURN":
            draw_screen(f"Vez de {nicks.get(data['player'])}")
            if data["player"] == meu_id:
                val = data.get('valor', 1)
                inp = console.input(f"\n[green]Carta (0-{len(minha_mao)-1}) ou 'T' para Truco: [/]").upper()
                if inp == "T":
                    client.sendall(pickle.dumps("TRUCO"))
                    continue
                client.sendall(pickle.dumps(minha_mao.pop(int(inp))))
        elif data["tipo"] == "ASK_TRUCO":
            resp = console.input(f"\n[bold red]{data['msg']} (S/N/A): [/]").upper()
            client.sendall(pickle.dumps(resp))
        elif data["tipo"] == "UPDATE":
            mesa.append(f"• {data['msg']}")
            draw_screen()
        elif data["tipo"] == "RESULT":
            mesa.append(f"[bold magenta]>> {data['msg']}[/]")
            draw_screen()
            time.sleep(1.5)
        elif data["tipo"] == "SCORE":
            placar = data["placar"]
            draw_screen("PONTUAÇÃO ATUALIZADA")
            time.sleep(2)
    except: break