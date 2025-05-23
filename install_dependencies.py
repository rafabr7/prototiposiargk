import subprocess
import sys

# Bibliotecas e suas versões mínimas/exatas desejadas
# O formato é "biblioteca": "versao" ou "biblioteca": ">=versao"
# Usaremos as versões exatas do seu prompt inicial para garantir consistência.
REQUIRED_LIBS = {
    "mss": "9.0.0",
    "opencv-python-headless": "4.9.0.80", # O prompt tinha 4.9.0, mas opencv geralmente tem 4 partes
    "pyautogui": "0.9.54", # O prompt tinha 0.9.53, versão mais recente é 0.9.54
    "pillow": "10.4.0", # Tentando a versão mais recente após falha com 10.3.0
    # "human-mouse": "2.2.1", # Esta biblioteca parece não existir mais ou foi renomada/descontinuada.
                               # Vou comentar por enquanto e podemos pesquisar alternativas depois se necessário.
    "pyhm": "0.0.7", # O prompt tinha "pyHM": "3.7.0" e 0.1.6 não foi encontrado. Tentando 0.0.7 que pip listou.
                    # É possível que "pyHM" com "3.7.0" seja outra biblioteca ou uma versão customizada.
                    # Vamos usar a versão disponível no PyPI. Se for outra, precisaremos do link/fonte correta.
    "packaging": "24.0",  # Adicionada dependência para verificação de versão
    "dxcam": "0.0.5",  # Alterado para a versão que foi instalada com sucesso
    "numpy": "<2.0,>=1.21.2" # Adicionando a restrição do NumPy aqui para a verificação
}

# Definição de outras dependências que são instaladas via requirements.txt mas não estão na lista principal de verificação de versão exata.
# Ou podem ser verificadas com menor rigor.
OTHER_DEPENDENCIES = {
    "pyperclip": None, 
    "pyscreeze": None,
    "pygetwindow": None,
    "mouseinfo": None,
    "pytweening": None,
    "pymsgbox": None
}

def install_and_verify_libraries(libs):
    """
    Instala ou atualiza as bibliotecas listadas e verifica suas versões.
    """
    print("Iniciando a instalação/atualização de dependências...")
    all_installed_correctly = True

    for lib, target_version_spec in libs.items():
        # Tenta instalar/atualizar a biblioteca
        try:
            print(f"Instalando/Atualizando {lib} (versão alvo: {target_version_spec})...")
            # Usamos a versão exata para garantir consistência
            # Se quiséssemos >= usaríamos f"{lib}>={target_version_spec}"
            # Para exata, o pip install já entende "lib==versao"
            if target_version_spec.startswith(">="):
                 package_spec = f"{lib}{target_version_spec}"
            else:
                 package_spec = f"{lib}=={target_version_spec}"

            # subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package_spec])
            # Usando apenas install, pois --upgrade com ==versao pode não fazer o downgrade se uma maior estiver instalada.
            # pip install lib==versao irá instalar a versão exata, ou falhar se não for possível.
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec])
            print(f"{lib} instalado/atualizado com sucesso para a especificação {target_version_spec}.")

        except subprocess.CalledProcessError as e:
            print(f"ERRO ao instalar/atualizar {lib}: {e}")
            all_installed_correctly = False
        except Exception as e:
            print(f"ERRO inesperado ao processar {lib}: {e}")
            all_installed_correctly = False
        print("-" * 30)

    if all_installed_correctly:
        print("\nTodas as dependências principais parecem ter sido instaladas/configuradas corretamente.")
    else:
        print("\nATENÇÃO: Algumas dependências não puderam ser instaladas/configuradas corretamente. Verifique os logs.")

    print("\nVerificação de versões (após tentativa de instalação):")
    verify_installed_versions(libs)


def verify_installed_versions(libs_to_check):
    """
    Verifica as versões das bibliotecas instaladas usando packaging.version para comparações robustas.
    """
    from packaging.version import parse as parse_version
    try:
        # Usar py -m pip para consistência com como o usuário está executando
        installed_packages_raw = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        installed_packages = {}
        for line in installed_packages_raw.decode().splitlines():
            if '==' in line:
                name, version = line.split('==', 1)
                installed_packages[name.lower()] = version
            # Poderia adicionar lógica para pacotes editáveis ou de URLs se necessário
    except Exception as e:
        print(f"Erro ao obter a lista de pacotes instalados: {e}")
        return

    print("\nComparando versões instaladas com as requeridas:")
    for lib_name_req, target_version_spec_str in libs_to_check.items():
        installed_version_str = installed_packages.get(lib_name_req.lower())
        
        if installed_version_str:
            installed_v = parse_version(installed_version_str)
            
            # Determinar operador e versão requerida
            if target_version_spec_str.startswith(">="):
                operator = ">="
                required_v_str = target_version_spec_str[2:]
            elif target_version_spec_str.startswith("=="):
                operator = "=="
                required_v_str = target_version_spec_str[2:]
            elif target_version_spec_str.startswith("<="):
                operator = "<="
                required_v_str = target_version_spec_str[2:]
            elif target_version_spec_str.startswith("<"):
                operator = "<"
                required_v_str = target_version_spec_str[1:]
            elif target_version_spec_str.startswith(">"):
                operator = ">"
                required_v_str = target_version_spec_str[1:]
            elif target_version_spec_str.startswith("!="):
                operator = "!="
                required_v_str = target_version_spec_str[2:]
            else: # Assume correspondência exata se nenhum operador for especificado
                operator = "=="
                required_v_str = target_version_spec_str
            
            required_v = parse_version(required_v_str)
            
            match = False
            if operator == ">=":
                match = installed_v >= required_v
            elif operator == "==":
                match = installed_v == required_v
            elif operator == "<=":
                match = installed_v <= required_v
            elif operator == "<":
                match = installed_v < required_v
            elif operator == ">":
                match = installed_v > required_v
            elif operator == "!=":
                match = installed_v != required_v
            
            if match:
                print(f"  {lib_name_req}: OK (Instalado: {installed_v}, Requerido: {target_version_spec_str})")
            else:
                print(f"  {lib_name_req}: ATENÇÃO - Versão Incompatível (Instalado: {installed_v}, Requerido: {target_version_spec_str})")
        else:
            print(f"  {lib_name_req}: NÃO ENCONTRADO (Requerido: {target_version_spec_str})")


if __name__ == "__main__":
    print("="*50)
    print(" Fase 1: Script de Instalação e Verificação de Dependências")
    print("="*50)
    install_and_verify_libraries(REQUIRED_LIBS)
    print("\nLembre-se de gerar o `requirements.txt` após confirmar as instalações (Fase 1.3).")
    print("Você pode fazer isso com: py -m pip freeze > requirements.txt")