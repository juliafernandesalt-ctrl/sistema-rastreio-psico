import os
import json
import re
import requests
from datetime import datetime

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


def buscar_descartes_recentes():
    """Pega os últimos temas/títulos que Julia descartou, pra evitar repetir o padrão."""
    url = (
        f"{SUPABASE_URL}/rest/v1/pautas_conteudo"
        f"?select=titulo,tema&status=eq.descartado&order=created_at.desc&limit=20"
        f"&apikey={SUPABASE_KEY}"
    )
    response = requests.get(url, timeout=30)
    if not response.ok:
        return []
    return response.json()


def montar_prompt(descartes):
    bloco_descartes = ""
    if descartes:
        linhas = "\n".join(f'- "{d["titulo"]}" (tema: {d["tema"]})' for d in descartes)
        bloco_descartes = f"""
IMPORTANTE — Julia já descartou estas pautas em semanas anteriores, porque não gostou
do ângulo, tema ou estilo delas. NÃO repita temas ou abordagens parecidas com estas:
{linhas}

Aprenda com esse padrão de rejeição: evite temas, ângulos ou formatos semelhantes aos
descartados acima, e prefira variações claramente diferentes.
"""

    return f"""
Você é um assistente de pesquisa de conteúdo para uma criadora de conteúdo no Instagram
(@juliaalt.psi), cujo público é ESTUDANTES DE PSICOLOGIA.

Seu foco é o Instagram especificamente. Pesquise ativamente por:
- Vídeos educativos sobre psicologia que estão em alta
- Memes de psicologia/vida acadêmica que estão circulando
- Vlogs de estudantes de psicologia (rotina, dia a dia, bastidores da faculdade)
- Carrosséis sobre psicologia performando bem

Formule buscas específicas incluindo termos como "instagram", "reels", "carrossel" e o ano atual,
por exemplo: "psicologia instagram reels tendência 2026", "meme psicologia instagram",
"vlog estudante de psicologia instagram", "carrossel psicologia instagram viral 2026".

Regras importantes:
- IGNORE resultados de blogs, sites de notícias genéricos ou artigos de SEO antigos.
- IGNORE qualquer conteúdo com mais de 3 meses de idade. Se não tiver certeza da data,
  prefira descartar a fazer pautas com conteúdo desatualizado.
- Priorize o que está sendo postado e comentado NO INSTAGRAM agora, não o que
  aparece em listas de blog sobre "tendências de psicologia".
- Traga psicologia num sentido AMPLO (teorias, curiosidades, casos, humor, rotina
  acadêmica) — não fique presa só em temas de TCC/estágio. Varie os ângulos.
- Varie também os formatos entre as 6 pautas: não traga todas do mesmo tipo
  (por exemplo, misture pelo menos um meme, um vlog/reel de rotina e um carrossel
  educativo, não só carrosséis de burocracia acadêmica).
{bloco_descartes}
Retorne EXATAMENTE 6 pautas de conteúdo, cada uma com estes campos, em formato JSON
(lista de objetos):
- titulo: título curto e chamativo
- tema: assunto principal
- descricao: 1 a 2 frases curtas explicando a ideia e o ângulo do conteúdo
- formato: "reel", "carrossel" ou "story"
- fonte: de onde veio a referência (perfil do Instagram, nome da conta, etc)
- link_referencia: link da fonte, se houver
- status: sempre "novo"

Seja direta e objetiva nas descrições. Responda APENAS com o JSON válido,
sem texto antes ou depois, sem markdown, sem explicações.
"""


def buscar_pautas():
    descartes = buscar_descartes_recentes()
    print(f"Descartes considerados: {len(descartes)}")

    prompt = montar_prompt(descartes)

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
            "messages": [{"role": "user", "content": prompt}],
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
