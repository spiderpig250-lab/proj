import streamlit as st
import math
import random
from thefuzz import process
import requests
from io import StringIO
import pandas as pd
from io import BytesIO

url = "https://www.football-data.co.uk/new/BRA.csv"
headers = {"User-Agent": "Mozilla/5.0"}

r = requests.get(url, headers=headers)
print("Status:", r.status_code)
print("Primeiras 200 chars:", r.text[:200])

st.set_page_config(page_title="Comparador Tático Inteligente", layout="wide")
st.title("Comparador Tático Inteligente")

# --- 38 LIGAS (22 originais + 16 novas) - ORDENADAS POR NOME DO PAÍS
LEAGUE_CONFIG = {

    "Bundesliga": {"code": "D1", "season": "2526"},
    "2. Bundesliga": {"code": "D2", "season": "2526"},
    "Torneo De La Liga Profesional ": {"code": "ARG", "season": "2025"},
    "Austrian Bundesliga": {"code": "AUT", "season": "2025"},
    "Pro League": {"code": "B1", "season": "2526"},
    "Brasileirão": {"code": "BRA", "season": "2025"},
    "Chinese Super League": {"code": "CHN", "season": "2025"},
    "Danish Superliga": {"code": "DNK", "season": "2025"},
    "LaLiga" : {"code": "SP1", "season": "2526"},
    "LaLiga2" : {"code": "SP2", "season": "2526"},
    "Premiership": {"code": "SC0", "season": "2526"},
    "Championship": {"code": "SC1", "season": "2526"},
    "League One": {"code": "SC2", "season": "2526"},
    "League Two": {"code": "SC3", "season": "2526"},
    "Veikkausliiga": {"code": "FIN", "season": "2025"},
    "Ligue 1": {"code": "F1", "season": "2526"},
    "Ligue 2": {"code": "F2", "season": "2526"},
    "Super League": {"code": "G1", "season": "2526"},
    "Eredivisie": {"code": "N1", "season": "2526"},
    "Premier League": {"code": "E0", "season": "2526"},
    "Championship": {"code": "E1", "season": "2526"},
    "League One": {"code": "E2", "season": "2526"},
    "League Two": {"code": "E3", "season": "2526"},
    "League of Ireland Premier Division": {"code": "IRL", "season": "2025"},
    "Serie A": {"code": "I1", "season": "2526"},
    "Serie B": {"code": "I2", "season": "2526"},
    "J1 League": {"code": "JPN", "season": "2025"},
    "Liga MX": {"code": "MEX", "season": "2025"},
    "Eliteserien": {"code": "NOR", "season": "2025"},
    "Liga Portugal": {"code": "P1", "season": "2526"},
    "Ekstraklasa": {"code": "POL", "season": "2025"},
    "Romanian SuperLiga ": {"code": "ROU", "season": "2025"},
    "Russian Premier League": {"code": "RUS", "season": "2025"},
    "Allsvenskan": {"code": "SWE", "season": "2025"},
    "Super League": {"code": "SWZ", "season": "2025"},
    "Süper Lig": {"code": "T1", "season": "2526"},
    "Ukrainian Premier League": {"code": "UKR", "season": "2526"},
    "MLS": {"code": "USA", "season": "2025"},
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_euro_2024_2025():
    url = "https://www.football-data.co.uk/mmz4281/2425/all-euro-data-2024-2025.xlsx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return pd.DataFrame()
        df = pd.read_excel(BytesIO(response.content))
        return df
    except Exception as e:
        st.warning(f"Erro ao carregar dados de 2024/25: {e}")
        return pd.DataFrame()
def load_league_data(code, season, _ver=1):  # <-- adicione _ver=1
# Ligas que estão em /new/
    new_leagues_codes = {"ARG", "BRA", "MEX", "RUS", "USA", "JPN", "AUT", "CHN", "DNK", "FIN", "IRL", "NOR", "POL", "ROU", "SWE", "SWZ"}  

    if code in new_leagues_codes:
        url = f"https://www.football-data.co.uk/new/{code}.csv"
    else:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()

        # Detectar encoding com BOM
        text = response.text
        if text.startswith('\ufeff'):  # Remove BOM se presente
            text = text[1:]

        df = pd.read_csv(StringIO(text))
        return df

    except Exception as e:
        return pd.DataFrame()


def calculate_stats(df, league_name):
    if df.empty:
        return {}

    # Corrigir BOM
    if df.columns[0].startswith("ï»¿"):
        df.columns = df.columns.str.replace("ï»¿", "", regex=False)

    # Detectar layout e tipo de liga
    if 'HomeTeam' in df.columns and 'FTHG' in df.columns and 'FTR' in df.columns:
        # Liga tradicional europeia
        home_col, away_col = 'HomeTeam', 'AwayTeam'
        hg_col, ag_col = 'FTHG', 'FTAG'
        res_col = 'FTR'
        is_new_league = False
    elif 'Home' in df.columns and 'HG' in df.columns and 'Res' in df.columns:
        # Liga nova (internacional)
        home_col, away_col = 'Home', 'Away'
        hg_col, ag_col = 'HG', 'AG'
        res_col = 'Res'
        is_new_league = True
    else:
        return {}

    required = [home_col, away_col, hg_col, ag_col, res_col]
    if not all(c in df.columns for c in required):
        return {}

    # --- Filtragem por ano para ligas novas ---
    if is_new_league and 'Date' in df.columns:
        try:
            # Converter Date para datetime (formato: dd/mm/yyyy)
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            # Filtrar apenas jogos de 2025
            df = df[df['Date'].dt.year == 2025].copy()
        except Exception:
            # Se falhar, usar todos os dados (fallback)
            pass

    # Remover linhas com dados faltantes nas colunas essenciais
    df = df[required].dropna()

    # Evitar processar se não houver jogos após filtragem
    if df.empty:
        return {}

    teams = set(df[home_col].unique()) | set(df[away_col].unique())
    stats = {}

    for team in teams:
        home = df[df[home_col] == team]
        away = df[df[away_col] == team]

        total = len(home) + len(away)
        if total == 0:
            continue

        # --- Resultados gerais ---
        wins = len(home[home[res_col] == 'H']) + len(away[away[res_col] == 'A'])
        draws = len(home[home[res_col] == 'D']) + len(away[away[res_col] == 'D'])
        losses = len(home[home[res_col] == 'A']) + len(away[away[res_col] == 'H'])
        gf = home[hg_col].sum() + away[ag_col].sum()
        ga = home[ag_col].sum() + away[hg_col].sum()
        clean = len(home[home[ag_col] == 0]) + len(away[away[hg_col] == 0])
        fail = len(home[home[hg_col] == 0]) + len(away[away[ag_col] == 0])

        # --- Casa ---
        h_games = len(home)
        h_w = len(home[home[res_col] == 'H'])
        h_d = len(home[home[res_col] == 'D'])
        h_l = len(home[home[res_col] == 'A'])
        h_gf = home[hg_col].sum()
        h_ga = home[ag_col].sum()
        h_clean = len(home[home[ag_col] == 0])
        h_fail = len(home[home[hg_col] == 0])

        # --- Fora ---
        a_games = len(away)
        a_w = len(away[away[res_col] == 'A'])
        a_d = len(away[away[res_col] == 'D'])
        a_l = len(away[away[res_col] == 'H'])
        a_gf = away[ag_col].sum()
        a_ga = away[hg_col].sum()
        a_clean = len(away[away[hg_col] == 0])
        a_fail = len(away[away[ag_col] == 0])

        # --- Médias ---
        media_gm = round(gf / total, 2) if total > 0 else 0
        media_gs = round(ga / total, 2) if total > 0 else 0
        media_gm_casa = round(h_gf / h_games, 2) if h_games > 0 else 0
        media_gs_casa = round(h_ga / h_games, 2) if h_games > 0 else 0
        media_gm_fora = round(a_gf / a_games, 2) if a_games > 0 else 0
        media_gs_fora = round(a_ga / a_games, 2) if a_games > 0 else 0

        stats[team] = {
            "liga": league_name,
            "jogos": total,
            "vitorias": wins,
            "empates": draws,
            "derrotas": losses,
            "gols_marcados": gf,
            "gols_sofridos": ga,
            "sem_sofrer": clean,
            "sem_marcar": fail,
            "media_gm": media_gm,
            "media_gs": media_gs,
            "jogos_casa": h_games,
            "v_casa": h_w,
            "e_casa": h_d,
            "d_casa": h_l,
            "gm_casa": h_gf,
            "gs_casa": h_ga,
            "sem_sofrer_casa": h_clean,
            "sem_marcar_casa": h_fail,
            "media_gm_casa": media_gm_casa,
            "media_gs_casa": media_gs_casa,
            "jogos_fora": a_games,
            "v_fora": a_w,
            "e_fora": a_d,
            "d_fora": a_l,
            "gm_fora": a_gf,
            "gs_fora": a_ga,
            "sem_sofrer_fora": a_clean,
            "sem_marcar_fora": a_fail,
            "media_gm_fora": media_gm_fora,
            "media_gs_fora": media_gs_fora,
        }
    return stats



# --- CARREGAR TODAS AS EQUIPAS DE TODAS AS LIGAS ---
all_stats = {}
for lg_name, cfg in LEAGUE_CONFIG.items():
    df = load_league_data(cfg["code"], cfg["season"])
    if df.empty:
        continue  # Ignorar ligas sem dados
    lg_stats = calculate_stats(df, lg_name)
    all_stats.update(lg_stats)

# Preparar opções de equipas
team_options = []
team_map = {}
for team, stats in all_stats.items():
    label = f"{team} ({stats['liga']})"
    team_options.append(label)
    team_map[label] = {"team": team, "liga": stats["liga"], "stats": stats}

team_options.sort(key=lambda x: x.split(" (")[0].lower())


# Escolha de equipas com multiselect
home_label = st.sidebar.multiselect("Equipa da CASA", team_options, key="home_multiselect")
away_label = st.sidebar.multiselect("Equipa VISITANTE", team_options, key="away_multiselect")

# Verificar se foi selecionada exatamente uma equipa
if len(home_label) != 1:
    st.warning("Selecione a equipa da casa.")
    st.stop()
if len(away_label) != 1:
    st.warning("Selecione a equipa visitante.")
    st.stop()


home_label = home_label[0]
away_label = away_label[0]
h = team_map[home_label]
a = team_map[away_label]
home_team = h["team"]
away_team = a["team"]
home_liga = h["liga"]
away_liga = a["liga"]
s_home = h["stats"]
s_away = a["stats"]

if home_label == away_label:
    st.warning("Escolha duas equipes diferentes.")
    st.stop()


##### h2h #####

def get_h2h_results(home_team, away_team, home_liga, away_liga, df_current, is_new_league):
    """
    Retorna lista de resultados H2H nos últimos 12 meses.
    Cada item: (resultado, gols_home, gols_away)
    """
    h2h = []

    # --- 1. Procurar no DataFrame atual (2025) ---
    if not df_current.empty:
        # Detectar layout
        if 'HomeTeam' in df_current.columns:
            home_col, away_col = 'HomeTeam', 'AwayTeam'
            hg_col, ag_col = 'FTHG', 'FTAG'
            res_col = 'FTR'
        elif 'Home' in df_current.columns:
            home_col, away_col = 'Home', 'Away'
            hg_col, ag_col = 'HG', 'AG'
            res_col = 'Res'
        else:
            return h2h

        # Filtrar jogos entre as duas equipas
        mask1 = (df_current[home_col] == home_team) & (df_current[away_col] == away_team)
        mask2 = (df_current[home_col] == away_team) & (df_current[away_col] == home_team)
        df_h2h = df_current[mask1 | mask2].copy()

        for _, row in df_h2h.iterrows():
            if row[home_col] == home_team:
                g_home = row[hg_col]
                g_away = row[ag_col]
                res = row[res_col]
            else:
                g_home = row[ag_col]
                g_away = row[hg_col]
                # Inverter resultado
                if row[res_col] == 'H':
                    res = 'A'
                elif row[res_col] == 'A':
                    res = 'H'
                else:
                    res = 'D'
            h2h.append((res, g_home, g_away))

    # --- 2. Se for liga tradicional, procurar também em 2024/25 ---
    if not is_new_league and home_liga == away_liga:
        df_2425 = load_euro_2024_2025()
        if not df_2425.empty:
            # Mapear nome da liga para código (ex: "Inglaterra - Premier League" → "E0")
            code_to_league = {v["code"]: k for k, v in LEAGUE_CONFIG.items()}
            league_code = None
            for code, name in code_to_league.items():
                if name == home_liga:
                    league_code = code
                    break

            if league_code and 'Div' in df_2425.columns:
                df_league_2425 = df_2425[df_2425['Div'] == league_code].copy()
                if not df_league_2425.empty:
                    mask1 = (df_league_2425['HomeTeam'] == home_team) & (df_league_2425['AwayTeam'] == away_team)
                    mask2 = (df_league_2425['HomeTeam'] == away_team) & (df_league_2425['AwayTeam'] == home_team)
                    df_h2h_2425 = df_league_2425[mask1 | mask2]

                    for _, row in df_h2h_2425.iterrows():
                        if row['HomeTeam'] == home_team:
                            g_home = row['FTHG']
                            g_away = row['FTAG']
                            res = row['FTR']
                        else:
                            g_home = row['FTAG']
                            g_away = row['FTHG']
                            if row['FTR'] == 'H':
                                res = 'A'
                            elif row['FTR'] == 'A':
                                res = 'H'
                            else:
                                res = 'D'
                        h2h.append((res, g_home, g_away))

    # Manter apenas os últimos 5 confrontos (ordem cronológica inversa)
    return h2h[-5:]


# ================================================
# 🎛️ FATORES CONTEXTUAIS
# ================================================
st.divider()
st.subheader("Fatores Contextuais")
col_f1, col_f2 = st.columns(2)
with col_f1:
    aus_casa = st.selectbox(f"Ausências em {home_team}", ["Nenhuma", "1 ausência ofensiva", "2+ ausências ofensivas", "1 ausência defensiva", "2+ ausências defensivas"], key="aus_casa")
    desc_casa = st.number_input(f"Dias de desc ({home_team})", 0, 14, 5, step=1)
    exp_casa = st.number_input(f"Expulsões ({home_team})", 0, 5, 0, step=1)
with col_f2:
    aus_fora = st.selectbox(f"Ausências em {away_team}", ["Nenhuma", "1 ausência ofensiva", "2+ ausências ofensivas", "1 ausência defensiva", "2+ ausências defensivas"], key="aus_fora")
    desc_fora = st.number_input(f"Dias de desc ({away_team})", 0, 14, 5, step=1)
    exp_fora = st.number_input(f"Expulsões ({away_team})", 0, 5, 0, step=1)

st.divider()

# ================================================
# 🔢 CÁLCULO COM NOVA LÓGICA DE EMPATE
# ================================================
def poisson_prob(lam, k):
    if lam <= 0 or k < 0:
        return 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# Médias base
media_gm_casa = s_home["media_gm_casa"]
media_gs_casa = s_home["media_gs_casa"]
media_gm_fora = s_away["media_gm_fora"]
media_gs_fora = s_away["media_gs_fora"]

# Ajuste por ausências
if aus_casa == "1 ausência ofensiva":
    media_gm_casa *= 0.85
elif aus_casa == "2+ ausências ofensivas":
    media_gm_casa *= 0.75
elif aus_casa == "1 ausência defensiva":
    media_gs_casa *= 1.20
elif aus_casa == "2+ ausências defensivas":
    media_gs_casa *= 1.35

if aus_fora == "1 ausência ofensiva":
    media_gm_fora *= 0.85
elif aus_fora == "2+ ausências ofensivas":
    media_gm_fora *= 0.75
elif aus_fora == "1 ausência defensiva":
    media_gs_fora *= 1.20
elif aus_fora == "2+ ausências defensivas":
    media_gs_fora *= 1.35

# Calcular golos esperados
golos_casa = (media_gm_casa + media_gs_fora) / 2
golos_fora = (media_gm_fora + media_gs_casa) / 2
golos_casa = max(0.1, golos_casa)
golos_fora = max(0.1, golos_fora)

max_g = 5
p1_raw = p2_raw = 0.0
for i in range(max_g + 1):
    for j in range(max_g + 1):
        if i == j:
            continue
        prob = poisson_prob(golos_casa, i) * poisson_prob(golos_fora, j)
        if i > j:
            p1_raw += prob
        elif j > i:
            p2_raw += prob

# Normalizar p1 e p2
total_12 = p1_raw + p2_raw
if total_12 == 0:
    p1_norm = 0.5
    p2_norm = 0.5
else:
    p1_norm = p1_raw / total_12
    p2_norm = p2_raw / total_12

# Empate = min / max
min_p = min(p1_norm, p2_norm)
max_p = max(p1_norm, p2_norm)
px_ratio = min_p / max_p if max_p > 0 else 0.0

# Ajuste adicional por empates reais
frequencia_empate_casa = s_home['e_casa'] / max(s_home['jogos_casa'], 1)
frequencia_empate_fora = s_away['e_fora'] / max(s_away['jogos_fora'], 1)
media_empate = (frequencia_empate_casa + frequencia_empate_fora) / 2
if media_empate > 0.3:
    px_ratio = min(px_ratio * (1 + (media_empate - 0.3) * 2), 1.0)

# Normalizar
total_final = p1_norm + p2_norm + px_ratio
p1 = round(p1_norm / total_final * 100, 1)
p2 = round(p2_norm / total_final * 100, 1)
px = round(px_ratio / total_final * 100, 1)

# Garantir mínimo de 5%
p1 = max(p1, 5.0)
px = max(px, 5.0)
p2 = max(p2, 5.0)
soma = p1 + px + p2
p1 = round(p1 / soma * 100, 1)
px = round(px / soma * 100, 1)
p2 = round(p2 / soma * 100, 1)


# Escolha final
probs = {"1": p1, "X": px, "2": p2}
sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
(first_key, first_val), (second_key, second_val), (third_key, third_val) = sorted_items

if (first_val - second_val) < 25:
    order = {"1": 0, "X": 1, "2": 2}
    pick = "".join(sorted([first_key, second_key], key=lambda x: order[x]))
else:
    pick = first_key

# Resultado hipotético
if pick == "X":
    g = max(1, round((golos_casa + golos_fora) / 2))
    resultado_hip = f"{g} - {g}"
elif pick == "1":
    gc = max(2, round(golos_casa))
    gf = min(gc - 1, max(0, round(golos_fora)))
    resultado_hip = f"{gc} - {gf}"
elif pick == "2":
    gf = max(2, round(golos_fora))
    gc = min(gf - 1, max(0, round(golos_casa)))
    resultado_hip = f"{gc} - {gf}"
elif pick in ["1X", "X2"]:
    g = max(1, round((golos_casa + golos_fora) / 2))
    resultado_hip = f"{g} - {g}"
else:
    gc = max(1, round(golos_casa))
    gf = max(1, round(golos_fora))
    if gc == gf:
        gf += 1
    resultado_hip = f"{gc} - {gf}"
# ================================================
# 📊 ANÁLISE TÁTICA (PROFISSIONAL, DETALHADA E AUTOMATIZADA)
# ================================================



def plural(num, singular, plural_form):
    return f"{num} {singular}" if num == 1 else f"{num} {plural_form}"

def get_df(lg):
    for name, cfg in LEAGUE_CONFIG.items():
        if name == lg:
            df = load_league_data(cfg["code"], cfg["season"])
            return df
    return pd.DataFrame()

def calc_rank(df):
    if df.empty:
        return {}

    # Corrigir BOM
    if df.columns[0].startswith("ï»¿"):
        df.columns = df.columns.str.replace("ï»¿", "", regex=False)

    # Detectar layout
    if 'HomeTeam' in df.columns and 'FTHG' in df.columns and 'FTR' in df.columns:
        home_col, away_col = 'HomeTeam', 'AwayTeam'
        hg_col, ag_col = 'FTHG', 'FTAG'
        res_col = 'FTR'
        is_new_league = False
    elif 'Home' in df.columns and 'HG' in df.columns and 'Res' in df.columns:
        home_col, away_col = 'Home', 'Away'
        hg_col, ag_col = 'HG', 'AG'
        res_col = 'Res'
        is_new_league = True
    else:
        return {}

    # --- Filtrar por 2025 nas ligas novas ---
    if is_new_league and 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df[df['Date'].dt.year == 2025].copy()
        except Exception:
            pass  # fallback: usar todos os dados

    # Verificar colunas essenciais
    required = [home_col, away_col, hg_col, ag_col, res_col]
    if not all(col in df.columns for col in required):
        return {}

    df = df[required].dropna()

    # Dicionário de times
    teams = {}

    for _, row in df.iterrows():
        ht = row[home_col]
        at = row[away_col]
        hg = row[hg_col]
        ag = row[ag_col]
        res = row[res_col]

        # Inicializar times
        if ht not in teams:
            teams[ht] = {"p": 0, "gm": 0, "gs": 0}
        if at not in teams:
            teams[at] = {"p": 0, "gm": 0, "gs": 0}

        # Gols
        teams[ht]["gm"] += hg
        teams[ht]["gs"] += ag
        teams[at]["gm"] += ag
        teams[at]["gs"] += hg

        # Pontos
        if res == 'H':
            teams[ht]["p"] += 3
        elif res == 'A':
            teams[at]["p"] += 3
        elif res == 'D':
            teams[ht]["p"] += 1
            teams[at]["p"] += 1

    # Ordenar por pontos e saldo (gm - gs)
    ranking = sorted(
        teams.items(),
        key=lambda x: (x[1]["p"], x[1]["gm"] - x[1]["gs"]),
        reverse=True
    )

    # Retornar dicionário: time -> (posição, pontos)
    return {team: (i + 1, data["p"]) for i, (team, data) in enumerate(ranking)}


df_h = get_df(home_liga)
rank_h = calc_rank(df_h) if not df_h.empty else {}
total_h = len(rank_h) or 20

df_a = get_df(away_liga)
rank_a = calc_rank(df_a) if not df_a.empty else {}
total_a = len(rank_a) or 20

# Detectar se é liga nova (pela presença de colunas 'Home' em vez de 'HomeTeam')
is_new_league = ('Home' in df_h.columns) if not df_h.empty else ('Home' in df_a.columns)

# Obter confrontos diretos
h2h_results = get_h2h_results(
    home_team=home_team,
    away_team=away_team,
    home_liga=home_liga,
    away_liga=away_liga,
    df_current=df_h if home_liga == away_liga else pd.DataFrame(),
    is_new_league=is_new_league
)


# --- Ajuste com base em confrontos diretos (H2H) ---
bonus_home = 0.0
bonus_draw = 0.0
bonus_away = 0.0

for res, _, _ in h2h_results:
    if res == 'H':
        bonus_home += 0.05
    elif res == 'A':
        bonus_away += 0.05
    else:
        bonus_draw += 0.05

# Aplicar bônus e normalizar
p1_adj = p1 + bonus_home
px_adj = px + bonus_draw
p2_adj = p2 + bonus_away

# Evitar valores nulos
p1_adj = max(p1_adj, 0.01)
px_adj = max(px_adj, 0.01)
p2_adj = max(p2_adj, 0.01)

total = p1_adj + px_adj + p2_adj
p1 = p1_adj / total *100
px = px_adj / total *100
p2 = p2_adj / total *100

# Arredondar para exibição (2 casas decimais)
p1_d = round(p1, 2)
px_d = round(px, 2)
p2_d = round(p2, 2)

# Ajuste visual para somar 1.00
total_d = p1_d + px_d + p2_d
if abs(total_d - 1.0) >= 0.01:
    # Corrigir o maior
    if p1_d >= px_d and p1_d >= p2_d:
        p1_d = round(1.0 - px_d - p2_d, 2)
    elif px_d >= p2_d:
        px_d = round(1.0 - p1_d - p2_d, 2)
    else:
        p2_d = round(1.0 - p1_d - px_d, 2)


pos_casa = rank_h.get(home_team, (total_h, 0))[0]
pts_casa = rank_h.get(home_team, (0, 0))[1]
pos_fora = rank_a.get(away_team, (total_a, 0))[0]
pts_fora = rank_a.get(away_team, (0, 0))[1]
saldo_casa = s_home["gols_marcados"] - s_home["gols_sofridos"]
saldo_fora = s_away["gols_marcados"] - s_away["gols_sofridos"]

fatores = []
if aus_casa != "Nenhuma":
    fatores.append(f"- Ausências {aus_casa.lower()} em {home_team} comprometem o seu desempenho, afetando a dinâmica tática e a profundidade do plantel.")
if aus_fora != "Nenhuma":
    fatores.append(f"- Ausências {aus_fora.lower()} em {away_team} alteram o equilíbrio da equipa, especialmente em zonas-chave do campo.")
if exp_casa > 0:
    fatores.append(f"- {home_team}: {plural(exp_casa, 'expulsão', 'expulsões')} recente(s) — risco disciplinar que pode condicionar a estratégia e a rotação.")
if exp_fora > 0:
    fatores.append(f"- {away_team}: {plural(exp_fora, 'expulsão', 'expulsões')} recente(s) — potencial desequilíbrio na estrutura defensiva.")
if desc_casa < 3:
    fatores.append(f"- {home_team} com apenas {plural(desc_casa, 'dia', 'dias')} de descanso — possível fadiga física e mental.")
if desc_fora < 3:
    fatores.append(f"- {away_team} com apenas {plural(desc_fora, 'dia', 'dias')} de descanso — risco de desgaste acumulado.")

resumo_linhas = []
resumo_linhas.append("**Contexto competitivo:**")
resumo_linhas.append(f"- {home_team} ocupa a {pos_casa}.ª posição com {pts_casa} pontos.")
resumo_linhas.append(f"- {away_team} está em {pos_fora}.º lugar com {pts_fora} pontos.")

if pos_casa <= 5:
    resumo_linhas.append(f"- {home_team} encontra-se entre as formações de elite da competição, demonstrando consistência e eficácia.")
elif pos_casa >= total_h - 2:
    resumo_linhas.append(f"- {home_team} luta pela sobrevivência, com uma campanha que denota fragilidade e instabilidade.")

if pos_fora <= 5:
    resumo_linhas.append(f"- {away_team} figura entre os principais candidatos ao título, exibindo um desempenho sólido e coeso.")
elif pos_fora >= total_a - 2:
    resumo_linhas.append(f"- {away_team} enfrenta um cenário crítico, com risco real de rebaixamento e necessidade de recuperação imediata.")

resumo_linhas.append("")
resumo_linhas.append("**Desempenho no cenário do confronto (casa vs fora):**")

resumo_linhas.append(f"**{home_team} como anfitriã:**")
resumo_linhas.append(f"- Registou {plural(s_home['v_casa'], 'vitória', 'vitórias')}, {plural(s_home['e_casa'], 'empate', 'empates')} e {plural(s_home['d_casa'], 'derrota', 'derrotas')} em {s_home['jogos_casa']} jogos.")
resumo_linhas.append(f"- Média de {s_home['media_gm_casa']} golos marcados e {s_home['media_gs_casa']} sofridos por jogo em casa.")
if s_home['sem_sofrer_casa'] > 0:
    resumo_linhas.append(f"- {plural(s_home['sem_sofrer_casa'], 'jogo', 'jogos')} sem sofrer golos como anfitriã — evidência de solidez defensiva e forte ambiente no estádio.")
if s_home['sem_marcar_casa'] > 0:
    resumo_linhas.append(f"- Falhou em marcar em {plural(s_home['sem_marcar_casa'], 'jogo', 'jogos')} em casa — sinal de dificuldade ofensiva ou bloqueio tático.")

resumo_linhas.append(f"\n**{away_team} como visitante:**")
resumo_linhas.append(f"- Registou {plural(s_away['v_fora'], 'vitória', 'vitórias')}, {plural(s_away['e_fora'], 'empate', 'empates')} e {plural(s_away['d_fora'], 'derrota', 'derrotas')} em {s_away['jogos_fora']} jogos fora.")
resumo_linhas.append(f"- Média de {s_away['media_gm_fora']} golos marcados e {s_away['media_gs_fora']} sofridos por jogo fora.")
if s_away['sem_sofrer_fora'] > 0:
    resumo_linhas.append(f"- {plural(s_away['sem_sofrer_fora'], 'jogo', 'jogos')} sem sofrer golos como visitante — demonstração de organização tática e capacidade de contenção.")
if s_away['sem_marcar_fora'] > 0:
    resumo_linhas.append(f"- Não marcou em {plural(s_away['sem_marcar_fora'], 'jogo', 'jogos')} fora de casa — indicação de bloqueio ofensivo ou falta de eficácia em espaços reduzidos.")

resumo_linhas.append("")


# === DETECÇÃO AUTOMÁTICA DE CONFRONTOS COM TOP 5 ===
top5_casa = False
top5_fora = False
top5_casa_opponent = None
top5_fora_opponent = None
top5_casa_result = None
top5_fora_result = None

# Obter as 5 equipas no topo da classificação
if len(rank_h) >= 5:
    top5_teams = list(rank_h.keys())[:5]
    # Verificar se a equipa da casa jogou contra uma das 5 equipas no topo
    for _, r in df_h.iterrows():
        if 'HomeTeam' in r:
            ht = r['HomeTeam']
            at = r['AwayTeam']
        elif 'Home' in r:
            ht = r['Home']
            at = r['Away']
        else:
            continue

        if ht == home_team and at in top5_teams:
            if ('FTR' in r and r['FTR'] == 'H') or ('Res' in r and r['Res'] == 'H'):
                top5_casa = True
                top5_casa_opponent = at
                top5_casa_result = f"venceu por {r['FTHG'] if 'FTHG' in r else r['HG']:.0f}-{r['FTAG'] if 'FTAG' in r else r['AG']:.0f}"
                break
            elif ('FTR' in r and r['FTR'] == 'D') or ('Res' in r and r['Res'] == 'D'):
                top5_casa = True
                top5_casa_opponent = at
                top5_casa_result = f"empatou {r['FTHG'] if 'FTHG' in r else r['HG']:.0f}-{r['FTAG'] if 'FTAG' in r else r['AG']:.0f}"
                break
        elif at == home_team and ht in top5_teams:
            if ('FTR' in r and r['FTR'] == 'A') or ('Res' in r and r['Res'] == 'A'):
                top5_casa = True
                top5_casa_opponent = ht
                top5_casa_result = f"venceu por {r['FTAG'] if 'FTAG' in r else r['AG']:.0f}-{r['FTHG'] if 'FTHG' in r else r['HG']:.0f}"
                break
            elif ('FTR' in r and r['FTR'] == 'D') or ('Res' in r and r['Res'] == 'D'):
                top5_casa = True
                top5_casa_opponent = ht
                top5_casa_result = f"empatou {r['FTAG'] if 'FTAG' in r else r['AG']:.0f}-{r['FTHG'] if 'FTHG' in r else r['HG']:.0f}"
                break

if len(rank_a) >= 5:
    top5_teams = list(rank_a.keys())[:5]
    # Verificar se a equipa visitante jogou contra uma das 5 equipas no topo
    for _, r in df_a.iterrows():
        if 'HomeTeam' in r:
            ht = r['HomeTeam']
            at = r['AwayTeam']
        elif 'Home' in r:
            ht = r['Home']
            at = r['Away']
        else:
            continue

        if ht == away_team and at in top5_teams:
            if ('FTR' in r and r['FTR'] == 'H') or ('Res' in r and r['Res'] == 'H'):
                top5_fora = True
                top5_fora_opponent = at
                top5_fora_result = f"venceu por {r['FTHG'] if 'FTHG' in r else r['HG']:.0f}-{r['FTAG'] if 'FTAG' in r else r['AG']:.0f}"
                break
            elif ('FTR' in r and r['FTR'] == 'D') or ('Res' in r and r['Res'] == 'D'):
                top5_fora = True
                top5_fora_opponent = at
                top5_fora_result = f"empatou {r['FTHG'] if 'FTHG' in r else r['HG']:.0f}-{r['FTAG'] if 'FTAG' in r else r['AG']:.0f}"
                break
        elif at == away_team and ht in top5_teams:
            if ('FTR' in r and r['FTR'] == 'A') or ('Res' in r and r['Res'] == 'A'):
                top5_fora = True
                top5_fora_opponent = ht
                top5_fora_result = f"venceu por {r['FTAG'] if 'FTAG' in r else r['AG']:.0f}-{r['FTHG'] if 'FTHG' in r else r['HG']:.0f}"
                break
            elif ('FTR' in r and r['FTR'] == 'D') or ('Res' in r and r['Res'] == 'D'):
                top5_fora = True
                top5_fora_opponent = ht
                top5_fora_result = f"empatou {r['FTAG'] if 'FTAG' in r else r['AG']:.0f}-{r['FTHG'] if 'FTHG' in r else r['HG']:.0f}"
                break

if top5_casa:
    # Obter estatísticas da equipa do top 5
    stats_opponent = all_stats.get(top5_casa_opponent, {})
    if stats_opponent:
        media_gm_fora = stats_opponent.get("media_gm_fora", 0)
        media_gs_fora = stats_opponent.get("media_gs_fora", 0)
        sem_sofrer_fora = stats_opponent.get("sem_sofrer_fora", 0)
        sem_marcar_fora = stats_opponent.get("sem_marcar_fora", 0)

        # Criar descrição da equipa do top 5
        if media_gm_fora > 1.8:
            descricao_opponent = "uma equipa ofensiva e agressiva"
        elif media_gs_fora < 1.2:
            descricao_opponent = "uma equipa defensivamente sólida"
        elif sem_sofrer_fora > 3:
            descricao_opponent = "com uma defesa impenetrável fora de casa"
        elif sem_marcar_fora > 3:
            descricao_opponent = "que luta para marcar fora de casa"
        else:
            descricao_opponent = "uma equipa equilibrada"

        # Obter posição da equipa do top 5
        pos_opponent = rank_h.get(top5_casa_opponent, (len(rank_h), 0))[0]

        # Criar frase baseada na posição e desempenho
        if pos_opponent == 1:
            frase_opponent = f"contra {top5_casa_opponent}, a equipa líder da {home_liga} — num jogo intenso e revelador das suas capacidades."
        elif pos_opponent == 2:
            frase_opponent = f"contra {top5_casa_opponent}, a segunda classificada da {home_liga}— um resultado de grande impacto."
        elif pos_opponent <= 3:
            frase_opponent = f"contra {top5_casa_opponent}, o terceiro classificado da {home_liga}— um sinal de maturidade e qualidade."
        else:
            frase_opponent = f"contra {top5_casa_opponent}, uma das equipas de elite da {home_liga} — refltindo numa moral elevada e confiança reforçada."

        # Se a equipa do top 5 for forte fora de casa, destacar isso
        if media_gm_fora > 1.8 or media_gs_fora < 1.2 or sem_sofrer_fora > 3:
            frase_opponent = f"contra {top5_casa_opponent}, uma equipa forte fora de casa — um resultado que demonstra a força da {home_team} a jogar em casa."

        fatores.append(f"- {home_team} {top5_casa_result} {frase_opponent}")
    else:
        fatores.append(f"- {home_team} {top5_casa_result} contra {top5_casa_opponent}, uma das equipas mais fortes nesta edição da {home_liga} — sinal de robustez e dominância no próprio estádio.")

if top5_fora:
    # Obter estatísticas da equipa do top 5
    stats_opponent = all_stats.get(top5_fora_opponent, {})
    if stats_opponent:
        media_gm_casa = stats_opponent.get("media_gm_casa", 0)
        media_gs_casa = stats_opponent.get("media_gs_casa", 0)
        sem_sofrer_casa = stats_opponent.get("sem_sofrer_casa", 0)
        sem_marcar_casa = stats_opponent.get("sem_marcar_casa", 0)

        # Criar descrição da equipa do top 5
        if media_gm_casa > 1.8:
            descricao_opponent = "uma equipa ofensiva e agressiva em casa"
        elif media_gs_casa < 1.2:
            descricao_opponent = "uma equipa defensivamente sólida em casa"
        elif sem_sofrer_casa > 3:
            descricao_opponent = "com uma defesa impenetrável em casa"
        elif sem_marcar_casa > 3:
            descricao_opponent = "que luta para marcar em casa"
        else:
            descricao_opponent = "uma equipa equilibrada"

        # Obter posição da equipa do top 5
        pos_opponent = rank_a.get(top5_fora_opponent, (len(rank_a), 0))[0]

        # Criar frase baseada na posição e desempenho
        if pos_opponent == 1:
            frase_opponent = f"contra {top5_fora_opponent}, a atual líder da competição — um feito extraordinário na sua jornada na {away_liga}."
        elif pos_opponent == 2:
            frase_opponent = f"contra {top5_fora_opponent}, a segunda classificada da {away_liga} — um resultado de grande impacto."
        elif pos_opponent <= 3:
            frase_opponent = f"contra {top5_fora_opponent}, a terceira classificada da {away_liga} — um sinal de maturidade e qualidade."
        else:
            frase_opponent = f"contra {top5_fora_opponent}, uma das equipas mais fortes deste ano na {away_liga} — demonstração de capacidade para superar adversários de alto nível."

        # Se a equipa do top 5 for forte em casa, destacar isso
        if media_gm_casa > 1.8 or media_gs_casa < 1.2 or sem_sofrer_casa > 3:
            frase_opponent = f"contra {top5_fora_opponent}, umas das principais equipas da corrida ao título, revelando estar ao nível dos atuais líderes da {away_liga}."

        fatores.append(f"- {away_team} {top5_fora_result} {frase_opponent}")
    else:
        fatores.append(f"- {away_team} {top5_fora_result} contra {top5_fora_opponent}, um dos colossos da {away_liga}, atualmente, demonstrando de capacidade para superar adversários de alto nível.")
if fatores:
    resumo_linhas.append("**Fatores contextuais relevantes:**")
    resumo_linhas.extend(fatores)

# Exibir na análise
resumo_linhas.append("")
if h2h_results:
    h2h_desc = []
    for res, g_h, g_a in h2h_results:
        if res == 'H':
            desc = f"{home_team} {int(g_h)}-{int(g_a)} {away_team}"
        elif res == 'A':
            desc = f"{away_team} {int(g_a)}-{int(g_h)} {home_team}"
        else:
            desc = f"{home_team} {int(g_h)}-{int(g_a)} {away_team}"
        h2h_desc.append(desc)
    resumo_linhas.append("**Confrontos diretos recentes:**")
    for d in reversed(h2h_desc):  # mais recente primeiro
        resumo_linhas.append(f"- {d}")





resumo_linhas.append("\n**Interpretação tática:**")

# Frases baseadas em cenários
base_phrases = {
    "1": [
        f"Diante do registo caseiro de {home_team} e das dificuldades de {away_team} como visitante, a vitória da casa emerge como o desfecho mais lógico, especialmente considerando a sua superioridade estatística e a pressão do público.",
        f"Com {home_team} a demonstrar solidez em casa e {away_team} a lutar fora, tudo indica que os pontos ficarão em casa — um resultado que reflete a hierarquia atual das equipas e a sua adaptação ao cenário competitivo.",
        f"A combinação de um ataque produtivo em casa e uma defesa robusta posiciona {home_team} como favorita clara, enquanto {away_team} enfrenta um teste de caráter e consistência fora de casa."
    ],
    "2": [
        f"Apesar de jogar fora, {away_team} tem argumentos suficientes para levar a melhor sobre uma {home_team} inconsistente em casa, aproveitando a sua mobilidade e eficácia tática.",
        f"O equilíbrio defensivo de {away_team} fora de casa pode ser a chave para surpreender uma {home_team} que não convence em casa, especialmente se conseguir explorar espaços e transições rápidas.",
        f"Com {away_team} a mostrar maturidade e eficiência nos últimos jogos, a aposta em vitória do visitante é justificada — um desafio que exige foco e precisão, mas que está ao alcance da equipa visitante."
    ],
    "X": [
        f"Face à paridade entre as duas formações — ambas com tendência para o empate nos seus respetivos cenários — o resultado igualado é o mais coerente, reflectindo a simetria tática e a cautela estratégica.",
        f"Quando duas equipas demonstram tanta dificuldade em impor-se, o empate acaba por ser a conclusão mais natural — um desfecho que honra a competitividade e a prudência de ambas as formações.",
        f"Num confronto onde nenhuma equipa domina claramente, o empate representa o equilíbrio justo — um resultado que reconhece a qualidade defensiva e a contenção ofensiva de ambos os lados."
    ],
    "1X": [
        f"{home_team} pode não vencer, mas dificilmente perderá em casa, especialmente contra um {away_team} com pouca ambição fora — um cenário que favorece a manutenção de pontos no seu reduto.",
        f"Mesmo que não vença, {home_team} tem argumentos defensivos para garantir pelo menos um ponto em casa, numa partida que exigirá paciência e gestão de riscos.",
        f"Com {home_team} a não perder em casa há vários jogos e {away_team} a mostrar inconsistência fora, a aposta em 1X é estratégica — um resultado que minimiza riscos e maximiza segurança."
    ],
    "X2": [
        f"{away_team} demonstra suficiente solidez fora para evitar a derrota, mesmo diante de uma {home_team} com alguma qualidade caseira — um cenário que valoriza a adaptabilidade e a resiliência da equipa visitante.",
        f"Com {away_team} a não perder fora há vários jogos, e {home_team} a mostrar inconsistência em casa, a aposta em X2 é estratégica — um desfecho que reconhece a capacidade de resposta e a maturidade da equipa visitante.",
        f"Num confronto onde a equipa da casa não consegue impor-se e a visitante se mostra organizada, o empate ou vitória do visitante é o cenário mais plausível — um resultado que reflete a realidade tática e o desempenho recente."
    ]
}

# Escolher frase aleatória
base_phrase = random.choice(base_phrases.get(pick, [f"A análise aponta para {pick} como resultado mais provável."]))
resumo_linhas.append(base_phrase)

resumo = "\n".join(resumo_linhas)
# ================================================
# 📊 EXIBIÇÃO FINAL
# ================================================
st.subheader("Probabilidades e Escolha Final")
col_p1, col_px, col_p2 = st.columns(3)
with col_p1:
    st.markdown(f"""
    <div class="prob-box">
        <div class="prob-label"style="font-size: 1.4em; margin-top: -4px">{home_team}</div>
        <div class="prob-value"style="font-size: 1.4em; margin-top: -4px">1</div>
        <div class="prob-percent"style="font-size: 1em; margin-top: -4px">{p1:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with col_px:
    st.markdown(f"""
    <div class="prob-box">
        <div class="prob-label" style="font-size: 2em; margin-top: 4px; text-align: center">X</div>
        <div class="prob-value">&nbsp;</div>
        <div class="prob-percent"style="font-size: 1em; margin-top: -25px; text-align: center">{px:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with col_p2:
    st.markdown(f"""
    <div class="prob-box">
        <div class="prob-label" style="font-size: 1.4em; margin-top: -4px; text-align: right">{away_team}</div>
        <div class="prob-value"style="font-size: 1.4em; margin-top: -4px; text-align: right">2</div>
        <div class="prob-percent"style="font-size: 1em; margin-top: -4px; text-align: right">{p2:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<h4 style='text-align:center; color:green;'>ESCOLHA: <b>{pick}</b> &nbsp; <small>({resultado_hip})</small></h4>", unsafe_allow_html=True)

st.subheader("Análise Tática")
st.markdown(resumo)

st.caption("Dados: football-data.co.uk • Temporada 2025/26")