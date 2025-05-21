import cv2
import os
import numpy as np
from collections import defaultdict
import time # Adicionado para controle de FPS no teste
import shutil # Adicionado para limpar pasta de teste

# Tentativa de importação dos módulos de screen_capture
try:
    from screen_capture import MSSCapturer, select_and_configure_capture_region
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    print("AVISO: Módulo 'screen_capture' não encontrado. O teste de integração com captura de tela será desabilitado.")
    SCREEN_CAPTURE_AVAILABLE = False
    # Definir classes e funções dummy para evitar erros no if __name__ se o import falhar
    class MSSCapturer:
        def __init__(self, monitor): pass
        def get_frame(self): return None
        def close(self): pass
    def select_and_configure_capture_region(): return None, None, None

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
                            template_img = cv2.imread(caminho_completo_sprite, cv2.IMREAD_COLOR) 
                            
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

        # Converte o frame para escala de cinza para a detecção, se os templates também forem em escala de cinza.
        # Se os templates forem coloridos, a conversão pode ser desnecessária ou até prejudicial.
        # Por agora, vamos assumir que os templates e o frame podem ser processados como estão (BGR).
        # frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Descomente se for usar templates em escala de cinza

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
            for i, template_img in enumerate(lista_templates_img):
                # template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY) # Se for usar escala de cinza
                # w, h = template_gray.shape[::-1] # Largura e altura do template em escala de cinza
                
                if template_img is None or template_img.size == 0:
                    print(f"AVISO: Template para {nome_monstro} (índice {i}) está vazio ou inválido.")
                    continue

                # Verificar se o frame tem dimensões suficientes para o template
                if frame.shape[0] < template_img.shape[0] or frame.shape[1] < template_img.shape[1]:
                    # print(f"AVISO: Frame ({frame.shape}) é menor que o template {self.template_filenames[nome_monstro][i]} ({template_img.shape}). Pulando.")
                    continue

                w, h = template_img.shape[1], template_img.shape[0] # Largura e altura do template colorido

                # Método de matching: cv2.TM_CCOEFF_NORMED é geralmente bom.
                # Outros métodos: TM_SQDIFF_NORMED (menor valor é melhor), TM_CCORR_NORMED.
                try:
                    res = cv2.matchTemplate(frame, template_img, cv2.TM_CCOEFF_NORMED)
                except cv2.error as e:
                    # Isso pode acontecer se, por exemplo, o template for maior que o frame
                    # print(f"Erro no cv2.matchTemplate para {self.template_filenames[nome_monstro][i]}: {e}")
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
    
    # Configuração e carregamento de templates (como antes)
    sprites_dir_base = "monster_sprites_hierarchical" 
    if os.path.exists(sprites_dir_base):
        shutil.rmtree(sprites_dir_base)
        print(f"Pasta de teste antiga '{sprites_dir_base}' removida.")
    os.makedirs(sprites_dir_base)
    print(f"Pasta de teste '{sprites_dir_base}' criada.")

    monstros_teste_data = {
        "Poring": ["Poring_normal.png", "Poring_hit.png"],
        "Zombie": ["Zombie_walk_1.png"],
        "EmptyMonster": []
    }

    print("\nCriando estrutura de pastas e sprites de placeholder:")
    for nome_monstro, sprite_files in monstros_teste_data.items():
        pasta_monstro_atual = os.path.join(sprites_dir_base, nome_monstro)
        os.makedirs(pasta_monstro_atual, exist_ok=True)
        print(f"  Pasta criada para '{nome_monstro}': {pasta_monstro_atual}")
        if not sprite_files:
            print(f"    Monstro '{nome_monstro}' não terá sprites de placeholder.")
            continue
        for sprite_filename in sprite_files:
            caminho_sprite_placeholder = os.path.join(pasta_monstro_atual, sprite_filename)
            placeholder_img = np.zeros((30 + len(nome_monstro) * 2, 30 + len(sprite_filename)*1, 3), dtype=np.uint8)
            if "Poring" in nome_monstro: placeholder_img[:,:,0] = 50 
            elif "Zombie" in nome_monstro: placeholder_img[:,:,1] = 70
            else: placeholder_img[:,:,2] = 90
            placeholder_img += len(sprite_filename) 
            try:
                cv2.imwrite(caminho_sprite_placeholder, placeholder_img)
                print(f"    Sprite placeholder '{sprite_filename}' criado em '{pasta_monstro_atual}'.")
            except Exception as e:
                print(f"    ERRO ao criar sprite placeholder '{sprite_filename}': {e}")
    
    detector = MonsterDetector(pasta_sprites=sprites_dir_base)

    if not detector.templates:
        print("\nNenhum template foi carregado. O teste de detecção em tempo real não pode prosseguir sem templates.")
        if not SCREEN_CAPTURE_AVAILABLE:
            print("E o módulo screen_capture não está disponível.")
        exit()

    print("\nTemplates carregados. Prosseguindo para configuração da captura de tela (se disponível).")

    if SCREEN_CAPTURE_AVAILABLE:
        print("\n--- INICIANDO TESTE DE INTEGRAÇÃO COM SCREEN_CAPTURE ---")
        target_window_title, monitor_info, capturer_instance = select_and_configure_capture_region(try_dxcam=False)

        if capturer_instance:
            print(f"Captura configurada para a janela: '{target_window_title}'")
            print("Pressione 'q' na janela de visualização para sair.")
            
            target_fps = 15 # FPS desejado para o loop de captura e detecção
            delay_per_frame = 1.0 / target_fps
            
            try:
                while True:
                    start_time = time.time()
                    
                    frame = capturer_instance.get_frame()
                    if frame is None:
                        print("Não foi possível capturar o frame. A janela foi fechada ou minimizada?")
                        # Tenta re-selecionar a janela ou aguarda um pouco.
                        # Para simplificar, vamos sair do loop por agora.
                        # Poderia adicionar uma lógica para tentar re-selecionar a janela aqui.
                        # capturer_instance.close()
                        # target_window_title, monitor_info, capturer_instance = select_and_configure_capture_region(try_dxcam=False)
                        # if not capturer_instance:
                        #     print("Não foi possível reconfigurar a captura. Encerrando.")
                        #     break
                        # continue
                        break 

                    # Redimensionar o frame para a detecção se ele for muito grande (opcional, pode ajudar na performance)
                    # frame_para_detectar = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))
                    frame_para_detectar = frame.copy() # Usar uma cópia para não desenhar no original antes da detecção

                    # Detectar todos os monstros (ou especificar monstros_alvo=['Poring', 'Zombie'] por exemplo)
                    detections = detector.detectar_monstros(frame_para_detectar, threshold=0.7) # Ajuste o threshold conforme necessário

                    # Desenhar retângulos nas detecções no frame original (para exibição)
                    if detections:
                        print(f"Detectado(s) {len(detections)} monstro(s) no frame atual:")
                    for d in detections:
                        nome = d['nome']
                        x, y, w, h = d['regiao']
                        conf = d['confianca']
                        sprite_usado = d['sprite_usado']
                        
                        # Coordenadas para o retângulo
                        pt1 = (x, y)
                        pt2 = (x + w, y + h)
                        cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 2)
                        
                        # Texto para a detecção
                        label = f"{nome} ({conf:.2f})"
                        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        print(f"  - {nome} (sprite: {sprite_usado}) @ ({x},{y},{w},{h}) com conf={conf:.2f}")

                    cv2.imshow(f"Detecção em Tempo Real - {target_window_title}", frame)

                    # Calcular tempo para manter o FPS
                    elapsed_time = time.time() - start_time
                    sleep_time = delay_per_frame - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                    # Atual FPS (informativo)
                    actual_fps = 1.0 / (time.time() - start_time)
                    # print(f"FPS Atual: {actual_fps:.2f}") # Descomente para ver FPS no console

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Tecla 'q' pressionada. Encerrando a visualização.")
                        break
            
            except KeyboardInterrupt:
                print("Interrupção pelo usuário. Encerrando.")
            finally:
                if capturer_instance:
                    capturer_instance.close()
                cv2.destroyAllWindows()
                print("Recursos de captura e janelas liberados.")
        else:
            print("Não foi possível configurar a captura de tela. O teste de integração não será executado.")
    else:
        print("\nAVISO: Módulo 'screen_capture' não disponível. Pulando teste de integração com captura de tela.")
        print("Execute o teste de carregamento de templates isoladamente se desejar.")
        # Bloco de teste original para apenas carregar e detectar em dummy_frame pode ser colocado aqui se necessário
        # Por exemplo, para testar monstros_alvo específicos com dummy_frame:
        print("\nExecutando teste de detecção em frame dummy (sem captura de tela)...")
        dummy_frame = np.zeros((600, 800, 3), dtype=np.uint8) + 200 
        nome_monstro_teste_detect = "Poring" 
        sprite_placeholder_para_detectar = None
        nome_arquivo_sprite_detectar = ""

        if nome_monstro_teste_detect in detector.templates and detector.templates[nome_monstro_teste_detect]:
            sprite_placeholder_para_detectar = detector.templates[nome_monstro_teste_detect][0]
            nome_arquivo_sprite_detectar = detector.template_filenames[nome_monstro_teste_detect][0]
            if sprite_placeholder_para_detectar is not None:
                h_sprite, w_sprite = sprite_placeholder_para_detectar.shape[:2]
                pos_x, pos_y = 100, 150
                if pos_y + h_sprite <= dummy_frame.shape[0] and pos_x + w_sprite <= dummy_frame.shape[1]:
                    dummy_frame[pos_y:pos_y+h_sprite, pos_x:pos_x+w_sprite] = sprite_placeholder_para_detectar
                    print(f"Sprite de '{nome_monstro_teste_detect}' ({nome_arquivo_sprite_detectar}) inserido no frame de dummy em ({pos_x}, {pos_y})")
                
        deteccoes_dummy = detector.detectar_monstros(dummy_frame, threshold=0.7, monstros_alvo=[nome_monstro_teste_detect])
        if deteccoes_dummy:
            print(f"Detectados em dummy frame ({len(deteccoes_dummy)}):")
            for d in deteccoes_dummy: print(f"  - {d['nome']} (sprite: {d['sprite_usado']}) @ {d['regiao']} conf {d['confianca']:.2f}")
        else:
            print(f"Nenhum monstro '{nome_monstro_teste_detect}' detectado no dummy frame.")


    print("\nTeste do MonsterDetector (com possível integração de captura) finalizado.") 