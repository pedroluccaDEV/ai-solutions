import os
import time
import logging
import requests
from typing import Dict, Any
from textwrap import dedent

logger = logging.getLogger(__name__)


class EnhancePromptFeature:
    """Feature para aprimoramento de prompts usando DeepSeek API"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY não configurada")
        
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        logger.info("EnhancePromptFeature inicializada")
    
    async def enhance_prompt(
        self, 
        prompt: str, 
        enhancement_type: str = "general",
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Aprimora um prompt usando DeepSeek API
        
        Args:
            prompt: Prompt original
            enhancement_type: Tipo de conteúdo
            tone: Tom da resposta
            
        Returns:
            Dict com prompt aprimorado
        """
        start_time = time.time()
        
        try:
            # Construir instruções específicas
            instructions = self._build_instructions(enhancement_type, tone)
            
            # Fazer requisição para a API
            response = requests.post(
                self.api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt(instructions)
                        },
                        {
                            "role": "user",
                            "content": f"Aprimore este prompt:\n\n{prompt}"
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "stream": False
                },
                timeout=30
            )
            
            response.raise_for_status()
            
            data = response.json()
            enhanced_prompt = data["choices"][0]["message"]["content"].strip()
            
            # Calcular melhoria
            improvement = self._calculate_improvement(prompt, enhanced_prompt)
            
            return {
                "original_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "model_used": self.model,
                "improvement_percentage": improvement
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição API: {e}")
            raise ValueError(f"Falha na comunicação com a API: {str(e)}")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            raise
    
    def _build_instructions(self, enhancement_type: str, tone: str) -> str:
        """Constrói instruções baseadas nos parâmetros"""
        
        type_map = {
            "text": "Para geração de texto (artigos, relatórios, emails)",
            "image": "Para geração de imagens (descrições visuais detalhadas)",
            "video": "Para roteiros de vídeo ou storyboards",
            "audio": "Para scripts de áudio ou podcasts",
            "document": "Para criação de documentos formais",
            "presentation": "Para slides e apresentações",
            "code": "Para geração de código ou documentação técnica",
            "analysis": "Para análise de dados ou relatórios analíticos",
            "general": "Para uso geral com IA"
        }
        
        tone_map = {
            "casual": "Linguagem informal e amigável",
            "professional": "Linguagem formal e técnica",
            "creative": "Linguagem criativa e inspiradora",
            "academic": "Linguagem acadêmica formal",
            "technical": "Linguagem técnica precisa"
        }
        
        return f"Tipo: {type_map.get(enhancement_type, 'Para uso geral com IA')}. Tom: {tone_map.get(tone, 'Linguagem formal e técnica')}."
    
    def _get_system_prompt(self, instructions: str) -> str:
        """Retorna o prompt do sistema"""
        return dedent(f"""
        Você é um especialista em engenharia de prompts.
        
        Sua tarefa: Aprimorar prompts para sistemas de IA.
        
        Instruções específicas:
        {instructions}
        
        Técnicas a aplicar:
        1. Tornar o objetivo mais claro
        2. Adicionar detalhes específicos
        3. Estruturar de forma lógica
        4. Adaptar ao tom solicitado
        
        Retorne APENAS o prompt aprimorado, pronto para uso.
        Não inclua análises, explicações ou comentários.
        """)
    
    def _calculate_improvement(self, original: str, enhanced: str) -> float:
        """Calcula porcentagem de melhoria"""
        if not original:
            return 0.0
        
        original_len = len(original)
        enhanced_len = len(enhanced)
        
        if original_len == 0:
            return 0.0
        
        improvement = ((enhanced_len - original_len) / original_len) * 100
        return round(improvement, 1)