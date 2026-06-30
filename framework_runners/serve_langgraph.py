"""Persistent LangGraph supervisor server (runs in the langgraph venv).

Protocol (one JSON object per line on stdin -> one JSON object per line on stdout):
  first line  : {"aud_model","dec_model","aud_sop","dec_sop"}     # build the graph once
  each next   : {"payload","ctx","seed"}                          # -> {"audit","decision"} or {"error"}
A REAL LangGraph StateGraph (compiled graph + typed state + node execution) orchestrates a fixed
auditor->decider edge; LangChain ChatOpenAI does the OpenRouter calls. The decider anchors on the
auditor's verdict -- the supervisor/Manager-Worker structure -- and the auditor always runs so its
certainty (the fuzzer's fitness) is measurable.
"""
import os, sys, json
from typing import TypedDict
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

KEY = os.environ.get("OPENROUTER_API_KEY_2") or os.environ.get("OPENROUTER_API_KEY")
BASE = "https://openrouter.ai/api/v1"

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

_real_stdout = sys.stdout
sys.stdout = sys.stderr   # keep any framework chatter off the protocol channel


def emit(obj):
    _real_stdout.write(json.dumps(obj) + "\n"); _real_stdout.flush()


class S(TypedDict):
    payload: str
    ctx: str
    seed: int
    audit: str
    decision: str


def build(cfg):
    aud = ChatOpenAI(model=cfg["aud_model"], base_url=BASE, api_key=KEY, temperature=0.1, max_retries=4)
    dec = ChatOpenAI(model=cfg["dec_model"], base_url=BASE, api_key=KEY, temperature=0.1, max_retries=4)
    aud_sop, dec_sop = cfg["aud_sop"], cfg["dec_sop"]

    def auditor_node(s: S) -> dict:
        r = aud.invoke([SystemMessage(aud_sop),
                        HumanMessage(f"Analyze in context: {s['ctx']}\nUser Input: {s['payload']}")],
                       config={"seed": s.get("seed", 1)})
        return {"audit": r.content}

    def decider_node(s: S) -> dict:
        r = dec.invoke([SystemMessage(dec_sop),
                        HumanMessage(f"Audit assessment received. Determine the final action:\n{s['audit']}")])
        return {"decision": r.content}

    g = StateGraph(S)
    g.add_node("auditor", auditor_node)
    g.add_node("decider", decider_node)
    g.add_edge(START, "auditor")
    g.add_edge("auditor", "decider")
    g.add_edge("decider", END)
    return g.compile()


def main():
    app = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if app is None:
                app = build(req)
                emit({"ready": True})
                continue
            out = app.invoke({"payload": req["payload"], "ctx": req.get("ctx", "SRE incident"),
                              "seed": int(req.get("seed", 1)), "audit": "", "decision": ""})
            emit({"audit": out["audit"], "decision": out["decision"]})
        except Exception as e:
            emit({"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    main()
