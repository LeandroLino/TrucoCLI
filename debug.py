#!/usr/bin/env python3
"""
Script para ativar/desativar modo DEBUG
"""
import sys

CONFIG_FILE = "config.py"

def toggle_debug():
    """Alterna o modo DEBUG no arquivo config.py"""
    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    current_state = False
    
    for line in lines:
        if line.strip().startswith("DEBUG_MODE ="):
            if "True" in line:
                new_lines.append("DEBUG_MODE = False  # Mude para True para ativar logs de debug\n")
                current_state = False
            else:
                new_lines.append("DEBUG_MODE = True  # Mude para True para ativar logs de debug\n")
                current_state = True
        else:
            new_lines.append(line)
    
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(new_lines)
    
    estado = "ATIVADO ✅" if current_state else "DESATIVADO ❌"
    print(f"\n🔧 Modo DEBUG {estado}\n")

def show_status():
    """Mostra o status atual do DEBUG_MODE"""
    with open(CONFIG_FILE, 'r') as f:
        for line in f:
            if line.strip().startswith("DEBUG_MODE ="):
                if "True" in line:
                    print("\n📊 Status: DEBUG ATIVADO ✅\n")
                else:
                    print("\n📊 Status: DEBUG DESATIVADO ❌\n")
                return

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_status()
        elif sys.argv[1] == "on":
            # Força ativar
            with open(CONFIG_FILE, 'r') as f:
                lines = f.readlines()
            with open(CONFIG_FILE, 'w') as f:
                for line in lines:
                    if line.strip().startswith("DEBUG_MODE ="):
                        f.write("DEBUG_MODE = True  # Mude para True para ativar logs de debug\n")
                    else:
                        f.write(line)
            print("\n🔧 Modo DEBUG ATIVADO ✅\n")
        elif sys.argv[1] == "off":
            # Força desativar
            with open(CONFIG_FILE, 'r') as f:
                lines = f.readlines()
            with open(CONFIG_FILE, 'w') as f:
                for line in lines:
                    if line.strip().startswith("DEBUG_MODE ="):
                        f.write("DEBUG_MODE = False  # Mude para True para ativar logs de debug\n")
                    else:
                        f.write(line)
            print("\n🔧 Modo DEBUG DESATIVADO ❌\n")
        else:
            print("Uso: python3 toggle_debug.py [status|on|off|toggle]")
    else:
        toggle_debug()
