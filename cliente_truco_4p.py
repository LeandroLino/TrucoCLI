import socket, pickle, time
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

console = Console()
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

def renderizar_cartas(cartas):
    renderizacoes = [Panel(f"{v}\n{n[0]}", title=f"[{i}]", expand=False) for i, (v, n) in enumerate(cartas)]
    if renderizacoes: console.print(Columns(renderizacoes))

def refresh_screen(meu_id, time_nome, vira, mao, mesa):
    console.clear()
    console.print(Panel(f"Vira: {vira[0]} de {vira[1]} | TIME {time_nome}", title=f"JOGADOR {meu_id}", border_style="green"))
    if mesa: console.print(Panel(Text("\n".join(mesa), style="blue"), title="MESA"))
    renderizar_cartas(mao)

meu_id, minha_mao, meu_time, vira_atual, mesa_atual = None, [], "", None, []

while True:
    try:
        data = pickle.loads(client.recv(4096))
        
        if data["tipo"] == "START":
            meu_id, minha_mao, meu_time, vira_atual = data.get("id", meu_id), data["mao"], data["time"], data["vira"]
            mesa_atual = []
            refresh_screen(meu_id, meu_time, vira_atual, minha_mao, mesa_atual)

        elif data["tipo"] == "TURN":
            refresh_screen(meu_id, meu_time, vira_atual, minha_mao, mesa_atual)
            if data["player"] == meu_id:
                console.print("\n[yellow]Sua vez! Digite o índice ou 'T' para TRUCO:[/]")
                inp = console.input("> ").upper()
                if inp == "T":
                    client.sendall(pickle.dumps("TRUCO"))
                    inp = console.input("Aguardando resposta... Agora escolha a carta: ")
                client.sendall(pickle.dumps(minha_mao.pop(int(inp))))
            else:
                console.print(f"[dim]Aguardando Jogador {data['player']}...[/]")

        elif data["tipo"] == "ASK_TRUCO":
            console.print(Panel(data["msg"], title="⚠️ DESAFIO", border_style="red"))
            resp = console.input("(S/N/A): ").upper()
            client.sendall(pickle.dumps(resp))

        elif data["tipo"] == "UPDATE":
            mesa_atual.append(data["msg"])
            refresh_screen(meu_id, meu_time, vira_atual, minha_mao, mesa_atual)

        elif data["tipo"] == "RESULT":
            console.print(f"\n[magenta]>> {data['msg']} <<[/]")
            time.sleep(1.5)
            mesa_atual = []

        elif data["tipo"] == "SCORE":
            p = data["placar"]
            console.print(Panel(f"Time A: {p['A']} | Time B: {p['B']}", title="PLACAR", style="white on blue"))
            time.sleep(2) # Reduzi para evitar o engasgo

    except: break