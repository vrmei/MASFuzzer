"""Persistent Microsoft AutoGen (v0.4+) server (runs in the autogen venv).

Same line protocol as serve_langgraph.py. A REAL AutoGen RoundRobinGroupChat team orchestrates the
auditor->decider turn order (the auditor speaks first, the decider second and sees the auditor's audit in the
shared team context -- i.e. it anchors on the upstream verdict). AutoGen's OpenAIChatCompletionClient does the
OpenRouter calls (model_info supplied, as required for non-OpenAI model slugs).
"""
import os, sys, json, asyncio
os.environ["ANONYMIZED_TELEMETRY"] = "false"

KEY = os.environ.get("OPENROUTER_API_KEY_2") or os.environ.get("OPENROUTER_API_KEY")
BASE = "https://openrouter.ai/api/v1"

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily

_real_stdout = sys.stdout
sys.stdout = sys.stderr


def emit(obj):
    _real_stdout.write(json.dumps(obj) + "\n"); _real_stdout.flush()


def _client(model):
    return OpenAIChatCompletionClient(
        model=model, base_url=BASE, api_key=KEY, temperature=0.1,
        model_info=ModelInfo(vision=False, function_calling=True, json_output=False,
                             family=ModelFamily.UNKNOWN, structured_output=False))


STATE = {}


def build(cfg):
    aud = AssistantAgent("auditor", model_client=_client(cfg["aud_model"]), system_message=cfg["aud_sop"])
    dec = AssistantAgent("decider", model_client=_client(cfg["dec_model"]), system_message=cfg["dec_sop"])
    STATE["aud"] = aud
    STATE["dec"] = dec


async def run_once(payload, ctx):
    aud, dec = STATE["aud"], STATE["dec"]
    await aud.on_reset(None)
    await dec.on_reset(None)
    team = RoundRobinGroupChat([aud, dec], termination_condition=MaxMessageTermination(3))
    task = (f"Incident context: {ctx}\nUser Input: {payload}\n"
            "auditor: assess the request per your policy. decider: then issue the final action.")
    res = await team.run(task=task)
    audit = decision = ""
    for m in res.messages:
        src = getattr(m, "source", "")
        content = m.content if isinstance(getattr(m, "content", ""), str) else str(getattr(m, "content", ""))
        if src == "auditor":
            audit = content
        elif src == "decider":
            decision = content
    return audit, decision


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    built = False
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if not built:
                build(req); built = True
                emit({"ready": True}); continue
            audit, decision = loop.run_until_complete(run_once(req["payload"], req.get("ctx", "SRE incident")))
            emit({"audit": audit, "decision": decision})
        except Exception as e:
            emit({"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    main()
