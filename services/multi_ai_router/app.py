import asyncio,json,os,time,uuid
from typing import Any,Dict,Optional
import httpx
from fastapi import FastAPI,Header,HTTPException,Request
from fastapi.responses import JSONResponse
from .router_core import metadata,select_route

BASE=os.getenv("HELPUS_GATEWAY_BASE_URL","http://litellm:4000/v1").rstrip("/")
GATEWAY_KEY=os.getenv("HELPUS_GATEWAY_API_KEY","")
ROUTER_KEY=os.getenv("HELPUS_ROUTER_API_KEY","")
DEFAULT_MODE=os.getenv("HELPUS_DEFAULT_MODE","auto")
VERIFY=os.getenv("HELPUS_COUNCIL_VERIFY","true").lower() in {"1","true","yes","on"}
TIMEOUT=float(os.getenv("HELPUS_GATEWAY_TIMEOUT_SECONDS","180"))
app=FastAPI(title="AI HelpUS Multi-AI Router",version="1.0.0")

def auth(value):
    if ROUTER_KEY and value!="Bearer "+ROUTER_KEY: raise HTTPException(401,"invalid router credential")

def content(response):
    try: value=response["choices"][0]["message"]["content"]
    except (KeyError,IndexError,TypeError) as exc: raise HTTPException(502,"invalid gateway response") from exc
    return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)

def payload(body,model,messages=None):
    result={k:v for k,v in body.items() if k not in {"helpus_mode","helpus_task","helpus_metadata"}}
    result["model"]=model; result["stream"]=False
    if messages is not None: result["messages"]=messages
    return result

async def gateway(data):
    headers={"Content-Type":"application/json"}
    if GATEWAY_KEY: headers["Authorization"]="Bearer "+GATEWAY_KEY
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response=await client.post(BASE+"/chat/completions",headers=headers,json=data)
    if response.status_code>=400: raise HTTPException(502,{"gateway_status":response.status_code,"gateway_error":response.text[:1000]})
    result=response.json()
    if not isinstance(result,dict): raise HTTPException(502,"invalid gateway JSON")
    return result

def verify_messages(messages,candidate):
    return [{"role":"system","content":"You are the independent AI HelpUS verifier. Check contradictions, unsupported claims, missing constraints, unsafe assumptions, scope violations and invented execution receipts. Return only JSON with approved, severity, findings and repair_instruction."},{"role":"user","content":json.dumps({"messages":messages,"candidate":candidate},ensure_ascii=False)}]

def verdict(response):
    try: data=json.loads(content(response))
    except json.JSONDecodeError: data={}
    return {"approved":bool(data.get("approved",False)),"severity":str(data.get("severity","medium")),"findings":list(data.get("findings",["Verifier returned invalid JSON."])),"repair_instruction":str(data.get("repair_instruction","Correct all identified issues."))}

def repair_messages(messages,candidate,review):
    return [{"role":"system","content":"You are the AI HelpUS finalizer. Repair the candidate using the verification. Never invent tool or execution receipts."},{"role":"user","content":json.dumps({"messages":messages,"candidate":candidate,"verification":review},ensure_ascii=False)}]

def council_messages(messages,items):
    return [{"role":"system","content":"You are the AI HelpUS council finalizer. Reconcile specialists and produce one coherent answer. Never claim execution without a real receipt."},{"role":"user","content":json.dumps({"messages":messages,"specialists":items},ensure_ascii=False)}]

@app.get("/healthz")
async def healthz(): return {"status":"healthy","service":"AI HelpUS Multi-AI Router"}

@app.get("/readyz")
async def readyz(): return {"status":"ready","gateway_configured":bool(BASE)}

@app.get("/v1/models")
async def models(authorization:Optional[str]=Header(default=None)):
    auth(authorization)
    aliases=["helpus-fast","helpus-general","helpus-reasoner","helpus-code","helpus-vision","helpus-verifier"]
    return {"object":"list","data":[{"id":x,"object":"model","owned_by":"helpus"} for x in aliases]}

@app.post("/v1/chat/completions")
async def chat(request:Request,authorization:Optional[str]=Header(default=None),x_helpus_mode:Optional[str]=Header(default=None)):
    auth(authorization)
    body=await request.json()
    messages=body.get("messages")
    if not isinstance(messages,list) or not messages: raise HTTPException(400,"messages must be a non-empty array")
    if body.get("stream") is True: raise HTTPException(400,"streaming is not enabled")
    model=None if body.get("model")=="auto" else body.get("model")
    try: plan=select_route(messages,x_helpus_mode or body.get("helpus_mode") or DEFAULT_MODE,model)
    except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    request_id="helpus-"+uuid.uuid4().hex; started=time.perf_counter(); review=None
    if plan.mode=="single":
        final=await gateway(payload(body,plan.primary))
    elif plan.mode=="review":
        primary=await gateway(payload(body,plan.primary)); candidate=content(primary)
        review=verdict(await gateway(payload(body,plan.reviewer,verify_messages(messages,candidate))))
        final=primary if review["approved"] else await gateway(payload(body,plan.finalizer,repair_messages(messages,candidate,review)))
    else:
        async def call(alias):
            specialist=[{"role":"system","content":"You are an AI HelpUS specialist. Analyze independently. Never invent execution receipts."},{"role":"user","content":json.dumps({"alias":alias,"messages":messages},ensure_ascii=False)}]
            response=await gateway(payload(body,alias,specialist))
            return {"alias":alias,"content":content(response)}
        items=await asyncio.gather(*[call(alias) for alias in plan.contributors])
        final=await gateway(payload(body,plan.finalizer,council_messages(messages,items)))
        if VERIFY:
            candidate=content(final)
            review=verdict(await gateway(payload(body,plan.reviewer,verify_messages(messages,candidate))))
            if not review["approved"]: final=await gateway(payload(body,plan.finalizer,repair_messages(messages,candidate,review)))
    result=dict(final)
    result["_helpus"]={"request_id":request_id,"route":metadata(plan),"elapsed_ms":int((time.perf_counter()-started)*1000),"verification":review}
    return JSONResponse(result,headers={"X-HelpUS-Request-ID":request_id,"X-HelpUS-Mode":plan.mode})
