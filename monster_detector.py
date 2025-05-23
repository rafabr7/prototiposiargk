import cv2
import os
import numpy as np
from collections import defaultdict
import time # Adicionado para controle de FPS no teste
import shutil # Adicionado para limpar pasta de teste

# Tentativa de importação dos módulos de screen_capture
try:
    from screen_capture import MSSCapturer, select_and_configure_capture_region, configure_captura, stop_active_capturer
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    print("AVISO: Módulo 'screen_capture' não encontrado ou incompleto. O teste de integração com captura de tela será desabilitado.")
    SCREEN_CAPTURE_AVAILABLE = False
    # Definir classes e funções dummy para evitar erros no if __name__ se o import falhar
    class MSSCapturer:
        def __init__(self, monitor=None): pass # Adicionado monitor como opcional
        def get_frame(self): return None
        def close(self): pass
        def set_region(self, x,y,w,h): pass # Adicionado para compatibilidade dummy

    def configure_captura(backend_choice="mss", target_fps=30, device_idx=0, output_idx=0):
        print("Dummy configure_captura chamada.")
        if backend_choice == "mss":
            return MSSCapturer() # Retorna uma instância dummy
        return None
        
    def select_and_configure_capture_region(capturer_instance_arg, window_title_hint=None):
        print("Dummy select_and_configure_capture_region chamada.")
        return None, "Dummy Window" # Retorna (None para região), string para título

    def stop_active_capturer():
        print("Dummy stop_active_capturer chamada.")

