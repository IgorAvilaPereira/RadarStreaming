"""Catálogo local inicial e referências para comparação de streamings."""

GENRES = ["Drama", "Comédia", "Ficção científica", "Suspense", "Fantasia", "Documentário", "Aventura"]

# Títulos reais para o primeiro uso. Disponibilidade regional pode mudar; por isso,
# só os serviços de origem estáveis aparecem como provedores confirmados.
TITLES = [
    {
        "id": "seed_silo", "title": "Silo", "kind": "Série", "year": 2023,
        "genres": ["Ficção científica", "Drama", "Suspense"],
        "synopsis": "Em um futuro tóxico, milhares de pessoas vivem sob a terra e tentam descobrir a verdade sobre o silo.",
        "providers": ["Apple TV+"], "poster": "poster_silo.svg",
    },
    {
        "id": "seed_stranger_things", "title": "Stranger Things", "kind": "Série", "year": 2016,
        "genres": ["Ficção científica", "Fantasia", "Suspense"],
        "synopsis": "O desaparecimento de um garoto revela experimentos secretos e uma dimensão perigosa em Hawkins.",
        "providers": ["Netflix"], "poster": "poster_stranger.svg",
    },
    {
        "id": "seed_odyssey", "title": "A Odisseia", "kind": "Filme", "year": 2026,
        "genres": ["Aventura", "Drama", "Fantasia"],
        "synopsis": "Adaptação cinematográfica do poema épico de Homero, dirigida por Christopher Nolan.",
        "providers": [], "poster": "poster_odisseia.svg",
    },
    {
        "id": "seed_spiderman_nwh", "title": "Homem-Aranha: Sem Volta para Casa", "kind": "Filme", "year": 2021,
        "genres": ["Aventura", "Ficção científica"],
        "synopsis": "Peter Parker pede ajuda para proteger sua identidade, mas um feitiço abre caminho para outros universos.",
        "providers": [], "poster": "poster_spiderman.svg",
    },
    {
        "id": "seed_severance", "title": "Ruptura", "kind": "Série", "year": 2022,
        "genres": ["Ficção científica", "Suspense", "Drama"],
        "synopsis": "Funcionários de uma empresa passam por um procedimento que separa as memórias do trabalho e da vida pessoal.",
        "providers": ["Apple TV+"], "poster": "poster_ruptura.svg",
    },
    {
        "id": "seed_wednesday", "title": "Wandinha", "kind": "Série", "year": 2022,
        "genres": ["Fantasia", "Suspense", "Comédia"],
        "synopsis": "Na Academia Nunca Mais, Wandinha investiga mistérios enquanto tenta controlar seus poderes psíquicos.",
        "providers": ["Netflix"], "poster": "poster_wandinha.svg",
    },
    {
        "id": "seed_the_last_of_us", "title": "The Last of Us", "kind": "Série", "year": 2023,
        "genres": ["Drama", "Aventura", "Ficção científica"],
        "synopsis": "Em um mundo devastado por uma pandemia, Joel e Ellie atravessam os Estados Unidos em busca de esperança.",
        "providers": ["Max"], "poster": "poster_lastofus.svg",
    },
    {
        "id": "seed_fallout", "title": "Fallout", "kind": "Série", "year": 2024,
        "genres": ["Ficção científica", "Aventura", "Drama"],
        "synopsis": "Séculos após uma guerra nuclear, moradores de um abrigo subterrâneo encontram um mundo radicalmente diferente.",
        "providers": ["Prime Video"], "poster": "poster_fallout.svg",
    },
    {
        "id": "seed_percy_jackson", "title": "Percy Jackson e os Olimpianos", "kind": "Série", "year": 2023,
        "genres": ["Fantasia", "Aventura"],
        "synopsis": "Percy descobre que é filho de Poseidon e parte em uma missão pelo mundo dos deuses gregos.",
        "providers": ["Disney+"], "poster": "poster_percy.svg",
    },
    {
        "id": "seed_house_dragon", "title": "A Casa do Dragão", "kind": "Série", "year": 2022,
        "genres": ["Fantasia", "Drama", "Aventura"],
        "synopsis": "A disputa pela sucessão dos Targaryen ameaça dividir Westeros e seus dragões.",
        "providers": ["Max"], "poster": "poster_dragon.svg",
    },
    {
        "id": "seed_black_mirror", "title": "Black Mirror", "kind": "Série", "year": 2011,
        "genres": ["Ficção científica", "Drama", "Suspense"],
        "synopsis": "Histórias independentes exploram como a tecnologia pode transformar relações e escolhas humanas.",
        "providers": ["Netflix"], "poster": "poster_black_mirror.svg",
    },
    {
        "id": "seed_one_piece", "title": "One Piece", "kind": "Série", "year": 2023,
        "genres": ["Aventura", "Fantasia", "Comédia"],
        "synopsis": "Monkey D. Luffy parte em uma jornada pelos mares para encontrar o lendário tesouro One Piece.",
        "providers": ["Netflix"], "poster": "poster_one_piece.svg",
    },
    {
        "id": "seed_bridgerton", "title": "Bridgerton", "kind": "Série", "year": 2020,
        "genres": ["Drama", "Comédia"],
        "synopsis": "Na alta sociedade londrina, os irmãos Bridgerton vivem romances e disputas sob o olhar de uma cronista anônima.",
        "providers": ["Netflix"], "poster": "poster_bridgerton.svg",
    },
    {
        "id": "seed_the_boys", "title": "The Boys", "kind": "Série", "year": 2019,
        "genres": ["Aventura", "Ficção científica", "Drama"],
        "synopsis": "Um grupo de vigilantes tenta expor super-heróis poderosos que escondem um lado sombrio.",
        "providers": ["Prime Video"], "poster": "poster_the_boys.svg",
    },
    {
        "id": "seed_reacher", "title": "Reacher", "kind": "Série", "year": 2022,
        "genres": ["Aventura", "Suspense", "Drama"],
        "synopsis": "Um ex-investigador militar itinerante usa sua experiência para desvendar crimes e conspirações.",
        "providers": ["Prime Video"], "poster": "poster_reacher.svg",
    },
    {
        "id": "seed_loki", "title": "Loki", "kind": "Série", "year": 2021,
        "genres": ["Ficção científica", "Fantasia", "Aventura"],
        "synopsis": "Após escapar com o Tesseract, Loki é recrutado por uma organização que protege as linhas do tempo.",
        "providers": ["Disney+"], "poster": "poster_loki.svg",
    },
    {
        "id": "seed_mandalorian", "title": "The Mandalorian", "kind": "Série", "year": 2019,
        "genres": ["Ficção científica", "Aventura", "Drama"],
        "synopsis": "Um caçador de recompensas atravessa a galáxia protegendo uma criança sensível à Força.",
        "providers": ["Disney+"], "poster": "poster_mandalorian.svg",
    },
    {
        "id": "seed_ted_lasso", "title": "Ted Lasso", "kind": "Série", "year": 2020,
        "genres": ["Comédia", "Drama"],
        "synopsis": "Um treinador de futebol americano assume um clube inglês e conquista o time com otimismo e empatia.",
        "providers": ["Apple TV+"], "poster": "poster_ted_lasso.svg",
    },
    {
        "id": "seed_foundation", "title": "Fundação", "kind": "Série", "year": 2021,
        "genres": ["Ficção científica", "Drama"],
        "synopsis": "Um matemático prevê a queda de um império galáctico e planeja preservar o conhecimento da humanidade.",
        "providers": ["Apple TV+"], "poster": "poster_foundation.svg",
    },
    {
        "id": "seed_white_lotus", "title": "The White Lotus", "kind": "Série", "year": 2021,
        "genres": ["Drama", "Comédia", "Suspense"],
        "synopsis": "Hóspedes e funcionários de resorts de luxo se envolvem em relações tensas e situações inesperadas.",
        "providers": ["Max"], "poster": "poster_white_lotus.svg",
    },
]

# Valores de referência; planos e preços variam por região e modalidade.
PRICE_SOURCES = {
    "Netflix": "https://www.netflix.com/br/",
    "Prime Video": "https://www.primevideo.com/",
    "Disney+": "https://www.disneyplus.com/pt-br",
    "Max": "https://www.max.com/br/pt",
    "Apple TV+": "https://www.apple.com/br/apple-tv-plus/",
}

STREAMING_SERVICES = [
    {"name": "Netflix", "monthly_price": 20.90, "genres": ["Drama", "Comédia", "Ficção científica", "Suspense", "Fantasia"]},
    {"name": "Prime Video", "monthly_price": 19.90, "genres": ["Drama", "Comédia", "Ficção científica", "Aventura", "Suspense"]},
    {"name": "Disney+", "monthly_price": 27.90, "genres": ["Fantasia", "Aventura", "Documentário", "Comédia", "Drama"]},
    {"name": "Max", "monthly_price": 29.90, "genres": ["Drama", "Suspense", "Ficção científica", "Aventura"]},
    {"name": "Apple TV+", "monthly_price": 21.90, "genres": ["Ficção científica", "Drama", "Documentário", "Aventura"]},
]
