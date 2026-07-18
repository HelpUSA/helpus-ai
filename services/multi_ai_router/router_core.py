from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

MODELS=frozenset({"helpus-fast","helpus-general","helpus-reasoner","helpus-code","helpus-vision","helpus-verifier"})
MODES=frozenset({"auto","single","review","council"})
CODE=("code","código","python","javascript","typescript","powershell","sql","api","bug","erro","repositório","commit","deploy","docker","migration")
REASON=("analisar","análise","compare","estratégia","arquitetura","planejamento","hipótese","investigue","raciocínio")
RISK=("médico","saúde","jurídico","financeiro","produção","excluir","pagamento","segurança","credencial")
COUNCIL=("pesquisa profunda","conselho","múltiplas hipóteses","arquitetura completa")

@dataclass(frozen=True)
class Profile:
    category:str
    complexity:str
    risk:str
    has_vision:bool
    text_length:int

@dataclass(frozen=True)
class Plan:
    mode:str
    primary:str
    contributors:Tuple[str,...]
    reviewer:Optional[str]
    finalizer:Optional[str]
    profile:Profile

def normalize(messages:Sequence[Dict[str,Any]]):
    parts:List[str]=[]; vision=False
    for message in messages:
        content=message.get("content","")
        if isinstance(content,str): parts.append(content); continue
        if isinstance(content,list):
            for item in content:
                if not isinstance(item,dict): continue
                if str(item.get("type","")).lower() in {"image","image_url","input_image"}: vision=True
                if isinstance(item.get("text"),str): parts.append(item["text"])
    return "\n".join(parts).strip(),vision

def has(text:str,terms): return any(term in text.lower() for term in terms)

def classify(messages):
    text,vision=normalize(messages)
    category="vision" if vision else "code" if has(text,CODE) else "reasoning" if has(text,REASON) else "general"
    complexity="high" if has(text,COUNCIL) or len(text)>6000 else "medium" if category in {"code","reasoning"} or len(text)>1800 else "low"
    risk="high" if has(text,RISK) else "normal"
    return Profile(category,complexity,risk,vision,len(text))

def select_route(messages,requested_mode="auto",requested_model=None):
    mode=requested_mode.lower().strip()
    if mode not in MODES: raise ValueError("unsupported routing mode")
    if requested_model is not None and requested_model not in MODELS: raise ValueError("unsupported model alias")
    p=classify(messages)
    primary=requested_model or ("helpus-vision" if p.category=="vision" else "helpus-code" if p.category=="code" else "helpus-reasoner" if p.category=="reasoning" else "helpus-fast" if p.complexity=="low" else "helpus-general")
    if mode=="auto": mode="council" if p.complexity=="high" else "review" if p.risk=="high" else "single"
    if mode=="single": return Plan(mode,primary,(),None,None,p)
    if mode=="review": return Plan(mode,primary,(),"helpus-verifier","helpus-general",p)
    contributors=[]
    for alias in (primary,"helpus-reasoner","helpus-code","helpus-general"):
        if alias not in contributors: contributors.append(alias)
    return Plan(mode,primary,tuple(contributors[:3]),"helpus-verifier","helpus-general",p)

def metadata(plan):
    return {"mode":plan.mode,"primary":plan.primary,"contributors":list(plan.contributors),"reviewer":plan.reviewer,"finalizer":plan.finalizer,"profile":plan.profile.__dict__}
