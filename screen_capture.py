import abc
import time
import mss
import numpy as np
import dxcam # type: ignore # DXcam pode não ter stubs de tipo perfeitos
import pygetwindow # Adicionado para calibração de janela

class ScreenCapturerBase(abc.ABC):
    """
    Classe base abstrata para capturadores de tela.
    Define a interface comum para diferentes métodos de captura.
    """
    def __init__(self, target_fps: int = 30):
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps if target_fps > 0 else 0
        self._running = False
        self.region = {"top": 0, "left": 0, "width": 0, "height": 0} # Formato MSS

    @abc.abstractmethod
    def start(self):
        """Inicia o capturador (se necessário)."""
        self._running = True

    @abc.abstractmethod
    def stop(self):
        """Para o capturador (se necessário)."""
        self._running = False

    @abc.abstractmethod
    def set_region(self, x: int, y: int, width: int, height: int):
        """Define a região de captura."""
        self.region = {"top": y, "left": x, "width": width, "height": height}

    @abc.abstractmethod
    def capture_frame(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray | None:
        """
        Captura um único frame da região especificada ou da região padrão.
        A região é (x, y, largura, altura).
        Retorna um array numpy (BGR por padrão para OpenCV) ou None se falhar.
        """
        pass

    def get_actual_fps(self) -> float:
        """Retorna o FPS real (pode ser implementado por subclasses)."""
        return 0.0

    def is_running(self) -> bool:
        return self._running

class MSSCapturer(ScreenCapturerBase):
    """Capturador de tela usando a biblioteca MSS."""
    def __init__(self, target_fps: int = 30):
        super().__init__(target_fps)
        self.sct = None

    def start(self):
        try:
            self.sct = mss.mss()
            super().start()
            print("MSS Capturer iniciado.")
        except Exception as e:
            print(f"Erro ao iniciar MSS Capturer: {e}")
            self._running = False

    def stop(self):
        if self.sct:
            self.sct.close()
            self.sct = None
        super().stop()
        print("MSS Capturer parado.")

    def set_region(self, x: int, y: int, width: int, height: int):
        if width <= 0 or height <= 0:
            print(f"Erro: Região de captura inválida para MSS: w={width}, h={height}")
            return
        super().set_region(x, y, width, height)
        # print(f"MSS region set to: {self.region}")


    def capture_frame(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray | None:
        if not self.is_running() or not self.sct:
            # print("MSS Capturer não está rodando ou não inicializado.")
            return None

        capture_region = self.region
        if region:
            if region[2] <=0 or region[3] <=0: # width or height
                # print(f"Região de captura inválida fornecida para MSS: {region}")
                return None
            capture_region = {"top": region[1], "left": region[0], "width": region[2], "height": region[3]}
        
        if not capture_region or capture_region["width"] <= 0 or capture_region["height"] <= 0:
            # print(f"Tentativa de capturar com região inválida ou não definida: {capture_region}")
            return None

        try:
            sct_img = self.sct.grab(capture_region)
            # Converter para array numpy BGR
            img = np.array(sct_img)
            img = img[:, :, :3] # Remover canal alfa se existir (BGRA -> BGR)
            return img
        except mss.exception.ScreenShotError as e:
            # Comum se a região for inválida (ex: fora da tela) ou a janela não existir mais.
            # print(f"MSS ScreenShotError: {e}. Verifique a região de captura: {capture_region}")
            return None
        except Exception as e:
            print(f"Erro ao capturar frame com MSS: {e}")
            return None

class DXCamCapturer(ScreenCapturerBase):
    """Capturador de tela usando a biblioteca DXcam."""
    def __init__(self, target_fps: int = 30, device_idx: int = 0, output_idx: int = 0):
        super().__init__(target_fps)
        self.camera: dxcam.DXCamera | None = None
        self.device_idx = device_idx
        self.output_idx = output_idx
        self._region_for_dxcam: tuple[int, int, int, int] | None = None # left, top, right, bottom

    def start(self):
        try:
            # DXcam lida com FPS internamente se especificado na captura.
            # O construtor do DXCamera não leva FPS diretamente, é no grab.
            self.camera = dxcam.create(device_idx=self.device_idx, output_idx=self.output_idx)
            if self.camera is None:
                 raise Exception("Falha ao criar instância DXCamera (dxcam.create retornou None)")
            # DXcam não tem um método start explícito como o MSS para o objeto mss() em si,
            # mas podemos considerar "iniciado" quando o objeto camera existe.
            # A captura real é iniciada com camera.start_video_capture ou frame a frame com grab.
            # Para consistência com ScreenCapturerBase, vamos usar grab por enquanto.
            super().start()
            print(f"DXCam Capturer pronto. Device: {self.device_idx}, Output: {self.output_idx}")
        except Exception as e:
            print(f"Erro ao iniciar DXCam Capturer: {e}")
            self._running = False
            if self.camera:
                try:
                    self.camera.release() # Garante que a câmera seja liberada
                except Exception as e_release:
                    print(f"Erro ao tentar liberar câmera DXcam: {e_release}")
                self.camera = None


    def stop(self):
        if self.camera:
            try:
                # Se estivéssemos usando start_video_capture(), chamaríamos stop_video_capture() aqui.
                # Como estamos usando grab(), apenas liberar a câmera é suficiente.
                self.camera.release()
            except Exception as e:
                 print(f"Erro ao liberar câmera DXcam: {e}")
            self.camera = None
        super().stop()
        print("DXCam Capturer parado.")

    def set_region(self, x: int, y: int, width: int, height: int):
        if width <= 0 or height <= 0:
            print(f"Erro: Região de captura inválida para DXCam: w={width}, h={height}")
            return
        super().set_region(x, y, width, height) # Armazena no formato MSS
        # DXcam espera (left, top, right, bottom)
        self._region_for_dxcam = (x, y, x + width, y + height)
        # print(f"DXCam internal region set to: {self._region_for_dxcam}")


    def capture_frame(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray | None:
        if not self.is_running() or not self.camera:
            # print("DXCam Capturer não está rodando ou não inicializado.")
            return None

        dxcam_region_to_capture = self._region_for_dxcam
        if region: # Formato (x, y, w, h)
            if region[2] <=0 or region[3] <=0:
                # print(f"Região de captura inválida fornecida para DXCam: {region}")
                return None
            dxcam_region_to_capture = (region[0], region[1], region[0] + region[2], region[1] + region[3])

        if not dxcam_region_to_capture:
            # print(f"Tentativa de capturar com DXCam sem região definida: {dxcam_region_to_capture}")
            return None
            
        try:
            # DXcam retorna None se a região for inválida (ex: totalmente fora da tela)
            frame = self.camera.grab(region=dxcam_region_to_capture)
            if frame is not None:
                # DXcam já retorna um array numpy BGR, então nenhuma conversão é necessária.
                return frame
            else:
                # print(f"DXcam.grab() retornou None para a região {dxcam_region_to_capture}. A região pode ser inválida ou a janela não visível.")
                return None
        except Exception as e:
            # DXcam pode lançar exceções se houver problemas com o dispositivo DirectX
            print(f"Erro ao capturar frame com DXCam: {e}")
            # Em caso de erro grave, pode ser útil tentar reiniciar a câmera.
            # self.stop()
            # self.start() # Cuidado com recursão ou loops de falha aqui
            return None

# --- Função de Configuração ---
_active_capturer: ScreenCapturerBase | None = None

def configure_captura(
    backend_choice: str = "dxcam", 
    target_fps: int = 30,
    device_idx: int = 0, # Para DXCam
    output_idx: int = 0  # Para DXCam
) -> ScreenCapturerBase | None:
    """
    Configura e retorna um objeto de captura de tela.

    Args:
        backend_choice: "mss" ou "dxcam".
        target_fps: FPS desejado para a captura.
        device_idx: Índice do dispositivo GPU para DXCam.
        output_idx: Índice do monitor conectado à GPU para DXCam.

    Returns:
        Uma instância de ScreenCapturerBase ou None se a configuração falhar.
    """
    global _active_capturer

    if _active_capturer and _active_capturer.is_running():
        print("Um capturador já está ativo. Parando o anterior...")
        _active_capturer.stop()
        _active_capturer = None

    print(f"Configurando captura com backend: {backend_choice}, FPS alvo: {target_fps}")

    capturer: ScreenCapturerBase | None = None
    if backend_choice.lower() == "mss":
        capturer = MSSCapturer(target_fps=target_fps)
    elif backend_choice.lower() == "dxcam":
        capturer = DXCamCapturer(target_fps=target_fps, device_idx=device_idx, output_idx=output_idx)
    else:
        print(f"Backend de captura desconhecido: {backend_choice}. Escolha 'mss' ou 'dxcam'.")
        return None

    capturer.start()
    if not capturer.is_running():
        print(f"Falha ao iniciar o capturador {backend_choice}.")
        return None
    
    _active_capturer = capturer
    print(f"Capturador {backend_choice} configurado e iniciado.")
    return _active_capturer

def get_active_capturer() -> ScreenCapturerBase | None:
    """Retorna o capturador ativo global."""
    return _active_capturer

def stop_active_capturer():
    """Para o capturador ativo global, se existir."""
    global _active_capturer
    if _active_capturer and _active_capturer.is_running():
        _active_capturer.stop()
        print("Capturador ativo parado.")
    _active_capturer = None

# --- Funções de Calibração e Configuração de Região ---

def select_and_configure_capture_region(capturer: ScreenCapturerBase | None) -> tuple[dict | None, str | None]:
    """
    Permite ao usuário selecionar uma janela aberta para definir a região de captura.
    Configura o capturador fornecido com a região da janela selecionada.

    Args:
        capturer: A instância do capturador de tela a ser configurada.

    Returns:
        Uma tupla contendo:
        - Um dicionário com as coordenadas da região no formato MSS 
          (e.g., {"top": y, "left": x, "width": w, "height": h}) ou None se falhar.
        - O título da janela selecionada (str) ou None se falhar/cancelado.
    """
    if not capturer:
        print("Erro: Nenhum capturador ativo para configurar a região.")
        return None, None

    print("\n--- Seleção de Janela para Captura ---")
    game_window_title: str | None = None # Para armazenar o título
    try:
        windows = pygetwindow.getAllWindows()
        if not windows:
            print("Nenhuma janela encontrada.")
            return None, None

        print("Janelas disponíveis:")
        available_windows = []
        for i, window in enumerate(windows):
            if window.title and window.width > 0 and window.height > 0:
                available_windows.append(window)
                print(f"  {len(available_windows)}: \"{window.title}\" (ID: {window._hWnd}, Tamanho: {window.width}x{window.height})")
        
        if not available_windows:
            print("Nenhuma janela com título e dimensões válidas encontrada.")
            return None, None

        while True:
            try:
                choice_str = input(f"Digite o número da janela para capturar (1-{len(available_windows)}, ou '0' para cancelar): ")
                choice = int(choice_str)
                if choice == 0:
                    print("Seleção de janela cancelada.")
                    return None, None
                if 1 <= choice <= len(available_windows):
                    game_window = available_windows[choice - 1]
                    game_window_title = game_window.title # Armazena o título
                    break
                else:
                    print(f"Escolha inválida. Por favor, digite um número entre 1 e {len(available_windows)} (ou 0).")
            except ValueError:
                print("Entrada inválida. Por favor, digite um número.")
            except IndexError:
                 print("Número fora do alcance das janelas listadas. Tente novamente.")

        print(f"Janela selecionada: \"{game_window.title}\"")
        x, y, w, h = game_window.left, game_window.top, game_window.width, game_window.height
        
        if w <= 0 or h <= 0:
            print(f"Erro: A janela selecionada \"{game_window.title}\" tem dimensões inválidas (largura ou altura <= 0).")
            return None, game_window_title # Retorna título mesmo em falha de dimensão

        print(f"Configurando região de captura para: x={x}, y={y}, largura={w}, altura={h}")
        capturer.set_region(x, y, w, h)
        
        if capturer.region["width"] == w and capturer.region["height"] == h:
            print("Região de captura configurada com sucesso no capturador.")
            return {"top": y, "left": x, "width": w, "height": h}, game_window_title
        else:
            print("Falha ao configurar a região no capturador.")
            return None, game_window_title

    except pygetwindow.PyGetWindowException as e:
        print(f"Erro com PyGetWindow: {e}")
        return None, None
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a seleção da janela: {e}")
        return None, None

# --- Exemplo de Uso (para teste) ---
if __name__ == "__main__":
    print("Iniciando teste de captura de tela...")
    
    captador = configure_captura(backend_choice="mss", target_fps=30)
    target_window_title: str | None = None

    if captador:
        selected_region_info, target_window_title = select_and_configure_capture_region(captador)

        if selected_region_info and target_window_title:
            print(f"Região selecionada e configurada para janela '{target_window_title}': {selected_region_info}")
            
            print(f"Capturador ativo: {type(captador).__name__}")
            print(f"FPS alvo: {captador.target_fps}")
            
            import cv2 
            try:
                cv2.namedWindow("Teste Captura Calibrada", cv2.WINDOW_NORMAL)
            except cv2.error as e:
                print(f"Erro ao criar janela OpenCV: {e}.")
                if captador: captador.stop()
                exit()

            start_time = time.time()
            frames_captured = 0
            check_interval = 30 # Verificar estado da janela a cada X frames
            max_frames_to_test = 300 # Aumentado para dar mais tempo para o teste de janela

            while frames_captured < max_frames_to_test and captador.is_running():
                loop_start_time = time.time()

                # Verificação periódica da janela alvo
                if frames_captured > 0 and frames_captured % check_interval == 0:
                    try:
                        target_windows = pygetwindow.getWindowsWithTitle(target_window_title)
                        if not target_windows:
                            print(f"AVISO: Janela '{target_window_title}' não encontrada. Parando captura.")
                            break
                        current_target_window = target_windows[0]
                        if not current_target_window.visible or current_target_window.isMinimized:
                            print(f"AVISO: Janela '{target_window_title}' não está visível ou está minimizada. Parando captura.")
                            break
                        # Opcional: Verificar se a posição/tamanho mudou e recalibrar ou avisar
                        # if current_target_window.left != selected_region_info["left"] or \
                        #    current_target_window.top != selected_region_info["top"]:
                        #     print(f"AVISO: Posição da janela '{target_window_title}' mudou.")
                            # Poderia tentar recalibrar aqui
                    except Exception as e_check:
                        print(f"Erro ao verificar estado da janela '{target_window_title}': {e_check}")
                        # Decidir se continua ou para em caso de erro na verificação
                        # break 

                frame = captador.capture_frame() 
                
                if frame is not None and frame.size > 0:
                    frames_captured += 1
                    cv2.imshow("Teste Captura Calibrada", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Tecla 'q' pressionada, parando...")
                        break
                elif not captador.is_running(): # Se o captador parou por algum motivo interno
                    print("Capturador parou inesperadamente.")
                    break
                # else: # Frame None ou vazio, não necessariamente um erro fatal se a janela ainda estiver ok
                    # time.sleep(0.01) 

                if captador.frame_time > 0:
                    elapsed_time = time.time() - loop_start_time
                    sleep_time = captador.frame_time - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            
            end_time = time.time()
            total_time = end_time - start_time if start_time else 0
            actual_fps = frames_captured / total_time if total_time > 0 else 0
            
            print(f"Teste concluído. {frames_captured} frames capturados em {total_time:.2f} segundos.")
            print(f"FPS real médio: {actual_fps:.2f} FPS")

            cv2.destroyAllWindows()
        else:
            print("Nenhuma região de captura foi configurada ou título da janela não obtido.")
        
        if captador and captador.is_running(): 
            captador.stop() 
    else:
        print("Falha ao configurar o capturador inicial.")

    print("Teste de captura de tela finalizado.") 