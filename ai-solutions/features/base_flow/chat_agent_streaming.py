# features/chat/chat_agent_streaming.py

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from datetime import datetime
import sys
from pathlib import Path
import traceback
import base64
import json

sys.path.append(str(Path(__file__).resolve().parents[2]))

from features.chat.agent_builder import build_agent_from_request
from features.chat.planner_agent import run_planner
from features.chat.executor_agent import run_executor_streaming
from features.chat.file_interpretation_engine import FileInterpretationEngine
from services.v1.billing_service import get_billing_service


# =====================================================
# CHAT AGENT STREAMING (ORQUESTRADOR)
# =====================================================

class ChatAgentStreaming:

    def __init__(self, user_jwt: str, user_id: Optional[str] = None, db=None):
        self.user_jwt = user_jwt
        self.user_id = user_id
        self.db = db
        self.billing_service = get_billing_service()

        # 🔑 sempre o user_id real do Postgres
        self.pg_user_id: Optional[int] = None
        self.execution_cost: int = 0

    # =====================================================
    # BILLING (ANTES DA EXECUÇÃO)
    # =====================================================

    async def _billing_before_execution(
        self,
        firebase_uid: str,
        model_id: str,
        session_id: str,
    ) -> Dict[str, Any]:

        result = await self.billing_service.validate_and_charge_credits_simple(
            firebase_uid=firebase_uid,
            model_id=int(model_id),
            session_id=session_id,
        )

        if not result["success"] or not result["authorized"]:
            return {
                "authorized": False,
                "message": result.get("message", "Créditos insuficientes"),
            }

        self.pg_user_id = int(result["user_id"])
        self.execution_cost = int(result["execution_cost"])

        return {
            "authorized": True,
            "metadata": {
                "user_id": self.pg_user_id,
                "model_id": model_id,
                "execution_cost": self.execution_cost,
                "credits_before": result["credits_before"],
                "credits_after": result["credits_after"],
            },
        }

    # =====================================================
    # BUILDER + FILES
    # =====================================================

    async def _run_builder_and_files(self, request_data, files_dict):
        """
        Executa builder e processamento de arquivos em paralelo.
        files_dict deve ter estrutura: {"files": [...]}
        """
        print(f"\n{'='*60}")
        print(f"[CHAT AGENT] _run_builder_and_files")
        print(f"[CHAT AGENT] files_dict recebido: {files_dict is not None}")

        file_result = None

        if files_dict and files_dict.get("files"):
            files_list = files_dict["files"]
            print(f"[CHAT AGENT] Arquivos na lista: {len(files_list)}")

            engine = FileInterpretationEngine()

            builder_result, file_result = await asyncio.gather(
                build_agent_from_request(request_data, self.db),
                engine.interpret_files(files_list)
            )

            text_blocks = file_result.get("text_blocks", [])
            print(f"[CHAT AGENT] Processamento concluído: {len(text_blocks)} blocos de texto extraídos")
            for i, block in enumerate(text_blocks):
                meta = block.get("metadata", {})
                print(f"[CHAT AGENT]   Bloco {i+1}: {meta.get('filename')} ({meta.get('type')}) - {len(block.get('content', ''))} chars")
        else:
            if files_dict:
                print(f"[CHAT AGENT] ⚠️ files_dict não contém lista 'files'")
            else:
                print(f"[CHAT AGENT] Nenhum arquivo para processar")

            builder_result = await build_agent_from_request(request_data, self.db)

        print(f"[CHAT AGENT] Builder concluído")
        print(f"{'='*60}\n")

        return builder_result, file_result

    # =====================================================
    # FLOW SELECTOR
    # =====================================================

    def _select_flow_runner(self, flow_type: str):
        if flow_type == "chat":
            return self._run_chat_flow
        elif flow_type == "skill":
            return self._run_skill_flow
        elif flow_type == "search":
            try:
                from features.chat.search.search_flow import run_search_flow_streaming
                return run_search_flow_streaming
            except ImportError as e:
                print(f"[AVISO] Erro ao importar search flow: {e}")
                return self._search_fallback
        elif flow_type == "image":
            return self._run_image_flow
        return None

    async def _search_fallback(self, *args, **kwargs):
        yield {
            "type": "error",
            "stage": "flow_router",
            "error": "Módulo de search não disponível",
            "complete": True,
        }

    # =====================================================
    # MAIN ENTRYPOINT
    # =====================================================

    async def run_streaming(
        self,
        request_data: Dict[str, Any],
        files: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:

        firebase_uid = request_data.get("user_id")
        message = request_data.get("message")
        flow_type = request_data.get("flow_type", "chat")
        session_id = request_data.get("session_id") or f"s_{int(datetime.now().timestamp())}"

        print(f"\n{'='*60}")
        print(f"[CHAT AGENT] run_streaming INICIADO")
        print(f"[CHAT AGENT] session_id: {session_id}")
        print(f"[CHAT AGENT] flow_type: {flow_type}")
        print(f"[CHAT AGENT] message: {message[:50]}...")
        print(f"[CHAT AGENT] files recebido: {files is not None}")

        if files:
            file_list = files.get("files", [])
            print(f"[CHAT AGENT] Quantidade de arquivos na lista: {len(file_list)}")
            for i, f in enumerate(file_list):
                print(f"[CHAT AGENT]   Arquivo {i+1}: {f.get('filename')} ({f.get('size')} bytes) - {f.get('content_type')}")
        else:
            print(f"[CHAT AGENT] Nenhum arquivo recebido")
        print(f"{'='*60}\n")

        if not firebase_uid or not message:
            yield {
                "type": "error",
                "stage": "validation",
                "error": "user_id e message são obrigatórios",
                "complete": True,
            }
            return

        # =================== BUILDER + FILES ===================
        builder_result, file_result = await self._run_builder_and_files(
            request_data, files
        )

        agent_data = builder_result.get("agent")
        model_id = agent_data.get("model") or "1"

        builder_model = builder_result.get("resources", {}).get("builder_model")
        if not builder_model:
            builder_model = builder_result.get("model_data")

        if not builder_model:
            raise RuntimeError("builder_model ausente — impossível instanciar LLM")

        print(f"\n{'='*60}")
        print(f"[CHAT AGENT] Resultado do processamento:")
        print(f"[CHAT AGENT] Agente: {agent_data.get('name')}")
        print(f"[CHAT AGENT] Modelo ID: {model_id}")
        print(f"[CHAT AGENT] file_result: {file_result is not None}")
        if file_result:
            print(f"[CHAT AGENT]   Arquivos processados: {len(file_result.get('files', []))}")
            print(f"[CHAT AGENT]   has_files: {bool(file_result)}")
        print(f"{'='*60}\n")

        yield {
            "type": "resources_loaded",
            "stage": "agent_builder",
            "data": {
                "agent_name": agent_data.get("name"),
                "agent_id": agent_data.get("_id", {}).get("$oid"),
                "model_id": model_id,
                "flow_type": flow_type,
                "has_files": bool(file_result),
                "files_count": len(file_result.get("files", [])) if file_result else 0,
            },
            "complete": False,
        }

        # =================== BILLING ===================
        billing = await self._billing_before_execution(
            firebase_uid=firebase_uid,
            model_id=model_id,
            session_id=session_id,
        )

        if not billing["authorized"]:
            yield {
                "type": "billing_error",
                "stage": "billing",
                "error": billing["message"],
                "complete": True,
            }
            return

        yield {
            "type": "billing_verified",
            "stage": "billing",
            "data": billing["metadata"],
            "complete": False,
        }

        # =================== SELECT FLOW ===================
        flow_runner = self._select_flow_runner(flow_type)

        if not flow_runner:
            yield {
                "type": "error",
                "stage": "flow_router",
                "error": f"flow_type inválido: {flow_type}",
                "complete": True,
            }
            return

        # =================== EXECUTE FLOW ===================
        print(f"\n[CHAT AGENT] Executando flow: {flow_type}")
        async for event in flow_runner(
            message=message,
            firebase_uid=firebase_uid,
            session_id=session_id,
            agent_data=agent_data,
            model_id=model_id,
            builder_result=builder_result,
            file_result=file_result,
        ):
            yield event

    # =====================================================
    # CHAT FLOW
    # =====================================================

    async def _run_chat_flow(
        self,
        message: str,
        firebase_uid: str,
        session_id: str,
        agent_data: Dict,
        model_id: str,
        builder_result: Dict,
        file_result: Optional[Dict] = None,
    ) -> AsyncGenerator[Dict, None]:

        total_input_tokens = 0
        total_output_tokens = 0
        completed = False
        error_message = None
        full_response = ""

        builder_model = builder_result.get("resources", {}).get("builder_model")
        if not builder_model:
            builder_model = builder_result.get("model_data")
            if not builder_model:
                raise RuntimeError("builder_model ausente no chat flow")

        yield {
            "type": "planner_started",
            "stage": "planner",
            "data": {
                "status": "starting",
                "model_id": model_id,
                "flow_type": "chat",
            },
            "complete": False,
        }

        planner_result = await asyncio.to_thread(
            run_planner,
            user_prompt=message,
            kb_meta=builder_result.get("resources", {}).get("knowledgeBase", []),
            tools_meta=builder_result.get("resources", {}).get("tools", []),
            mcp_meta=builder_result.get("resources", {}).get("mcps", []),
            model_id=model_id,
            files_meta=None,
            agent_data=agent_data,
            conversation_history=builder_result.get("context", {}).get("conversation_history", []),
        )

        yield {
            "type": "planner_complete",
            "stage": "planner",
            "data": {
                "status": "completed",
                "plan": planner_result.get("planner_response", ""),
                "model_id": model_id,
                "flow_type": "chat",
            },
            "complete": False,
        }

        yield {
            "type": "executor_started",
            "stage": "executor",
            "data": {
                "status": "executing",
                "model_id": model_id,
                "flow_type": "chat",
            },
            "complete": False,
        }

        try:
            async for event in run_executor_streaming(
                agent_id=agent_data.get("_id", {}).get("$oid"),
                prompt=planner_result.get("planner_response", message),
                user_id=firebase_uid,
                resources={
                    "agent": agent_data,
                    "tools": builder_result.get("resources", {}).get("tools", []),
                    "mcps": builder_result.get("resources", {}).get("mcps", []),
                    "knowledge_bases": builder_result.get("resources", {}).get("knowledgeBase", []),
                    "files": file_result,
                    "context": {
                        **builder_result.get("context", {}),
                        "session_id": session_id,
                    },
                    "builder_model": builder_model,
                },
                resources_analyzed=planner_result.get("resources_analyzed", {}),
            ):
                event_type = event.get("type", "")

                if event_type == "token_usage":
                    token_data = event.get("data", {})
                    total_input_tokens += token_data.get("input_tokens", 0)
                    total_output_tokens += token_data.get("output_tokens", 0)

                if event_type == "chunk":
                    full_response += event.get("content", "")

                if event_type == "chunk":
                    yield {
                        "type": "executor_chunk",
                        "stage": "executor",
                        "data": {
                            "content": event.get("content", ""),
                            "chunk_number": event.get("chunk_number", 0),
                            "model_used": event.get("model_used", model_id),
                        },
                        "complete": False,
                    }
                elif event_type == "metadata":
                    yield {
                        "type": "metadata",
                        "stage": "executor",
                        "metadata": event.get("metadata", {}),
                        "complete": False,
                    }
                elif event_type == "token_usage":
                    yield {
                        "type": "token_usage",
                        "stage": "executor",
                        "data": event.get("data", {}),
                        "complete": False,
                    }
                elif event_type == "complete":
                    completed = True
                    yield {
                        "type": "flow_complete",
                        "stage": "complete",
                        "data": {
                            "flow_type": "chat",
                            "executor_type": "standard",
                            "model_used": event.get("model_used", model_id),
                            "tokens_used": event.get("tokens_used", {}),
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "full_response": full_response,
                        },
                        "complete": True,
                    }

                    yield {
                        "type": "all_loaded",
                        "stage": "complete",
                        "data": {
                            "status": "complete",
                            "session_id": session_id,
                            "has_response": bool(full_response),
                            "has_images": False,
                            "flow_type": "chat",
                        },
                        "complete": True,
                    }
                    return
                elif event_type == "error":
                    error_message = event.get("error", "Erro desconhecido")
                    yield {
                        "type": "error",
                        "stage": "executor",
                        "error": error_message,
                        "partial_response": event.get("partial_response"),
                        "model_used": event.get("model_used", model_id),
                        "complete": True,
                    }
                    return
                else:
                    yield event

            completed = True

        except Exception as e:
            error_message = str(e)
            print(f"[CHAT FLOW] Erro durante execução: {error_message}")
            traceback.print_exc()
            yield {
                "type": "error",
                "stage": "executor",
                "error": error_message,
                "partial_response": full_response,
                "complete": True,
            }
            raise

        finally:
            if self.pg_user_id:
                asyncio.create_task(
                    self.billing_service.register_credits_usage(
                        user_id=self.pg_user_id,
                        model_id=int(model_id),
                        credit_type="subscription",
                        credits_used=int(self.execution_cost),
                        usage_reason="chat_agent_streaming",
                        usage_metadata={
                            "session_id": session_id,
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "agent_name": agent_data.get("name"),
                            "flow_type": "chat",
                            "completed": completed,
                            "error": error_message,
                            "tokens": {
                                "input": total_input_tokens,
                                "output": total_output_tokens,
                                "total": total_input_tokens + total_output_tokens,
                            },
                            "model_used": builder_model.get("model_name", model_id),
                            "response_length": len(full_response),
                        },
                    )
                )

    # =====================================================
    # SKILL FLOW
    # =====================================================

    async def _run_skill_flow(
        self,
        message: str,
        firebase_uid: str,
        session_id: str,
        agent_data: Dict,
        model_id: str,
        builder_result: Dict,
        file_result: Optional[Dict] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Orquestra o fluxo de skill a partir do chat principal.
        """
        completed     = False
        error_message = None
        full_response = ""

        # skill_ids: tenta agent_data → context do builder → lista vazia
        skill_ids: List[str] = (
            agent_data.get("skill_ids")
            or builder_result.get("context", {}).get("skill_ids")
            or []
        )

        print(f"\n{'='*60}")
        print(f"[SKILL FLOW] Iniciando skill flow via chat")
        print(f"[SKILL FLOW] skill_ids: {skill_ids}")
        print(f"[SKILL FLOW] session_id: {session_id}")
        print(f"{'='*60}\n")

        if not skill_ids:
            yield {
                "type": "error",
                "stage": "skill_flow",
                "error": "skill_ids ausente — informe ao menos um skill_id no request.",
                "complete": True,
            }
            return

        try:
            from features.skills.skill_agent.skill_agent import SkillAgent
        except ImportError as e:
            yield {
                "type": "error",
                "stage": "skill_flow",
                "error": f"Módulo skill_agent não disponível: {e}",
                "complete": True,
            }
            return

        try:
            skill_agent = SkillAgent()

            async for event in skill_agent.run_streaming(
                user_prompt=message,
                builder_result=builder_result,
                skill_ids=skill_ids,
                user_id=firebase_uid,
            ):
                event_type = event.get("type", "")

                if event_type == "planner_start":
                    yield {
                        "type": "planner_started",
                        "stage": "planner",
                        "data": {
                            "status": "starting",
                            "model_id": model_id,
                            "flow_type": "skill",
                        },
                        "complete": False,
                    }

                elif event_type == "planner_complete":
                    yield {
                        "type": "planner_complete",
                        "stage": "planner",
                        "data": {
                            "status": "completed",
                            "plan": event.get("response", ""),
                            "can_proceed": event.get("can_proceed", False),
                            "model_id": model_id,
                            "flow_type": "skill",
                        },
                        "complete": False,
                    }

                elif event_type == "executor_start":
                    yield {
                        "type": "executor_started",
                        "stage": "executor",
                        "data": {
                            "status": "executing",
                            "model_id": model_id,
                            "flow_type": "skill",
                        },
                        "complete": False,
                    }

                elif event_type == "executor_chunk":
                    chunk_content = event.get("content", "")
                    full_response += chunk_content
                    yield {
                        "type": "executor_chunk",
                        "stage": "executor",
                        "data": {
                            "content": chunk_content,
                            "chunk_number": event.get("chunk_number", 0),
                            "model_used": model_id,
                        },
                        "complete": False,
                    }

                elif event_type == "flow_complete":
                    # 🔥 CORREÇÃO: skill_agent envia flow_complete, não executor_complete
                    completed = True
                    if event.get("final_response"):
                        full_response = event["final_response"]
                    
                    # Repassa o flow_complete
                    yield {
                        "type": "flow_complete",
                        "stage": "complete",
                        "data": {
                            "flow_type": "skill",
                            "executor_type": "skill",
                            "model_used": model_id,
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "full_response": full_response,
                            "success": event.get("success", True),
                        },
                        "complete": True,
                    }

                    # Envia all_loaded
                    yield {
                        "type": "all_loaded",
                        "stage": "complete",
                        "data": {
                            "status": "complete",
                            "session_id": session_id,
                            "has_response": bool(full_response),
                            "has_images": False,
                            "flow_type": "skill",
                        },
                        "complete": True,
                    }
                    return

                elif event_type == "executor_complete":
                    # Fallback para compatibilidade (caso o skill_agent ainda use executor_complete)
                    completed = True
                    if event.get("content"):
                        full_response = event["content"]

                    yield {
                        "type": "flow_complete",
                        "stage": "complete",
                        "data": {
                            "flow_type": "skill",
                            "executor_type": "skill",
                            "model_used": model_id,
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "full_response": full_response,
                            "success": event.get("success", True),
                        },
                        "complete": True,
                    }

                    yield {
                        "type": "all_loaded",
                        "stage": "complete",
                        "data": {
                            "status": "complete",
                            "session_id": session_id,
                            "has_response": bool(full_response),
                            "has_images": False,
                            "flow_type": "skill",
                        },
                        "complete": True,
                    }
                    return

                elif event_type == "error":
                    error_message = event.get("error", "Erro desconhecido no skill flow")
                    yield {
                        "type": "error",
                        "stage": "skill_flow",
                        "error": error_message,
                        "partial_response": full_response or None,
                        "complete": True,
                    }
                    return

                else:
                    # Repassa outros eventos sem modificação
                    yield event

            # Se saiu do loop sem encontrar flow_complete, envia um final
            if not completed:
                yield {
                    "type": "flow_complete",
                    "stage": "complete",
                    "data": {
                        "flow_type": "skill",
                        "executor_type": "skill",
                        "model_used": model_id,
                        "agent_id": agent_data.get("_id", {}).get("$oid"),
                        "full_response": full_response,
                        "success": True,
                    },
                    "complete": True,
                }

                yield {
                    "type": "all_loaded",
                    "stage": "complete",
                    "data": {
                        "status": "complete",
                        "session_id": session_id,
                        "has_response": bool(full_response),
                        "has_images": False,
                        "flow_type": "skill",
                    },
                    "complete": True,
                }

        except Exception as e:
            error_message = str(e)
            print(f"[SKILL FLOW] Erro durante execução: {error_message}")
            traceback.print_exc()
            yield {
                "type": "error",
                "stage": "skill_flow",
                "error": error_message,
                "partial_response": full_response or None,
                "complete": True,
            }

        finally:
            if self.pg_user_id:
                asyncio.create_task(
                    self.billing_service.register_credits_usage(
                        user_id=self.pg_user_id,
                        model_id=int(model_id),
                        credit_type="subscription",
                        credits_used=int(self.execution_cost),
                        usage_reason="skill_agent_streaming",
                        usage_metadata={
                            "session_id": session_id,
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "agent_name": agent_data.get("name"),
                            "flow_type": "skill",
                            "skill_ids": skill_ids,
                            "completed": completed,
                            "error": error_message,
                            "response_length": len(full_response),
                        },
                    )
                )

    # =====================================================
    # IMAGE FLOW
    # =====================================================

    async def _run_image_flow(
        self,
        message: str,
        firebase_uid: str,
        session_id: str,
        agent_data: Dict,
        model_id: str,
        builder_result: Dict,
        file_result: Optional[Dict] = None,
    ) -> AsyncGenerator[Dict, None]:

        completed = False
        error_message = None

        resources = builder_result.get("resources", {})
        builder_model = resources.get("builder_model")

        if not builder_model:
            builder_model = builder_result.get("model_data")

        if not builder_model:
            raise RuntimeError("builder_model ausente no image flow")

        image_models = resources.get("image_models", [])

        if not image_models:
            raise RuntimeError("Nenhum image_model definido no builder")

        yield {
            "type": "planner_started",
            "stage": "planner",
            "data": {
                "status": "starting",
                "model_id": model_id,
                "flow_type": "image",
            },
            "complete": False,
        }

        planner_result = await asyncio.to_thread(
            run_planner,
            user_prompt=message,
            kb_meta=[],
            tools_meta=image_models,
            mcp_meta=[],
            model_id=model_id,
            files_meta=None,
            agent_data=agent_data,
            conversation_history=[],
        )

        planner_prompt = planner_result.get("planner_response", message)

        yield {
            "type": "planner_complete",
            "stage": "planner",
            "data": {
                "status": "completed",
                "plan": planner_prompt,
                "model_id": model_id,
                "flow_type": "image",
            },
            "complete": False,
        }

        yield {
            "type": "executor_started",
            "stage": "executor",
            "data": {
                "status": "executing",
                "model_id": model_id,
                "flow_type": "image",
            },
            "complete": False,
        }

        try:
            from features.chat.image.executor_image import run_image_executor

            image_flow_data = {
                "planner_model": builder_model,
                "image_models": image_models,
                "agent": {
                    "name": agent_data.get("name"),
                    "description": agent_data.get("description"),
                },
                "original_user_message": message,
            }

            yield {
                "type": "image_generation_started",
                "stage": "executor",
                "complete": False,
            }

            print(f"[IMAGE FLOW] Executando run_image_executor...")
            result = await run_image_executor(
                prompt=planner_prompt,
                image_flow_data=image_flow_data,
            )

            if not result.get("success"):
                error_msg = result.get("error", "Erro na geração de imagem")
                print(f"[IMAGE FLOW] Erro na execução: {error_msg}")
                raise RuntimeError(error_msg)

            print(f"[IMAGE FLOW] Execução concluída: {len(result.get('images', []))} imagens")

            images = result.get("images", [])
            processed_images = []

            for img in images:
                img_copy = img.copy()
                if "base64" in img_copy and isinstance(img_copy["base64"], bytes):
                    img_copy["base64"] = base64.b64encode(img_copy["base64"]).decode("utf-8")
                processed_images.append(img_copy)

            yield {
                "type": "image_result",
                "stage": "executor",
                "data": {
                    "text": result.get("text", ""),
                    "images": processed_images,
                    "models_used": result.get("models_used", {}),
                },
                "complete": False,
            }

            completed = True

            yield {
                "type": "flow_complete",
                "stage": "complete",
                "data": {
                    "flow_type": "image",
                    "agent_id": agent_data.get("_id", {}).get("$oid"),
                    "models_used": result.get("models_used", {}),
                    "images_count": len(processed_images),
                    "has_images": len(processed_images) > 0,
                },
                "complete": True,
            }

            yield {
                "type": "all_loaded",
                "stage": "complete",
                "data": {
                    "status": "complete",
                    "session_id": session_id,
                    "has_response": bool(result.get("text")),
                    "has_images": len(processed_images) > 0,
                    "images_count": len(processed_images),
                    "flow_type": "image",
                },
                "complete": True,
            }

        except ImportError as e:
            error_message = f"Erro ao importar executor_image: {str(e)}"
            print(f"[IMAGE FLOW] {error_message}")
            traceback.print_exc()
            yield {
                "type": "error",
                "stage": "executor",
                "error": error_message,
                "complete": True,
            }
        except Exception as e:
            error_message = str(e)
            print(f"[IMAGE FLOW] Erro durante execução: {error_message}")
            traceback.print_exc()
            yield {
                "type": "error",
                "stage": "executor",
                "error": error_message,
                "complete": True,
            }
        finally:
            if self.pg_user_id:
                asyncio.create_task(
                    self.billing_service.register_credits_usage(
                        user_id=self.pg_user_id,
                        model_id=int(model_id),
                        credit_type="subscription",
                        credits_used=int(self.execution_cost),
                        usage_reason="image_generation",
                        usage_metadata={
                            "session_id": session_id,
                            "agent_id": agent_data.get("_id", {}).get("$oid"),
                            "flow_type": "image",
                            "completed": completed,
                            "error": error_message,
                            "image_models": [m.get("model_name") for m in image_models],
                            "images_generated": len(result.get("images", [])) if "result" in locals() else 0,
                        },
                    )
                )


# =====================================================
# ENTRYPOINT
# =====================================================

async def execute_chat_agent_streaming(
    request_data: Dict[str, Any],
    user_jwt: str,
    user_id: Optional[str] = None,
    files: Optional[Dict[str, Any]] = None,
    db=None,
) -> AsyncGenerator[Dict[str, Any], None]:

    print(f"\n{'='*60}")
    print(f"[ENTRYPOINT] execute_chat_agent_streaming")
    print(f"[ENTRYPOINT] user_id: {user_id}")
    print(f"[ENTRYPOINT] files recebido: {files is not None}")
    if files:
        print(f"[ENTRYPOINT]   files keys: {list(files.keys())}")
        file_list = files.get("files", [])
        print(f"[ENTRYPOINT]   total_files: {len(file_list)}")
    print(f"{'='*60}\n")

    agent = ChatAgentStreaming(
        user_jwt=user_jwt,
        user_id=user_id,
        db=db,
    )

    try:
        async for event in agent.run_streaming(request_data, files):
            if isinstance(event, dict):
                event["timestamp"] = datetime.now().isoformat()
            yield event

    except Exception as e:
        print(f"[ENTRYPOINT] Erro crítico: {e}")
        traceback.print_exc()
        yield {
            "type": "error",
            "stage": "entrypoint",
            "error": f"Erro crítico no chat agent: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "complete": True,
        }