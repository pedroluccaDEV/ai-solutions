# features/channels/webhook_saphien/agent/saphien_agent.py
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import os

from features.channels.webhook_saphien.agent.saphien_builder import build_saphien_agent
from features.channels.webhook_saphien.agent.saphien_planner import run_saphien_planner
from features.channels.webhook_saphien.agent.saphien_executor import run_saphien_executor
from services.v1.billing_service import get_billing_service


# =====================================================
# AGENT
# =====================================================

class SaphienAgent:

    def __init__(
        self,
        user_jwt: str,
        user_id: Optional[str] = None,
        db=None,
    ):
        self.user_jwt = user_jwt
        self.user_id = user_id
        self.db = db
        self.billing_service = get_billing_service()

        self.pg_user_id: Optional[int] = None
        self.execution_cost: int = 0

    # =====================================================
    # BILLING
    # =====================================================

    async def _billing_before(
        self,
        firebase_uid: str,
        model_id: str,
        session_id: str,
    ):
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

        return {"authorized": True}

    # =====================================================
    # MAIN (SEM STREAMING)
    # =====================================================

    async def run(
        self,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        firebase_uid = request_data.get("user_id")
        agent_id = request_data.get("agent_id")
        message = request_data.get("message", "")
        session_id = request_data.get("session_id") or f"saphien_{int(datetime.now().timestamp())}"
        conversation_history = request_data.get("conversation_history", [])
        widget_token = request_data.get("widget_token")
        session_id_frontend = request_data.get("session_id_frontend")

        if not firebase_uid or not agent_id or not message:
            return {"success": False, "error": "Dados obrigatórios ausentes"}

        completed = False
        error_message = None
        full_response = ""
        total_input_t = 0
        total_output_t = 0
        model_used = None

        try:
            # ================= BUILDER =================
            builder_result = await build_saphien_agent(
                agent_id=agent_id,
                user_id=firebase_uid,
                session_id=session_id,
                db=self.db,
            )

            agent_data = builder_result.get("agent", {})
            model_id = builder_result.get("model_id", "1")

            # ================= BILLING =================
            billing = await self._billing_before(
                firebase_uid,
                model_id,
                session_id,
            )

            if not billing["authorized"]:
                return {"success": False, "error": billing["message"]}

            # ================= PLANNER =================
            planner_result = await asyncio.to_thread(
                run_saphien_planner,
                user_prompt=message,
                agent_data=agent_data,
                kb_meta=builder_result["resources"].get("knowledgeBase", []),
                tools_meta=builder_result["resources"].get("tools", []),
                mcp_meta=builder_result["resources"].get("mcps", []),
                conversation_history=conversation_history,
            )

            # ================= EXECUTOR =================
            executor_result = await run_saphien_executor(
                agent_id=agent_id,
                prompt=planner_result.get("planner_response", message),
                user_id=firebase_uid,
                resources={
                    "agent": agent_data,
                    "tools": builder_result["resources"].get("tools", []),
                    "mcps": builder_result["resources"].get("mcps", []),
                    "knowledge_bases": builder_result["resources"].get("knowledgeBase", []),
                    "builder_model": builder_result["resources"]["builder_model"],
                    "context": {
                        **builder_result.get("context", {}),
                        "session_id": session_id,
                        "conversation_history": conversation_history,
                    },
                },
                resources_analyzed=planner_result.get("resources_analyzed", {}),
            )

            full_response = executor_result.get("response", "")
            total_input_t = executor_result.get("input_tokens", 0)
            total_output_t = executor_result.get("output_tokens", 0)
            model_used = executor_result.get("model_used")

            completed = True

            return {
                "success": True,
                "response": full_response,
                "model_used": model_used,
                "tokens": {
                    "input": total_input_t,
                    "output": total_output_t,
                    "total": total_input_t + total_output_t,
                },
            }

        except Exception as e:
            error_message = str(e)
            traceback.print_exc()

            return {
                "success": False,
                "error": error_message,
                "partial_response": full_response,
            }

        finally:
            if self.pg_user_id:
                asyncio.create_task(
                    self.billing_service.register_credits_usage(
                        user_id=self.pg_user_id,
                        model_id=int(model_id),
                        credit_type="subscription",
                        credits_used=int(self.execution_cost),
                        usage_reason="saphien_agent",
                        usage_metadata={
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "widget_token": widget_token,
                            "session_id_frontend": session_id_frontend,
                            "completed": completed,
                            "error": error_message,
                        },
                    )
                )


# =====================================================
# ENTRYPOINT
# =====================================================

async def execute_saphien_agent(
    request_data: Dict[str, Any],
    user_jwt: str,
    user_id: Optional[str] = None,
    db=None,
) -> Dict[str, Any]:

    agent = SaphienAgent(
        user_jwt=user_jwt,
        user_id=user_id,
        db=db,
    )

    return await agent.run(request_data)