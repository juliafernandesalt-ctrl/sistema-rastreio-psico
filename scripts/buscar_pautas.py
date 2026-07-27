
import os
import json
import re
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

Retorne EXATAMENTE 6 pautas de conteúdo (não mais que isso), cada uma com estes campos,
em formato JSON (lista de objetos):
- titulo: título curto e chamativo
- tema: assunto principal
- descricao: 1 a 2 frases curtas explicando a ideia e o ângulo do conteúdo
- formato: "reel", "carrossel" ou "story"
- fonte: de onde veio a referência (perfil, site, etc)
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
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
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
