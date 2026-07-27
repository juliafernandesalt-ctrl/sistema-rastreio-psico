import os
import json
import requests
from datetime import datetime

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

PROMPT = """
Você é um assistente de pesquisa de conteúdo para uma criadora de conteúdo sobre psicologia,
voltada para estudantes de psicologia, vida acadêmica e curiosidades da área.

Pesquise na web por conteúdos, temas e formatos em alta AGORA sobre:
- Psicologia (temas, teorias, curiosidades que estão viralizando)
- Vida acadêmica de estudantes de psicologia
- Livros de psicologia populares ou comentados recentemente
- Formatos de Reels e carrosséis performando bem em contas de psicologia

Retorne EXATAMENTE 8 pautas de conteúdo, cada uma com estes campos, em formato JSON (lista de objetos):
- titulo: título curto e chamativo
- tema: assunto principal
- descricao: 2 a 3 frases explicando a ideia e o ângulo do conteúdo
- formato: "reel", "carrossel" ou "story"
- fonte: de onde veio a referência (perfil, site, etc)
- link_referencia: link da fonte, se houver
- status: sempre "novo"

Responda APENAS com o JSON válido, sem texto antes ou depois, sem markdown.
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
            "max_tokens": 4096,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    texto_completo = "".join(
        bloco["text"] for bloco in data["content"] if bloco["type"] == "text"
    )

    texto_limpo = texto_completo.strip()
    if texto_limpo.startswith("```"):
        texto_limpo = texto_limpo.split("```")[1]
        if texto_limpo.startswith("json"):
            texto_limpo = texto_limpo[4:]

    return json.loads(texto_limpo)


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
