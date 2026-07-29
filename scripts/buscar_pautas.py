import os
import json
import re
import requests
from datetime import datetime

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

PROMPT = """
Você é um assistente de pesquisa de conteúdo para uma criadora de conteúdo no Instagram
(@juliaalt.psi), cujo público é especificamente ESTUDANTES DE PSICOLOGIA.

Seu foco é redes sociais, não blogs ou artigos de site. Pesquise ativamente em:
- Instagram (Reels, carrosséis, posts de contas de psicologia/estudantes de psicologia)
- TikTok (vídeos e trends sobre psicologia e vida acadêmica)

Formule buscas específicas incluindo termos como "instagram", "reels", "tiktok" e o ano atual,
por exemplo: "estudantes de psicologia instagram reels tendência 2026",
"psicologia tiktok trend 2026", "carrossel psicologia instagram viral".

Regras importantes:
- IGNORE resultados de blogs, sites de notícias genéricos ou artigos de SEO antigos.
- IGNORE qualquer conteúdo com mais de 3 meses de idade. Se não tiver certeza da data,
  prefira descartar a fazer pautas com conteúdo desatualizado.
- Priorize o que está sendo postado e comentado NAS PRÓPRIAS REDES agora, não o que
  aparece em listas de blog sobre "tendências de psicologia".
- O nicho é estudantes de psicologia especificamente (rotina de faculdade, estágio, TCC,
  vida acadêmica, curiosidades da área) — não psicologia genérica pra público leigo.

Retorne EXATAMENTE 6 pautas de conteúdo, cada uma com estes campos, em formato JSON
(lista de objetos):
- titulo: título curto e chamativo
- tema: assunto principal
- descricao: 1 a 2 frases curtas explicando a ideia e o ângulo do conteúdo
- formato: "reel", "carrossel" ou "story"
- fonte: de onde veio a referência (perfil do Instagram/TikTok, nome da conta, etc — não site genérico)
- link_referencia: link da fonte, se houver
- status: sempre "novo"

Seja direta e objetiva nas descrições. Responda APENAS com o JSON válido,
sem texto antes ou depois, sem markdown, sem explicações.
"""

def buscar_pautas():
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-5",
            "max_tokens": 8192,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=180,
    )
    response.raise_for_status()
    data = response.json()

    print(f"Motivo de parada: {data.get('stop_reason')}")

    texto_completo = "".join(
        bloco["text"] for bloco in data["content"] if bloco["type"] == "text"
    )

    match = re.search(r"\[.*\]", texto_completo, re.DOTALL)
    if not match:
        print("Resposta recebida (sem JSON encontrado):")
        print(texto_completo)
        raise ValueError("Não encontrei uma lista JSON na resposta da IA.")

    return json.loads(match.group(0))


def salvar_no_supabase(pautas):
    url = f"{SUPABASE_URL}/rest/v1/pautas_conteudo"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    response = requests.post(url, headers=headers, json=pautas, timeout=30)
    response.raise_for_status()
    print(f"{len(pautas)} pautas salvas com sucesso em {datetime.now().isoformat()}")


if __name__ == "__main__":
    pautas = buscar_pautas()
    salvar_no_supabase(pautas)
