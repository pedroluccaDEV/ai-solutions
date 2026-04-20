# features/channels/webhook_saphien/connection/saphien_widget_generator.py
"""
Gerador do código JavaScript para o widget.
Versão com token seguro no header e session_id persistente.
"""
from typing import Dict, Any
import json


class SaphienWidgetGenerator:
    """Gera o código JS embeddable do widget."""
    
    def generate_widget_script(self, config: Dict[str, Any]) -> str:
        """
        Gera o script completo do widget.
        
        Args:
            config: Configuração do widget contendo:
                - widget_token: Token único do widget
                - apiUrl: URL base do webhook (sem token na URL)
                - instance_name: Nome da instância
                - allowed_origins: Lista de domínios permitidos
                - preferences: Preferências de estilo/comportamento
        
        Returns:
            String com o código JavaScript do widget
        """
        # Prepara as configurações com defaults
        preferences = config.get("preferences", {})
        
        widget_config = {
            "token": config["widget_token"],
            "apiUrl": config.get("apiUrl", "/api/v1/saphien/webhook_saphien"),
            "instanceName": config.get("instanceName", "Saphien Assistant"),
            "allowedOrigins": config.get("allowedOrigins", []),
            "position": preferences.get("position", "bottom-right"),
            "primaryColor": preferences.get("primary_color", "#5c6bc0"),
            "placeholderText": preferences.get("placeholder_text", "Como posso ajudar?"),
            "showBranding": preferences.get("show_branding", True),
            "windowTitle": preferences.get("window_title", "Assistente Virtual"),
            "windowSubtitle": preferences.get("window_subtitle", "Online agora"),
            "theme": preferences.get("theme", "light"),
            "chatHeight": preferences.get("chat_height", "500px"),
            "chatWidth": preferences.get("chat_width", "380px"),
            "buttonIcon": preferences.get("button_icon", "message-circle"),
        }
        
        # Gera o script
        script = f"""
(function() {{
    'use strict';
    
    // =====================================================
    // CONFIGURAÇÃO
    // =====================================================
    var config = {json.dumps(widget_config, indent=2)};
    
    // =====================================================
    // SESSION ID PERSISTENTE (localStorage)
    // =====================================================
    var sessionId = localStorage.getItem('saphien_session_id');
    if (!sessionId) {{
        // Gera UUID v4
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
            var r = Math.random() * 16 | 0;
            var v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        }});
        localStorage.setItem('saphien_session_id', sessionId);
        console.log('[Saphien Widget] Nova sessão criada:', sessionId);
    }} else {{
        console.log('[Saphien Widget] Sessão existente:', sessionId);
    }}
    
    // Flag para controle de registro de sessão
    var sessionRegistered = localStorage.getItem('saphien_session_registered') === 'true';
    
    // =====================================================
    // VALIDAÇÃO DE ORIGEM (CORS)
    // =====================================================
    var currentOrigin = window.location.origin;
    var isFileProtocol = currentOrigin === 'file://' || currentOrigin === 'null';
    if (!isFileProtocol && config.allowedOrigins.length > 0 && !config.allowedOrigins.includes(currentOrigin)) {{
        console.warn('[Saphien Widget] Domínio não autorizado:', currentOrigin);
        console.warn('[Saphien Widget] Domínios permitidos:', config.allowedOrigins);
        return;
    }}
    
    if (isFileProtocol) {{
        console.log('[Saphien Widget] Modo desenvolvimento (file://) - ignorando validação CORS');
    }}
    
    // =====================================================
    // CRIAÇÃO DO WIDGET
    // =====================================================
    
    // Cria o container do widget
    var widgetContainer = document.createElement('div');
    widgetContainer.id = 'saphien-widget-container';
    widgetContainer.style.cssText = `
        position: fixed;
        ${{config.position === 'bottom-right' ? 'right: 20px;' : 'left: 20px;'}}
        bottom: 20px;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    // Cria o botão flutuante
    var widgetButton = document.createElement('div');
    widgetButton.id = 'saphien-widget-button';
    widgetButton.style.cssText = `
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: ${{config.primaryColor}};
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s;
    `;
    
    // Ícone do botão (balão de chat)
    widgetButton.innerHTML = `
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="white"/>
        </svg>
    `;
    
    widgetButton.onmouseover = function() {{ this.style.transform = 'scale(1.1)'; }};
    widgetButton.onmouseout = function() {{ this.style.transform = 'scale(1)'; }};
    
    // Cria a janela de chat
    var chatWindow = document.createElement('div');
    chatWindow.id = 'saphien-chat-window';
    chatWindow.style.cssText = `
        position: absolute;
        ${{config.position === 'bottom-right' ? 'right: 0;' : 'left: 0;'}}
        bottom: 80px;
        width: ${{config.chatWidth}};
        height: ${{config.chatHeight}};
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        display: none;
        flex-direction: column;
        overflow: hidden;
    `;
    
    // Cabeçalho do chat
    chatWindow.innerHTML = `
        <div style="background: ${{config.primaryColor}}; color: white; padding: 15px;">
            <strong>${{config.windowTitle}}</strong>
            <small style="display: block; font-size: 12px; opacity: 0.9;">${{config.windowSubtitle}}</small>
        </div>
        <div id="saphien-messages" style="flex: 1; overflow-y: auto; padding: 15px; background: #f5f5f5;">
            <div style="text-align: center; color: #999; padding: 20px;">
                Carregando...
            </div>
        </div>
        <div style="padding: 15px; border-top: 1px solid #e0e0e0; background: white;">
            <div style="display: flex; gap: 10px;">
                <input type="text" id="saphien-input" placeholder="${{config.placeholderText}}" 
                       style="flex: 1; padding: 10px; border: 1px solid #e0e0e0; border-radius: 20px; outline: none;">
                <button id="saphien-send" style="background: ${{config.primaryColor}}; color: white; border: none; 
                        border-radius: 20px; padding: 10px 20px; cursor: pointer;">
                    Enviar
                </button>
            </div>
        </div>
        ${{config.showBranding ? '<div style="text-align: center; padding: 5px; font-size: 10px; color: #999;">Powered by Saphien</div>' : ''}}
    `;
    
    widgetContainer.appendChild(widgetButton);
    widgetContainer.appendChild(chatWindow);
    document.body.appendChild(widgetContainer);
    
    // =====================================================
    // FUNÇÕES DE API (com headers seguros)
    // =====================================================
    
    // Registra sessão (apenas uma vez)
    function registerSession() {{
        if (sessionRegistered) return Promise.resolve();
        
        return fetch(config.apiUrl + '/session', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Widget-Token': config.token,
                'X-Session-Id': sessionId
            }},
            body: JSON.stringify({{
                session_id: sessionId,
                url: window.location.href,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.status === 'success') {{
                sessionRegistered = true;
                localStorage.setItem('saphien_session_registered', 'true');
                console.log('[Saphien Widget] Sessão registrada:', sessionId);
            }} else {{
                console.warn('[Saphien Widget] Falha ao registrar sessão:', data.message);
            }}
        }})
        .catch(error => {{
            console.error('[Saphien Widget] Erro ao registrar sessão:', error);
        }});
    }}
    
    // Carrega mensagens iniciais
    function loadInitialMessages() {{
        var url = config.apiUrl + '/messages?limit=50';
        
        fetch(url, {{
            method: 'GET',
            headers: {{
                'Content-Type': 'application/json',
                'X-Widget-Token': config.token,
                'X-Session-Id': sessionId
            }}
        }})
        .then(response => response.json())
        .then(data => {{
            if (data.status === 'success' && data.messages && data.messages.length > 0) {{
                messagesContainer.innerHTML = '';
                data.messages.forEach(function(msg) {{
                    appendMessage(msg.text, msg.sender);
                }});
            }} else {{
                messagesContainer.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">Envie uma mensagem para começar</div>';
            }}
        }})
        .catch(function(error) {{
            console.error('[Saphien Widget] Erro ao carregar mensagens:', error);
            messagesContainer.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">Conectando ao assistente...</div>';
        }});
    }}
    
    // Adiciona mensagem ao chat
    function appendMessage(text, sender) {{
        var messageDiv = document.createElement('div');
        messageDiv.style.cssText = `
            margin-bottom: 10px;
            display: flex;
            justify-content: ${{sender === 'user' ? 'flex-end' : 'flex-start'}};
        `;
        
        var bubble = document.createElement('div');
        bubble.style.cssText = `
            max-width: 70%;
            padding: 10px 15px;
            border-radius: 18px;
            background: ${{sender === 'user' ? config.primaryColor : '#e0e0e0'}};
            color: ${{sender === 'user' ? 'white' : '#333'}};
            word-wrap: break-word;
        `;
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }}
    
    // Envia mensagem
    function sendMessage() {{
        var message = inputElement.value.trim();
        if (!message) return;
        
        // Adiciona mensagem do usuário na UI
        appendMessage(message, 'user');
        inputElement.value = '';
        
        // Envia para o backend
        fetch(config.apiUrl, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'X-Widget-Token': config.token,
                'X-Session-Id': sessionId
            }},
            body: JSON.stringify({{
                message: message,
                session_id: sessionId,
                sender: 'user',
                timestamp: new Date().toISOString()
            }})
        }})
        .then(function(response) {{ return response.json(); }})
        .then(function(data) {{
            if (data.reply) {{
                appendMessage(data.reply, 'bot');
            }} else if (data.status === 'error') {{
                appendMessage(data.reply || 'Erro ao processar mensagem.', 'bot');
            }}
        }})
        .catch(function(error) {{
            console.error('[Saphien Widget] Erro ao enviar mensagem:', error);
            appendMessage('Desculpe, ocorreu um erro. Tente novamente.', 'bot');
        }});
    }}
    
    // =====================================================
    // EVENT LISTENERS
    // =====================================================
    
    var isOpen = false;
    var messagesContainer = document.getElementById('saphien-messages');
    var inputElement = document.getElementById('saphien-input');
    var sendButton = document.getElementById('saphien-send');
    
    sendButton.onclick = sendMessage;
    inputElement.onkeypress = function(e) {{
        if (e.key === 'Enter') sendMessage();
    }};
    
    widgetButton.onclick = function() {{
        isOpen = !isOpen;
        chatWindow.style.display = isOpen ? 'flex' : 'none';
        if (isOpen && messagesContainer.innerHTML.includes('Carregando...')) {{
            loadInitialMessages();
        }}
    }};
    
    // =====================================================
    // INICIALIZAÇÃO
    // =====================================================
    
    // Registra sessão automaticamente
    registerSession();
    
    console.log('[Saphien Widget] Inicializado com session_id:', sessionId);
    console.log('[Saphien Widget] API URL:', config.apiUrl);
    
}})();
"""
        return script.strip()