class MonsterDetector:
    def __init__(self, pasta_sprites: str):
        """
        Inicializa o detector de monstros.

        Args:
            pasta_sprites: O caminho para a pasta principal contendo subpastas de monstros.
                           Cada subpasta deve ser nomeada com o nome do monstro e conter
                           arquivos PNG de seus sprites.
                           Ex: monster_sprites/Zombie/Zombie_A.png
        """
        self.pasta_sprites = pasta_sprites
        self.templates = {}  # Dicionário: {"NomeMonstro": [template1_img, template2_img, ...]}}
        self.template_filenames = {} # Dicionário: {"NomeMonstro": [filename1, filename2, ...]} para debug
        self._cache_loaded = False
        
        self.carregar_templates()

    def carregar_templates(self, forcar_recarregar: bool = False):
        """
        Carrega todos os arquivos PNG das subpastas de monstros na pasta de sprites especificada.
        Os templates são agrupados pelo nome da subpasta (nome do monstro).
        Implementa um cache simples para evitar recarregamentos desnecessários.

        Args:
            forcar_recarregar: Se True, ignora o cache e recarrega todos os templates.
        """
        if self._cache_loaded and not forcar_recarregar:
            print("Templates já carregados do cache.")
            return

        print(f"Carregando templates da pasta principal de sprites: {self.pasta_sprites}...")
        
        loaded_templates = defaultdict(list)
        loaded_filenames = defaultdict(list)

        if not os.path.isdir(self.pasta_sprites):
            print(f"ERRO: Pasta principal de sprites '{self.pasta_sprites}' não encontrada.")
            self._cache_loaded = False
            self.templates = {}
            self.template_filenames = {}
            return

        for nome_pasta_monstro in os.listdir(self.pasta_sprites):
            caminho_pasta_monstro = os.path.join(self.pasta_sprites, nome_pasta_monstro)
            
            if os.path.isdir(caminho_pasta_monstro):
                nome_base_monstro = nome_pasta_monstro # Nome da subpasta é o nome do monstro
                print(f"  Analisando pasta do monstro: '{nome_base_monstro}' em '{caminho_pasta_monstro}'")
                
                arquivos_png_encontrados = 0
                for nome_arquivo_sprite in os.listdir(caminho_pasta_monstro):
                    if nome_arquivo_sprite.lower().endswith(".png"):
                        caminho_completo_sprite = os.path.join(caminho_pasta_monstro, nome_arquivo_sprite)
                        try:
                            # Carregar diretamente em escala de cinza
                            template_img = cv2.imread(caminho_completo_sprite, cv2.IMREAD_GRAYSCALE) 
                            
                            if template_img is None:
                                print(f"    AVISO: Não foi possível carregar a imagem: {caminho_completo_sprite}")
                                continue
                            
                            loaded_templates[nome_base_monstro].append(template_img)
                            # Armazenar apenas o nome do arquivo para template_filenames, para consistência com a saída
                            loaded_filenames[nome_base_monstro].append(nome_arquivo_sprite) 
                            print(f"      Template carregado: '{nome_arquivo_sprite}' para o monstro '{nome_base_monstro}'")
                            arquivos_png_encontrados +=1

                        except Exception as e:
                            print(f"    ERRO ao carregar o template '{nome_arquivo_sprite}' de '{caminho_pasta_monstro}': {e}")
                if arquivos_png_encontrados == 0:
                    print(f"    AVISO: Nenhum arquivo PNG encontrado na pasta do monstro '{nome_base_monstro}'.")
            # else: (opcional)
            #     print(f"  Item ignorado (não é uma pasta): {nome_pasta_monstro}")
        
        self.templates = dict(loaded_templates)
        self.template_filenames = dict(loaded_filenames)
        
        if not self.templates:
            print("Nenhum template foi carregado. Verifique as subpastas de monstros e os arquivos PNG dentro delas.")
        else:
            print(f"Total de {sum(len(v) for v in self.templates.values())} templates carregados para {len(self.templates)} tipos de monstros.")
            for nome_monstro, sprites in self.templates.items():
                print(f"  - Monstro '{nome_monstro}': {len(sprites)} sprite(s)")
                # for i, filename in enumerate(self.template_filenames[nome_monstro]):
                # print(f"    - Sprite {i+1}: {filename}")


        self._cache_loaded = True

    def detectar_monstros(self, frame: np.ndarray, threshold: float = 0.8, monstros_alvo: list[str] | None = None) -> list:
        """
        Detecta monstros em um frame de imagem usando os templates carregados.

        Args:
            frame: O frame da tela (imagem NumPy BGR) onde procurar os monstros.
            threshold: O limiar de confiança para considerar uma detecção válida (0.0 a 1.0).
            monstros_alvo: Uma lista opcional de nomes de monstros para focar a detecção.
                             Se None, procura todos os monstros com templates carregados.

        Returns:
            Uma lista de dicionários, onde cada dicionário representa um monstro detectado.
            Ex: [{"nome": "Poring", "regiao": (x, y, w, h), "confianca": 0.92, "sprite_usado": "Poring_Sprit_1.png"}, ...]
        """
        detections = []
        
        if not self.templates:
            print("Nenhum template carregado. Não é possível detectar monstros.")
            return detections

        # Converte o frame para escala de cinza para a detecção
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        monstros_a_procurar = {}
        if monstros_alvo:
            for nome_monstro in monstros_alvo:
                if nome_monstro in self.templates:
                    monstros_a_procurar[nome_monstro] = self.templates[nome_monstro]
                else:
                    print(f"AVISO: Monstro alvo '{nome_monstro}' não encontrado nos templates carregados.")
        else:
            # Se nenhum monstro alvo específico for fornecido, procura todos os monstros carregados
            monstros_a_procurar = self.templates

        if not monstros_a_procurar:
            print("Nenhum monstro selecionado ou válido para detecção.")
            return detections

        for nome_monstro, lista_templates_img in monstros_a_procurar.items():
            for i, template_img_gray in enumerate(lista_templates_img):
                # template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY) # Não é mais necessário, já carregamos em cinza
                # w, h = template_gray.shape[::-1] # Largura e altura do template em escala de cinza
                
                if template_img_gray is None or template_img_gray.size == 0:
                    print(f"AVISO: Template (gray) para {nome_monstro} (índice {i}) está vazio ou inválido.")
                    continue

                # Verificar se o frame_gray tem dimensões suficientes para o template_img_gray
                if frame_gray.shape[0] < template_img_gray.shape[0] or frame_gray.shape[1] < template_img_gray.shape[1]:
                    # print(f"AVISO: Frame (gray) ({frame_gray.shape}) é menor que o template {self.template_filenames[nome_monstro][i]} ({template_img_gray.shape}). Pulando.")
                    continue

                w, h = template_img_gray.shape[1], template_img_gray.shape[0] # Em escala de cinza, shape é (altura, largura)

                try:
                    # Realizar matchTemplate com o frame em escala de cinza e o template em escala de cinza
                    res = cv2.matchTemplate(frame_gray, template_img_gray, cv2.TM_CCOEFF_NORMED)
                except cv2.error as e:
                    # print(f"Erro no cv2.matchTemplate para {self.template_filenames[nome_monstro][i]} (gray): {e}")
                    continue

                # Encontra locais com score acima do threshold
                loc = np.where(res >= threshold)
                
                # O resultado de np.where é uma tupla de arrays (um para y, um para x)
                # Iteramos sobre os pontos encontrados
                for pt in zip(*loc[::-1]): # pt é (x, y)
                    confianca = res[pt[1], pt[0]] # Acessa o valor de confiança em res[y, x]
                    detections.append({
                        "nome": nome_monstro,
                        "regiao": (pt[0], pt[1], w, h), # (x, y, largura, altura)
                        "confianca": float(confianca),
                        "sprite_usado": self.template_filenames[nome_monstro][i]
                    })
        
        # Opcional: aplicar Non-Maximum Suppression (NMS) para remover detecções sobrepostas.
        # Por enquanto, vamos retornar todas as detecções acima do threshold.
        # Se houver muitas detecções redundantes, NMS pode ser adicionado aqui.

        if detections:
            # Ordenar por confiança (opcional, mas pode ser útil)
            detections.sort(key=lambda d: d["confianca"], reverse=True)
            # print(f"Detectados {len(detections)} monstros.")
        # else:
            # print("Nenhum monstro detectado no frame com o threshold especificado.")

        return detections


