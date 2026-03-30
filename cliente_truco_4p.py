import socket, pickle, time
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

console = Console()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

def render_cards(cards, title="SUAS CARTAS"):
    ren = [Panel(f"{c[0]}\n{c[1][0]}", title=f"[{i}]", expand=False) for i, c in enumerate(cards)]
    console.print(Panel(Columns(ren), title=title))

meu_id, minha_mao, vira, mesa = None, [], None, []

while True:
    try:
        data = pickle.loads(client.recv(4096))
        
        if data["tipo"] == "START":
            meu_id, minha_mao, vira, mesa = data["id"], data["mao"], data["vira"], []
            console.clear()
            console.print(f"[bold yellow]Vira: {vira[0]} de {vira[1]} | Time: {data['time']}[/]")
            render_cards(minha_mao)

        elif data["tipo"] == "ONZE":
            console.print(Panel("[bold red]MÃO DE ONZE![/] Analise as cartas do seu parceiro:") )
            render_cards(data["parceiro"], title="CARTAS DO PARCEIRO")
            time.sleep(2)

        elif data["tipo"] == "TURN":
            if data["player"] == meu_id:
                console.print(f"\n[bold green]Sua vez! (Valor: {data['valor']})[/]")
                inp = console.input("Índice ou 'T' para Trucar: ").upper()
                if inp == "T":
                    client.sendall(pickle.dumps("TRUCO"))
                    continue
                client.sendall(pickle.dumps(minha_mao.pop(int(inp))))
            else:
                console.print(f"[dim]Aguardando J{data['player']}...[/]")

        elif data["tipo"] == "ASK_TRUCO":
            resp = console.input(f"{data['msg']} (S/N/A): ").upper()
            client.sendall(pickle.dumps(resp))

        elif data["tipo"] == "UPDATE":
            console.print(f"[blue]• {data['msg']}[/]")

        elif data["tipo"] == "RESULT":
            console.print(f"[bold magenta]>> {data['msg']}[/]")
            time.sleep(1)

        elif data["tipo"] == "SCORE":
            p = data["placar"]
            console.print(Panel(f"PLACAR: A {p['A']} x {p['B']} B", style="white on blue"))
            time.sleep(3)

    except: break