# Acompanhamento do Projeto: Bot de Automação para Ragnarok Online

## Contexto do Projeto

Desenvolvimento de um bot para Ragnarok Online utilizando Python, com foco em automação de tarefas, reconhecimento de monstros e interação humanizada para evitar detecção. O projeto será desenvolvido em fases, cobrindo desde a configuração inicial até testes e otimizações.

## Fases de Desenvolvimento e Lista de Tarefas

A seguir, as fases de desenvolvimento e suas respectivas tarefas. Marque as caixas de seleção (substituindo `[ ]` por `[x]`) à medida que cada tarefa for concluída e testada.

---

### Fase 1: Configuração Inicial
*   **Exigência:** Gerar código de instalação com verificação de versões.
    ```python
    # required_libs = {
    #     "mss": "9.0.0",
    #     "opencv-python-headless": "4.9.0",
    #     "pyautogui": "0.9.53",
    #     "human-mouse": "2.2.1",
    #     "pyHM": "3.7.0"
    # }
    ```
*   **Tarefas:**
    - [x] 1.1. Criar script de instalação automática com `pip install --upgrade`.
    - [x] 1.2. Implementar verificação de compatibilidade de versões das bibliotecas.
    - [x] 1.3. Gerar arquivo `requirements.txt` otimizado.
*   **Entregáveis Esperados:**
    - [x] Código Python comentado em português (`install_dependencies.py`).
    - [x] Exemplo de uso/implementação do script de instalação (execução via `py install_dependencies.py`).
    - [x] Arquivo `requirements.txt` gerado.
    - [ ] Técnicas anti-detecção específicas (se aplicável nesta fase).

---

### Fase 2: Sistema de Captura de Tela Adaptativo
*   **Exigência:** Implementar captura por região com fallback para DXcam (ou seleção de backend).
    ```python
    # def configurar_captura(modo_jogo: str):
    #     '''Suportar: Fullscreen | Janela | Borderless'''
    #     # Lógica de detecção automática de modo
    #     # Retornar objeto de captura configurado
    ```
*   **Requisitos:**
    - [x] 2.1. Implementar seletor automático de backend (MSS/DXcam) ou permitir escolha. (MSS implementado e funcional, DXCam adiado)
    - [x] 2.2. Desenvolver sistema de calibração dinâmica da região do jogo (seleção de janela e monitoramento básico).
    - [x] 2.3. Implementar taxa de captura ajustável (15-30 FPS) (estrutura básica implementada, otimização posterior).
*   **Entregáveis Esperados:**
    - [x] Código Python comentado em português (`screen_capture.py` com MSSCapturer, calibração e ajuste de FPS básico).
    - [x] Exemplo de uso/implementação da captura de tela (bloco `__main__` em `screen_capture.py`).
    - [ ] Arquivos de configuração relacionados (se houver) (Nenhum ainda para esta fase).
    - [ ] Técnicas anti-detecção específicas (ex: variação na taxa de captura se relevante).

---

### Fase 3: Motor de Reconhecimento de Monstros
*   **Exigência:** Sistema multi-template com threshold adaptativo.
    ```python
    # class MonsterDetector:
    #     def __init__(self, pasta_sprites: str):
    #         self.templates = self.carregar_templates(pasta_sprites)
        
    #     def carregar_templates(self, pasta: str) -> dict:
    #         # Carregar todos os PNGs da pasta de sprites
    #         # Retornar dicionário {nome: array}
    ```
*   **Especificações:**
    - [x] 3.1. Implementar pré-processamento de imagens (ex: normalização HSV, escala de cinza).
    - [x] 3.2. Desenvolver sistema de correspondência de templates (inicialmente simples com `cv2.matchTemplate`, com possibilidade de evolução para hierárquico).
    - [x] 3.3. Implementar cache de templates para performance (cache simples no carregamento).
    - [x] 3.4. Criar lógica para carregar templates de uma pasta de sprites (suporta subpastas por monstro).