# --- Exemplo de Uso (para teste do carregamento e DETECÇÃO EM TEMPO REAL) ---
if __name__ == "__main__":
    print("Iniciando teste do MonsterDetector...")
    
    # --- Configuração da Pasta de Sprites ---
    # Esta é a pasta principal onde você deve organizar os sprites dos monstros.
    # Dentro desta pasta, crie subpastas com o nome de cada monstro.
    # Ex: monster_sprites/Zombie/contem_sprites_do_zombie.png
    sprites_dir_base = "monster_sprites" 
    print(f"ATTENÇÃO: O detector tentará carregar sprites da pasta: '{os.path.abspath(sprites_dir_base)}'")
    print(f"Certifique-se que esta pasta exista e contenha subpastas para cada monstro com seus sprites PNG.")
    print(f"Exemplo de estrutura esperada:")
    print(f"- {sprites_dir_base}/")
    print(f"  - Zombie/  <-- Subpasta com nome do monstro")
    print(f"    - zombie_frente.png")
    print(f"    - zombie_lado.png")
    print(f"  - Poring/ ")
    print(f"    - poring_normal.png")
    print("-----------------------------------------")

    # Não há mais criação automática de pastas ou sprites de placeholder.
    # O detector agora depende dos sprites fornecidos pelo usuário na pasta especificada.
    
    detector = MonsterDetector(pasta_sprites=sprites_dir_base)

    if not detector.templates:
        print(f"\nNENHUM TEMPLATE FOI CARREGADO da pasta '{sprites_dir_base}'.")
        print("Verifique se a pasta existe, se contém subpastas de monstros (ex: Zombie), e se essas subpastas contêm arquivos PNG.")
        if not SCREEN_CAPTURE_AVAILABLE:
            print("E o módulo screen_capture não está disponível ou completo.")
        exit()
    else:
        print(f"\nTotal de {sum(len(v) for v in detector.templates.values())} templates carregados para {len(detector.templates)} tipos de monstros:")
        for nome_monstro, lista_sprites in detector.templates.items():
            print(f"  - Monstro '{nome_monstro}': {len(lista_sprites)} sprite(s) carregado(s).")

    print("\nTemplates carregados. Prosseguindo para configuração da captura de tela (se disponível).")

    capturer_instance = None 
    if SCREEN_CAPTURE_AVAILABLE:
        print("\n--- INICIANDO TESTE DE INTEGRAÇÃO COM SCREEN_CAPTURE (Focando em 'Zombie') ---")
        
        capturer_instance = configure_captura(backend_choice="mss", target_fps=15)

        if capturer_instance:
            selected_region_dict, target_window_title = select_and_configure_capture_region(capturer=capturer_instance)

            if selected_region_dict and target_window_title:
                print(f"Captura configurada para a janela: '{target_window_title}' com região: {selected_region_dict}")
                print("Pressione 'q' na janela de visualização para sair.")
                
                target_fps = 15 
                delay_per_frame = 1.0 / target_fps
                
                try:
                    while True:
                        start_time = time.time()
                        raw_frame = capturer_instance.capture_frame()
                        if raw_frame is None:
                            print("Não foi possível capturar o frame. A janela foi fechada ou minimizada?")
                            break 

                        # Garante que temos uma cópia BGR contígua para desenho e display
                        # A maioria dos capturadores já retorna BGR, mas a contiguidade pode ser um problema.
                        # O .copy() geralmente resolve isso.
                        frame_for_display = raw_frame.copy()

                        # A detecção pode operar em uma cópia separada ou na mesma se não for modificada
                        # Se detectar_monstros não modificar frame_para_detectar, podemos usar frame_for_display
                        frame_para_detectar = frame_for_display.copy() # Ou raw_frame.copy() se preferir
                        
                        # Detectar APENAS Zombie (ou o monstro que você configurou os sprites)
                        detections = detector.detectar_monstros(frame_para_detectar, threshold=0.4, monstros_alvo=["Zombie"]) 

                        if detections:
                            print(f"Detectado(s) {len(detections)} monstro(s) 'Zombie' no frame atual:")
                        for d in detections:
                            nome = d['nome']
                            x, y, w, h = d['regiao']
                            conf = d['confianca']
                            sprite_usado = d['sprite_usado']
                            pt1 = (x, y)
                            pt2 = (x + w, y + h)
                            # Desenhar na cópia feita para display
                            cv2.rectangle(frame_for_display, pt1, pt2, (0, 0, 255), 2) 
                            label = f"{nome} ({conf:.2f})"
                            cv2.putText(frame_for_display, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            print(f"  - {nome} (sprite: {sprite_usado}) @ ({x},{y},{w},{h}) com conf={conf:.2f}")

                        cv2.imshow(f"Detecção em Tempo Real - Focando em Zombie - {target_window_title}", frame_for_display)

                        elapsed_time = time.time() - start_time
                        sleep_time = delay_per_frame - elapsed_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("Tecla 'q' pressionada. Encerrando a visualização.")
                            break
                
                except KeyboardInterrupt:
                    print("Interrupção pelo usuário. Encerrando.")
                finally:
                    if SCREEN_CAPTURE_AVAILABLE:
                        stop_active_capturer() 
                    cv2.destroyAllWindows()
                    print("Recursos de captura e janelas liberados.")
            else:
                print("Seleção de janela cancelada ou falhou. O teste de integração não será executado.")
                if SCREEN_CAPTURE_AVAILABLE:
                    stop_active_capturer() 
        else:
            print("Falha ao criar a instância do capturador (MSS). O teste de integração não será executado.")
    else:
        print("\nAVISO: Módulo 'screen_capture' não disponível. Pulando teste de integração com captura de tela.")
        print("Executando teste de detecção para Zombie em frame dummy (usando sprites de 'monster_sprites/Zombie/')...")
        
        dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8) + 200 
        nome_monstro_teste_detect = "Zombie"  
        sprite_para_inserir_no_dummy = None
        nome_arquivo_sprite_inserido = ""

        # Tentar carregar um sprite real do Zombie para inserir no dummy frame
        # Isso só funcionará se os templates foram carregados com sucesso anteriormente
        if nome_monstro_teste_detect in detector.templates and detector.templates[nome_monstro_teste_detect]:
            if detector.templates[nome_monstro_teste_detect]: # Verifica se a lista de sprites não está vazia
                 sprite_para_inserir_no_dummy = detector.templates[nome_monstro_teste_detect][0]
                 nome_arquivo_sprite_inserido = detector.template_filenames[nome_monstro_teste_detect][0]
            
            if sprite_para_inserir_no_dummy is not None:
                h_sprite, w_sprite = sprite_para_inserir_no_dummy.shape[:2]
                pos_x, pos_y = 100, 150
                if pos_y + h_sprite <= dummy_frame.shape[0] and pos_x + w_sprite <= dummy_frame.shape[1]:
                    dummy_frame[pos_y:pos_y+h_sprite, pos_x:pos_x+w_sprite] = sprite_para_inserir_no_dummy
                    print(f"Sprite real '{nome_arquivo_sprite_inserido}' de '{nome_monstro_teste_detect}' inserido no frame dummy em ({pos_x}, {pos_y})")
                else:
                    print(f"Não foi possível inserir o sprite '{nome_arquivo_sprite_inserido}' de '{nome_monstro_teste_detect}' no frame dummy (dimensões excedem).")
            else:
                print(f"Nenhum sprite encontrado para '{nome_monstro_teste_detect}' nos templates carregados para inserir no dummy frame. O dummy frame estará vazio.")
        else:
            print(f"Monstro '{nome_monstro_teste_detect}' não encontrado nos templates carregados (pasta '{sprites_dir_base}/{nome_monstro_teste_detect}' vazia ou inexistente?). Não é possível popular o dummy frame.")
                
        deteccoes_dummy = detector.detectar_monstros(dummy_frame, threshold=0.7, monstros_alvo=[nome_monstro_teste_detect])
        if deteccoes_dummy:
            print(f"Detectados em dummy frame ({len(deteccoes_dummy)}):")
            for d in deteccoes_dummy: 
                print(f"  - {d['nome']} (sprite: {d['sprite_usado']}) @ {d['regiao']} conf {d['confianca']:.2f}")
                x,y,w,h = d['regiao']
                cv2.rectangle(dummy_frame, (x,y), (x+w,y+h), (0,0,255), 2)
            cv2.imshow("Dummy Frame com Deteccao de Zombie", dummy_frame)
            print("Pressione qualquer tecla na janela do dummy frame para fechar.")
            cv2.waitKey(0)
            cv2.destroyWindow("Dummy Frame com Deteccao de Zombie")
        else:
            print(f"Nenhum monstro '{nome_monstro_teste_detect}' detectado no dummy frame.")

    print("\nTeste do MonsterDetector finalizado.") 