import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.multi_ai_router.router_core import select_route

class Tests(unittest.TestCase):
    def test_fast(self): self.assertEqual(select_route([{"role":"user","content":"Resuma."}]).primary,"helpus-fast")
    def test_code(self): self.assertEqual(select_route([{"role":"user","content":"Analise este código Python."}]).primary,"helpus-code")
    def test_review(self): self.assertEqual(select_route([{"role":"user","content":"Analise a segurança em produção."}]).mode,"review")
    def test_council(self): self.assertEqual(select_route([{"role":"user","content":"Faça uma arquitetura completa com múltiplas hipóteses."}]).mode,"council")
    def test_vision(self): self.assertEqual(select_route([{"role":"user","content":[{"type":"text","text":"Analise."},{"type":"image_url","image_url":{"url":"x"}}]}]).primary,"helpus-vision")
    def test_invalid_alias(self):
        with self.assertRaises(ValueError): select_route([{"role":"user","content":"Olá"}],requested_model="physical-model")

if __name__=="__main__": unittest.main()