*   **Entregáveis Esperados:**
    - [x] Código Python comentado em português (`monster_detector.py` com lógica de carregamento de subpastas e detecção).
    - [x] Exemplo de uso/implementação do detector de monstros (bloco `__main__` em `monster_detector.py` agora integrado com `screen_capture.py` para teste em tempo real).
    - [x] Pasta de exemplo com sprites/templates (criada dinamicamente pelo script de teste `monster_detector.py` como `monster_sprites_hierarchical`).
    - [ ] Técnicas anti-detecção específicas (ex: pequenas variações no pré-processamento).

---

### Fase 4: Controle Humanizado de Mouse
*   **Exigência:** Implementar movimentos Bézier com variação paramétrica.
    ```python
    # def mover_para(x: int, y: int, urgency: float = 0.5):
    #     '''
    #     urgency: 0.0 (lento/natural) a 1.0 (rápido/robótico)
    #     Retorna: Tempo real gasto no movimento
    #     '''
    #     # Usar pyHM para trajetórias não lineares
    #     # Implementar offset final aleatório (3-7 pixels)
    ```
*   **Proteções Anti-Detecção:**
    - [ ] 4.1. Implementar movimentos com variação de aceleração (ex: `curve_factor` com `pyHM`).
    - [ ] 4.2. Adicionar pausas pós-movimento aleatórias (0.1-0.7s).
    - [ ] 4.3. Garantir padrões de movimento imprevisíveis (evitar linearidade).
    - [ ] 4.4. Implementar offset final aleatório (3-7 pixels) na posição do clique.
    - [ ] 4.5. (Opcional Avançado) Explorar sistema de aprendizado por reforço para adaptação.
*   **Entregáveis Esperados:**
    - [ ] Código Python comentado em português.
    - [ ] Exemplo de uso/implementação do controle de mouse.
    - [ ] Demonstração das técnicas anti-detecção.

---

### Fase 5: Sistema de Controle de Teclado
*   **Exigência:** Simulador de digitação humana com perfis configuráveis.
    ```python
    # class Teclado:
    #     def __init__(self, perfil: str = 'padrão'):
    #         self.perfis = {
    #             'combate': {'delay': (0.08, 0.15)},
    #             'navegação': {'delay': (0.2, 0.4)}
    #         }
        
    #     def pressionar(self, tecla: str, contexto: str):
    #         # Implementar atrasos aleatórios baseados no contexto
    ```
*   **Features:**
    - [ ] 5.1. Implementar mapeamento de teclas por classe/personagem (configurável).
    - [ ] 5.2. Desenvolver sistema de cooldown adaptativo para habilidades/teclas.
    - [ ] 5.3. Criar sequenciador de combos (ex: F1 → F2 → Espaço) configurável.
    - [ ] 5.4. Implementar atrasos aleatórios entre pressionamentos de tecla, baseados em perfis/contexto.
*   **Entregáveis Esperados:**
    - [ ] Código Python comentado em português.
    - [ ] Exemplo de uso/implementação do controle de teclado.
    - [ ] Arquivos de configuração para perfis e mapeamento de teclas.
    - [ ] Técnicas anti-detecção (atrasos humanizados).

---

### Fase 6: Integração e Controle Principal
*   **Exigência:** Máquina de estados finitos (FSM) para comportamento.
    ```python
    # class BotFSM:
    #     estados = ('patrulha', 'combate', 'fuga', 'descanso')
        
    #     def decidir_acao(self, frame):
    #         # Lógica de transição de estados
    #         # Priorizar ações com base na detecção
    ```
*   **Módulos de Integração:**
    - [ ] 6.1. Implementar o loop principal do bot com taxa de atualização variável (se benéfico).
    - [ ] 6.2. Desenvolver sistema de priorização de alvos (baseado em `prioridade_monstros` da config).
    - [ ] 6.3. Implementar a Máquina de Estados Finitos (FSM) com os estados básicos e lógica de transição.
    - [ ] 6.4. Implementar logger (possivelmente não criptografado inicialmente para facilitar debugging, depois adicionar criptografia se necessário).
