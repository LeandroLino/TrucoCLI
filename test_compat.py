#!/usr/bin/env python3
"""
Script de teste de compatibilidade multiplataforma
Testa se todas as funções críticas funcionam no SO atual
"""
import sys
import platform
from rich.console import Console

console = Console()

def test_imports():
    """Testa se todos os imports necessários funcionam"""
    console.print("\n[bold cyan]🔍 Testando imports...[/]")
    
    try:
        import config
        console.print("  ✅ config.py importado com sucesso")
    except Exception as e:
        console.print(f"  ❌ Erro ao importar config.py: {e}")
        return False
    
    try:
        from utils import get_key_multiplataforma, log, debug_log
        console.print("  ✅ utils.py importado com sucesso")
    except Exception as e:
        console.print(f"  ❌ Erro ao importar utils.py: {e}")
        return False
    
    try:
        import socket
        import pickle
        console.print("  ✅ Módulos de rede OK (socket, pickle)")
    except Exception as e:
        console.print(f"  ❌ Erro nos módulos de rede: {e}")
        return False
    
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        console.print("  ✅ Rich library OK")
    except Exception as e:
        console.print(f"  ❌ Erro na Rich library: {e}")
        return False
    
    return True

def test_platform_detection():
    """Testa detecção do sistema operacional"""
    console.print("\n[bold cyan]🖥️  Testando detecção de plataforma...[/]")
    
    sistema = platform.system()
    console.print(f"  Sistema detectado: [bold green]{sistema}[/]")
    console.print(f"  Versão: {platform.version()}")
    console.print(f"  Arquitetura: {platform.machine()}")
    
    if sistema == "Windows":
        console.print("  ℹ️  Modo Windows ativado - usando msvcrt")
        try:
            import msvcrt
            console.print("  ✅ msvcrt disponível")
            return True
        except ImportError:
            console.print("  ❌ msvcrt não disponível (isso é estranho no Windows!)")
            return False
    elif sistema in ("Linux", "Darwin"):
        console.print(f"  ℹ️  Modo Unix ativado - usando termios")
        try:
            import tty
            import termios
            console.print("  ✅ tty e termios disponíveis")
            return True
        except ImportError:
            console.print("  ❌ tty/termios não disponíveis")
            return False
    else:
        console.print(f"  ⚠️  Sistema não reconhecido: {sistema}")
        return False

def test_keyboard_input():
    """Testa captura de teclado"""
    console.print("\n[bold cyan]⌨️  Testando captura de teclado...[/]")
    console.print("  [dim]Pressione qualquer tecla para testar (ou 'q' para pular)...[/]")
    
    try:
        from utils import get_key_multiplataforma
        
        tecla = get_key_multiplataforma()
        
        if tecla == 'q' or tecla == 'Q':
            console.print("  ⏭️  Teste pulado pelo usuário")
            return True
        
        console.print(f"  ✅ Tecla capturada: '{tecla}' (código: {ord(tecla)})")
        return True
        
    except Exception as e:
        console.print(f"  ❌ Erro ao capturar tecla: {e}")
        return False

def test_rich_features():
    """Testa recursos do Rich"""
    console.print("\n[bold cyan]🎨 Testando recursos Rich...[/]")
    
    try:
        from rich.panel import Panel
        from rich.table import Table
        from rich.progress import Progress
        
        # Testa painel
        panel = Panel("Teste de painel", title="Título", border_style="cyan")
        console.print(panel)
        console.print("  ✅ Painéis funcionando")
        
        # Testa tabela
        table = Table(show_header=True)
        table.add_column("Col1")
        table.add_column("Col2")
        table.add_row("A", "B")
        console.print(table)
        console.print("  ✅ Tabelas funcionando")
        
        # Testa cores
        console.print("  [red]Vermelho[/] [green]Verde[/] [blue]Azul[/] [yellow]Amarelo[/]")
        console.print("  ✅ Cores funcionando")
        
        return True
        
    except Exception as e:
        console.print(f"  ❌ Erro nos recursos Rich: {e}")
        return False

def test_network():
    """Testa capacidades de rede"""
    console.print("\n[bold cyan]🌐 Testando rede...[/]")
    
    try:
        import socket
        
        # Testa criação de socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        console.print("  ✅ Socket TCP criado")
        
        # Testa bind local
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 0))  # Porta aleatória
        port = sock.getsockname()[1]
        console.print(f"  ✅ Bind local OK (porta {port})")
        
        sock.close()
        console.print("  ✅ Socket fechado corretamente")
        
        return True
        
    except Exception as e:
        console.print(f"  ❌ Erro de rede: {e}")
        return False

def main():
    """Executa todos os testes"""
    console.clear()
    
    console.print("""
╔══════════════════════════════════════════════════════════╗
║           🧪 TESTE DE COMPATIBILIDADE TRUCOCLI          ║
╚══════════════════════════════════════════════════════════╝
""", style="bold cyan")
    
    resultados = []
    
    resultados.append(("Imports", test_imports()))
    resultados.append(("Detecção de Plataforma", test_platform_detection()))
    resultados.append(("Recursos Rich", test_rich_features()))
    resultados.append(("Rede", test_network()))
    resultados.append(("Entrada de Teclado", test_keyboard_input()))
    
    # Resumo
    console.print("\n" + "═" * 60)
    console.print("[bold cyan]📊 RESUMO DOS TESTES:[/]\n")
    
    passou = 0
    falhou = 0
    
    for nome, resultado in resultados:
        if resultado:
            console.print(f"  ✅ {nome}")
            passou += 1
        else:
            console.print(f"  ❌ {nome}")
            falhou += 1
    
    console.print("\n" + "═" * 60)
    
    if falhou == 0:
        console.print(f"\n[bold green]🎉 TODOS OS TESTES PASSARAM! ({passou}/{len(resultados)})[/]")
        console.print("[green]O TrucoCLI está pronto para usar neste sistema![/]\n")
    else:
        console.print(f"\n[bold red]⚠️  ALGUNS TESTES FALHARAM ({falhou}/{len(resultados)})[/]")
        console.print("[yellow]Verifique os erros acima antes de jogar.[/]\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Testes cancelados pelo usuário[/]")
    except Exception as e:
        console.print(f"\n[red]Erro inesperado: {e}[/]")
