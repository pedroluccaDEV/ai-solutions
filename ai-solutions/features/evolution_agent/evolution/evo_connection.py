import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# ======== DATACLASSES ========
@dataclass
class WebhookConfig:
    url: str
    enabled: bool = True
    webhook_by_events: bool = False
    webhook_base64: bool = True
    events: List[str] = field(default_factory=list)

@dataclass
class InstanceConfig:
    instance_name: str
    phone_number: Optional[str] = None
    reject_calls: bool = False
    call_message: Optional[str] = None
    groups_ignore: bool = False
    always_online: bool = False
    read_messages: bool = False
    read_status: bool = False
    sync_full_history: bool = False
    webhook: Optional[WebhookConfig] = None

# ======== API MANAGER ========
class EvolutionAPIManager:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/json', 'apikey': api_key}

    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('timeout', self.timeout)
        try:
            response = requests.request(method, url, **kwargs)
            return response.json() if response.text else {}
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None

    # Criar instância com webhook
    def criar_instancia_com_webhook(self, config: InstanceConfig) -> Optional[Dict]:
        payload = {
            "instanceName": config.instance_name,
            "phoneNumber": config.phone_number,
            "integration": "WHATSAPP-BAILEYS",
            "rejectCalls": config.reject_calls,
            "callMessage": config.call_message,
            "groupsIgnore": config.groups_ignore,
            "alwaysOnline": config.always_online,
            "readMessages": config.read_messages,
            "readStatus": config.read_status,
            "syncFullHistory": config.sync_full_history,
            "qrcode": True
        }
        if config.webhook:
            payload["webhook"] = {
                "url": config.webhook.url,
                "enabled": config.webhook.enabled,
                "byEvents": config.webhook.webhook_by_events,
                "base64": config.webhook.webhook_base64,
                "events": config.webhook.events
            }
        return self._request("POST", "/instance/create", json=payload)

    # Atualizar webhook
    def atualizar_webhook(self, instance_id: str, webhook: WebhookConfig) -> Optional[Dict]:
        payload = {
            "enabled": webhook.enabled,
            "url": webhook.url,
            "webhookByEvents": webhook.webhook_by_events,
            "webhookBase64": webhook.webhook_base64,
            "events": webhook.events
        }
        return self._request("POST", f"/webhook/set/{instance_id}", json=payload)

    # Deletar instância
    def deletar_instancia(self, instance_id: str) -> Optional[Dict]:
        return self._request("DELETE", f"/instance/delete/{instance_id}")

    # ========= NOVO MÉTODO =========
    def enviar_presenca_composing(self, instance_id: str, number: str, delay: int = 5000) -> Optional[Dict]:
        """
        Envia o status "digitando..." (composing) para o número especificado.

        :param instance_id: Nome da instância Evolution (ex: 'instance_5511999999999')
        :param number: Número do destinatário com DDI, sem '+'
        :param delay: Tempo em milissegundos que o status será exibido (default 5000 ms)
        """
        payload = {
            "number": number,
            "presence": "composing",
            "delay": delay
        }
        print(f"💬 Enviando status 'digitando...' para {number} (instância {instance_id})")
        return self._request("POST", f"/chat/sendPresence/{instance_id}", json=payload)

# ======== MAIN TEST FUNCTION (somente criação) ========
def main(input_data: Dict[str, Any], base_url: str, api_key: str):
    manager = EvolutionAPIManager(base_url, api_key)

    for number, data in input_data.items():
        required = data.get("required", {})
        preferences = data.get("preferences", {})
        webhook_data = data.get("webhook", {})

        # Define URL do webhook automaticamente se não vier
        webhook_url = webhook_data.get(
            "url",
            f"https://meuservidor.com/api/v1/evolution/webhook/{required.get('instance_name', number)}"
        )

        webhook = WebhookConfig(
            url=webhook_url,
            enabled=webhook_data.get("enabled", True),
            events=webhook_data.get("events", [])
        )

        instance_config = InstanceConfig(
            instance_name=required.get("instance_name", f"instancia_{number}"),
            phone_number=required.get("phone_number", number),
            reject_calls=preferences.get("reject_calls", False),
            call_message=preferences.get("call_message"),
            groups_ignore=preferences.get("groups_ignore", False),
            always_online=preferences.get("always_online", False),
            read_messages=preferences.get("read_messages", False),
            read_status=preferences.get("read_status", False),
            sync_full_history=preferences.get("sync_full_history", False),
            webhook=webhook
        )

        print(f"\n🚀 Criando instância: {instance_config.instance_name}")
        result = manager.criar_instancia_com_webhook(instance_config)
        print(f"✅ Resultado: {result}")

        # ===== Exemplo de uso do novo método =====
        print(f"🟡 Testando presença 'digitando...' na instância {instance_config.instance_name}")
        resp = manager.enviar_presenca_composing(instance_config.instance_name, instance_config.phone_number)
        print(f"📨 Retorno: {resp}")

# ======== EXEMPLO DE USO ========
if __name__ == "__main__":
    input_json = {
        "5511999999999": {
            "required": {
                "phone_number": "5511999999999",
                "instance_name": "instance_5511999999999"
            },
            "preferences": {
                "always_online": True,
                "read_messages": True
            },
            "webhook": {
                "enabled": True,
                "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE", "QRCODE_UPDATED"]
            }
        }
    }

    BASE_URL = "https://evolution-api-development-db11.up.railway.app"
    API_KEY = "2d877fb10d9051186d06609c35659e17"

    main(input_json, BASE_URL, API_KEY)