*   **Entregáveis Esperados:**
    - [ ] Código Python comentado em português da FSM e loop principal.
    - [ ] Exemplo de funcionamento do bot em um ciclo básico.
    - [ ] Demonstração da transição entre estados.

---

### Fase 7: Sistema de Configuração
*   **Exigência:** Arquivo JSON com perfis pré-definidos.
    ```python
    # config_schema = {
    #     "regiao_jogo": {"x": 0, "y": 0, "w": 1024, "h": 768},
    #     "prioridade_monstros": ["Poring", "Lunatic"],
    #     "comportamento": {
    #         "agressividade": 0.7,
    #         "intervalo_checagem": 2.5
    #     }
    # }
    ```
*   **Entregáveis:**
    - [ ] 7.1. Criar estrutura do arquivo de configuração JSON (baseado no schema).
    - [ ] 7.2. Implementar lógica para carregar e validar a configuração.
    - [ ] 7.3. (Opcional Inicial) GUI básica para ajuste de regiões, ou script para facilitar a configuração da região.
    - [ ] 7.4. Criar sistema de presets intercambiáveis (diferentes arquivos de config ou seções no config).
*   **Entregáveis Esperados:**
    - [ ] Código Python para gerenciamento da configuração.
    - [ ] Arquivo JSON de exemplo com a configuração.
    - [ ] Validador de configuração (script ou função).

---

### Fase 8: Testes e Otimização
*   **Exigência:** Suíte de testes com métricas de desempenho.
    ```python
    # def benchmark_deteccao():
    #     # Testar FPS/acuracia em diferentes cenários
    #     # Gerar relatório de performance
    ```
*   **Métricas Cruciais:**
    - [ ] 8.1. Desenvolver scripts para benchmark de detecção (FPS, acurácia).
    - [ ] 8.2. Medir e otimizar latência total do sistema.
    - [ ] 8.3. Avaliar e reduzir taxa de falsos positivos/negativos na detecção.
    - [ ] 8.4. Monitorar e otimizar consumo de recursos (CPU/GPU).
    - [ ] 8.5. Criar relatório de performance.
*   **Entregáveis Esperados:**
    - [ ] Scripts de teste e benchmark.
    - [ ] Relatório de performance com as métricas chave.
    - [ ] Código otimizado com base nos testes.

---

## Restrições Gerais do Projeto
- [ ] Manter 0 dependências pagas.
- [ ] Garantir compatibilidade com Windows 10/11.
- [ ] Manter consumo de CPU < 25% em idle (após otimizações).

## Status Atual / Próximos Passos

*(Esta seção é para você preencher e atualizar)*

-   **Última Tarefa Concluída:** Fase 1 completa (Configuração Inicial, Geração de `requirements.txt`).
-   **Em Andamento:** Fase 2 - Sistema de Captura de Tela Adaptativo.
-   **Próximos Objetivos:** Fase 2.3 - Implementar taxa de captura ajustável (15-30 FPS).
-   **Bloqueios/Desafios:** DXCam adiado devido à compatibilidade com Python 3.13.

---

**Lembre-se de atualizar este arquivo regularmente, marcando as tarefas concluídas e adicionando notas sobre o progresso.** 

-   **Última Tarefa Concluída:** Fase 2 completa (Sistema de Captura de Tela Adaptativo - MSS).
-   **Em Andamento:** Fase 3 - Motor de Reconhecimento de Monstros.
-   **Próximos Objetivos:** Fase 3.1 - Pré-processamento de imagens; Otimizações adicionais na detecção.
-   **Bloqueios/Desafios:** DXCam adiado; Otimização de FPS para captura de tela será revisitada.

---

**Lembre-se de atualizar este arquivo regularmente, marcando as tarefas concluídas e adicionando notas sobre o progresso.** 