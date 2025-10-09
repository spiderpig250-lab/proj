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


def highlight(text):
    return f"<span style='font-weight:bold; background-color:#ffebee; padding:0.2px 1px; border-radius:1px; color:#c62828;'>{text}</span>"


# --- 38 LIGAS (22 originais + 16 novas) - ORDENADAS POR NOME DO PAÍS
LEAGUE_CONFIG = {

    "Bundesliga": {"code": "D1", "season": "2526"},
    "2. Bundesliga": {"code": "D2", "season": "2526"},
    "Torneo De La Liga Profesional ": {"code": "ARG", "season": "2025"},
    "Austrian Bundesliga": {"code": "AUT", "season": "2025"},
    "Pro League": {"code": "B1", "season": "2526"},
    "Série A Brasileirão": {"code": "BRA", "season": "2025"},
    "Chinese Super League": {"code": "CHN", "season": "2025"},
    "Superligaen": {"code": "DNK", "season": "2025"},
    "LaLiga" : {"code": "SP1", "season": "2526"},
    "LaLiga2" : {"code": "SP2", "season": "2526"},
    "Scothis Premiership": {"code": "SC0", "season": "2526"},
    "Scothis Championship": {"code": "SC1", "season": "2526"},
    "Scotish League One": {"code": "SC2", "season": "2526"},
    "Scothis League Two": {"code": "SC3", "season": "2526"},
    "Veikkausliiga": {"code": "FIN", "season": "2025"},
    "Ligue 1": {"code": "F1", "season": "2526"},
    "Ligue 2": {"code": "F2", "season": "2526"},
    "A1 Ethniki Katigoria": {"code": "G1", "season": "2526"},
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
    "SuperLiga ": {"code": "ROU", "season": "2025"},
    "Russian Premier League": {"code": "RUS", "season": "2025"},
    "Allsvenskan": {"code": "SWE", "season": "2025"},
    "Super League": {"code": "SWZ", "season": "2025"},
    "Süper Lig": {"code": "T1", "season": "2526"},
    "Ukrainian Premier League": {"code": "UKR", "season": "2526"},
    "MLS": {"code": "USA", "season": "2025"},
}


LEAGUE_GENDER = {
    "Bundesliga": True,
    "2. Bundesliga": True ,
    "Torneo De La Liga Profesional ": True ,
    "Austrian Bundesliga": True ,
    "Pro League": True ,
    "Série A - Brasileirão": False,
    "Chinese Super League": True ,
    "Superligaen": True,
    "LaLiga" :  True,
    "LaLiga2" :  True,
    "Scothis Premiership":  True,
    "Scothis Championship":  True,
    "Scotish League One":  True,
    "Scothis League Two":  True,
    "Veikkausliiga":  True,
    "Ligue 1":  True,
    "Ligue 2":  True,
    "A1 Ethniki Katigoria":  True,
    "Eredivisie":  True,
    "Premier League":  True,
    "Championship": True,
    "League One":  True,
    "League Two":  True,
    "League of Ireland Premier Division":  True,
    "Serie A":  True,
    "Serie B":  True,
    "J1 League":  True,
    "Liga MX":  True,
    "Eliteserien":  True,
    "Liga Portugal":  True,
    "Ekstraklasa":  True,
    "SuperLiga ":  True,
    "Russian Premier League":  True,
    "Allsvenskan":  True,
    "Super League":  True,
    "Süper Lig":  True,
    "Ukrainian Premier League":  True,
    "MLS":  True,
}

STADIUMS = {
    # 🇦🇹 Áustria
    "A. Klagenfurt": "Hypo-Arena",
    "A. Lustenau": "Reichshofstadion",
    "Admira": "BSFZ-Arena",
    "Altach": "Cashpoint Arena",
    "Austria Vienna": "Generali Arena",
    "Grazer AK": "Merkur Arena",
    "Hartberg": "Profertil Arena Hartberg",
    "LASK": "Linzer Stadion",
    "Ried": "Keine Sorgen Arena",
    "St. Polten": "NV Arena",
    "Tirol": "Tivoli Stadion Tirol",
    "Wacker Innsbruck": "Tivoli Stadion Tirol",
    "Wolfsberger AC": "Lavanttal-Arena",
    
    # 🇫🇮 Finlândia
    "AC Oulu": "Raatti Stadium",
    "HIFK": "Bolt Arena",
    "HJK": "Bolt Arena",
    "Ilves": "Tammela Stadium",
    "KPV Kokkola": "Kokkolan Keskuskenttä",
    "KTP": "Kotkan Urheilukeskus",
    "Lahti": "Lahden Stadion",
    "Mariehamn": "Wiklöf Holding Arena",
    "SJK": "OmaSP Stadion",
    "VPS": "Hietalahti Stadium",
    
    # 🇬🇷 Grécia
    "AEK": "OPAP Arena",
    "Aris": "Kleanthis Vikelidis Stadium",
    "Asteras Tripolis": "Theodoros Kolokotronis Stadium",
    "Atromitos": "Peristeri Stadium",
    "Fenerbahce": "Şükrü Saracoğlu Stadium",  # Nota: Fenerbahce é turco, mas aparece aqui
    "Kifisia": "Zirineio Stadium",
    "Levadeiakos": "Levadia Municipal Stadium",
    "Olympiakos": "Georgios Karaiskakis Stadium",
    "PAOK": "Toumba Stadium",
    "Panathinaikos": "Apostolos Nikolaidis Stadium",
    "Panetolikos": "Panetolikos Stadium",
    "Panserraikos": "Serres Municipal Stadium",
    "Volos NFC": "Volos Municipal Stadium",
    
    # 🇸🇪 Suécia
    "AIK": "Friends Arena",
    "Djurgarden": "Tele2 Arena",
    "Elfsborg": "Borås Arena",
    "Gefle": "Gävle Energi Arena",
    "Hacken": "Bravida Arena",
    "Hammarby": "Tele2 Arena",
    "Halmstad": "Örjans Vall",
    "Kalmar": "Guldfågeln Arena",
    "Malmo FF": "Eleda Stadion",
    "Norrkoping": "PlatinumCars Arena",
    "Sirius": "Studenternas IP",
    "Sundsvall": "NP3 Arena",
    "Vasteras SK": "Solid Park Arena",
    
    # 🇩🇰 Dinamarca
    "Aalborg": "Aalborg Portland Park",
    "Brondby": "Brøndby Stadium",
    "FC Copenhagen": "Parken Stadium",
    "Horsens": "CASA Arena Horsens",
    "Lyngby": "Lyngby Stadion",
    "Midtjylland": "MCH Arena",
    "Nordsjaelland": "Right to Dream Park",
    "Silkeborg": "JYSK Park",
    "Vejle": "Vejle Stadium",
    "Viborg": "Viborg Stadium",
    
    # 🇳🇴 Noruega
    "Aalesund": "Color Line Stadion",
    "Bodo/Glimt": "Aspmyra Stadion",
    "Brann": "Brann Stadion",
    "Fredrikstad": "Fredrikstad Stadion",
    "Ham-Kam": "Briskeby Stadion",
    "Haugesund": "Haugesund Stadion",
    "Kristiansund": "Kristiansund Stadion",
    "Lillestrom": "Åråsen Stadion",
    "Molde": "Aker Stadion",
    "Odd": "Skagerak Arena",
    "Rosenborg": "Lerkendal Stadion",
    "Sandefjord": "Komplett Arena",
    "Sarpsborg 08": "Sarpsborg Stadion",
    "Stabaek": "Nadderud Stadion",
    "Tromso": "Romssa Arena",
    "Valerenga": "Intility Arena",
    "Viking": "SR-Bank Arena",
    
    # 🇦🇷 Argentina
    "Aldosivi": "José María Minella",
    "All Boys": "Islas Malvinas",
    "Argentinos Jrs": "Diego Armando Maradona",
    "Arsenal Sarandi": "Julio Humberto Grondona",
    "Atl. Rafaela": "Nuevo Monumental",
    "Atl. Tucuman": "Monumental José Fierro",
    "Banfield": "Florencio Sola",
    "Barracas Central": "Claudio Chiqui Tapia",
    "Belgrano": "Julio César Villagra",
    "Boca Juniors": "La Bombonera",
    "Central Cordoba": "Alfredo Terrera",
    "Colon Santa FE": "Brigadier General Estanislao López",
    "Defensa y Justicia": "Norberto Tomaghello",
    "Dep. Riestra": "Guillermo Laza",
    "Estudiantes L.P.": "Jorge Luis Hirschi",
    "Gimnasia L.P.": "Juan Carmelo Zerillo",
    "Godoy Cruz": "Malvinas Argentinas",
    "Huracan": "Tomás Adolfo Ducó",
    "Independiente": "Libertadores de América",
    "Ind. Rivadavia": "Bautista Gargantini",
    "Instituto": "Mario Alberto Kempes",
    "Lanus": "Ciudad de Lanús",
    "Newells Old Boys": "Marcelo Bielsa",
    "Olimpo Bahia Blanca": "Roberto Natalio Carminatti",
    "Platense": "Ciudad de Vicente López",
    "Racing Club": "El Cilindro",
    "River Plate": "El Monumental",
    "Rosario Central": "Gigante de Arroyito",
    "San Lorenzo": "Pedro Bidegain",
    "Sarmiento Junin": "Eva Perón",
    "Talleres Cordoba": "Mario Alberto Kempes",
    "Tigre": "José Dellagiovanna",
    "Union de Santa Fe": "15 de Abril",
    "Velez Sarsfield": "José Amalfitani",
    
    # 🇧🇷 Brasil
    "America MG": "Independência",
    "Atletico GO": "Antônio Accioly",
    "Atletico-MG": "Arena MRV",
    "Avai": "Ressacada",
    "Bahia": "Arena Fonte Nova",
    "Botafogo RJ": "Nilton Santos",
    "Bragantino": "Nabi Abi Chedid",
    "Ceara": "Castelão",
    "Chapecoense-SC": "Arena Condá",
    "Corinthians": "Neo Química Arena",
    "Coritiba": "Couto Pereira",
    "Criciuma": "Heriberto Hülse",
    "Cruzeiro": "Mineirão",
    "Cuiaba": "Arena Pantanal",
    "Flamengo RJ": "Maracanã",
    "Fluminense": "Maracanã",
    "Fortaleza": "Castelão",
    "Goias": "Hailé Pinheiro",
    "Gremio": "Arena do Grêmio",
    "Internacional": "Beira-Rio",
    "Juventude": "Alfredo Jaconi",
    "Mirassol": "José Maria de Campos Maia",
    "Palmeiras": "Allianz Parque",
    "Sao Paulo": "Morumbi",
    "Santos": "Vila Belmiro",
    "Sport": "Ilha do Retiro",
    "Vasco": "São Januário",
    "Vitoria": "Barradão",
    
    # 🇪🇸 Espanha
    "Alaves": "Mendizorrotza",
    "Albacete": "Carlos Belmonte",
    "Almeria": "Power Horse Stadium",
    "Andorra": "Estadi Nacional",
    "Antequera": "El Maulí",  # Nota: não está na lista, mas para referência
    "Ath Bilbao": "San Mamés",
    "Ath Madrid": "Metropolitano",
    "Barcelona": "Montjuïc",
    "Betis": "Benito Villamarín",
    "Burgos": "El Plantío",
    "Cadiz": "Nuevo Mirandilla",
    "Celta": "Abanca-Balaídos",
    "Cordoba": "Nuevo Arcángel",
    "Eibar": "Ipurua",
    "Espanol": "RCDE Stadium",
    "Estoril": "António Coimbra da Mota",  # Nota: Estoril é português, mas aparece aqui
    "Getafe": "Coliseum Alfonso Pérez",
    "Girona": "Montilivi",
    "Granada": "Nuevo Los Cármenes",
    "Huesca": "El Alcoraz",
    "La Coruna": "Riazor",
    "Las Palmas": "Gran Canaria",
    "Leganes": "Butarque",
    "Levante": "Ciutat de València",
    "Mallorca": "Visit Mallorca Estadi",
    "Mirandes": "Anduva",
    "Osasuna": "El Sadar",
    "Oviedo": "Carlos Tartiere",
    "R. Volgograd": "Volgograd Arena",  # Nota: R. Volgograd é russo
    "Racing Santander": "El Sardinero",  # Nota: não está na lista, mas para referência
    "Real Madrid": "Santiago Bernabéu",
    "Sociedad": "Reale Arena",
    "Sp Gijon": "El Molinón",
    "Sp Lisbon": "José Alvalade",  # Nota: Sp Lisbon é português
    "Valencia": "Mestalla",
    "Valladolid": "José Zorrilla",
    "Vallecano": "Campo de Fútbol de Vallecas",
    "Villarreal": " de la Cerámica",
    "Zaragoza": "La Romareda",
    
    # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra
    "AFC Wimbledon": "Cherry Red Records Stadium",
    "Arsenal": "Emirates Stadium",
    "Aston Villa": "Villa Park",
    "Barnsley": "Oakwell",
    "Birmingham": "St Andrew's",
    "Blackburn": "Ewood Park",
    "Blackpool": "Bloomfield Road",
    "Bournemouth": "Vitality Stadium",
    "Brentford": "Gtech Community Stadium",
    "Bristol City": "Ashton Gate",
    "Bristol Rvs": "Memorial Stadium",
    "Burnley": "Turf Moor",
    "Cambridge": "Abbey Stadium",
    "Cardiff": "Cardiff City Stadium",
    "Charlton": "The Valley",
    "Chelsea": "Stamford Bridge",
    "Coventry": "Coventry Building Society Arena",
    "Crystal Palace": "Selhurst Park",
    "Derby": "Pride Park Stadium",
    "Everton": "Goodison Park",
    "Exeter": "St James Park",
    "Fleetwood Town": "Highbury Stadium",
    "Fulham": "Craven Cottage",
    "Gillingham": "Priestfield Stadium",
    "Grimsby": "Blundell Park",
    "Guiseley": "Nethermoor Park",  # Nota: não está na lista
    "Harrogate": "Wetherby Road",
    "Huddersfield": "John Smith's Stadium",
    "Hull": "MKM Stadium",
    "Ipswich": "Portman Road",
    "Leeds": "Elland Road",
    "Leicester": "King Power Stadium",
    "Leyton Orient": "Brisbane Road",
    "Lincoln": "LNER Stadium",
    "Liverpool": "Anfield",
    "Luton": "Kenilworth Road",
    "Man City": "Etihad Stadium",
    "Man United": "Old Trafford",
    "Middlesbrough": "Riverside Stadium",
    "Millwall": "The Den",
    "Milton Keynes Dons": "Stadium MK",
    "Newcastle": "St James' Park",
    "Nott'm Forest": "City Ground",
    "Oxford": "Kassam Stadium",
    "Peterboro": "London Road Stadium",
    "Plymouth": "Home Park",
    "Port Vale": "Vale Park",
    "Portsmouth": "Fratton Park",
    "Preston": "Deepdale",
    "QPR": "Loftus Road",
    "Reading": "Select Car Leasing Stadium",
    "Rotherham": "AESSEAL New York Stadium",
    "Sheffield United": "Bramall Lane",
    "Sheffield Weds": "Hillsborough",
    "Southampton": "St Mary's Stadium",
    "Stoke": "bet365 Stadium",
    "Sunderland": "Stadium of Light",
    "Swansea": "Swansea.com Stadium",
    "Swindon": "County Ground",
    "Tottenham": "Tottenham Hotspur Stadium",
    "Watford": "Vicarage Road",
    "West Brom": "The Hawthorns",
    "West Ham": "London Stadium",
    "Wigan": "DW Stadium",
    "Wolves": "Molineux Stadium",
    "Wrexham": "Racecourse Ground",
    "Wycombe": "Adams Park",
    
    # 🇵🇹 Portugal
    "Alverca": "Complexo Desportivo do Alverca",
    "Arouca": "Municipal de Arouca",
    "AVS": "Complexo Desportivo do Alverca",  # Nota: AVS joga em Alverca
    "Benfica": "da Luz",
    "Boavista": "Bessa Século XXI",  # Nota: não está na lista
    "Braga": "Municipal de Braga",
    "Casa Pia": "Pina Manique",
    "Estoril": "António Coimbra da Mota",
    "Estrela": "José Gomes",
    "Famalicao": "Municipal de Famalicão",
    "Gil Vicente": "Cidade de Barcelos",
    "Guimaraes": "D. Afonso Henriques",
    "Moreirense": "Comendador Joaquim de Almeida Freitas",
    "Nacional": "Madeira Football Association Stadium",
    "Porto": "do Dragão",
    "Rio Ave": "Municipal do Rio Ave",
    "Santa Clara": "Achada do Rio",
    "Sporting": "José Alvalade",
    "Tondela": "João Cardoso",
    
    # 🇮🇹 Itália
    "Atalanta": "Gewiss Stadium",
    "Bari": "San Nicola",
    "Bologna": "Renato Dall'Ara",
    "Cagliari": "Unipol Domus",
    "Cremonese": "Giovanni Zini",
    "Empoli": "Carlo Castellani",
    "Fiorentina": "Artemio Franchi",
    "Frosinone": "Benito Stirpe",
    "Genoa": "Luigi Ferraris",
    "Inter": "San Siro",
    "Juventus": "Allianz Stadium",
    "Lazio": "Olimpico",
    "Lecce": "Via del Mare",
    "Milan": "San Siro",
    "Monza": "U-Power Stadium",
    "Napoli": "Diego Armando Maradona",
    "Parma": "Ennio Tardini",
    "Roma": "Olimpico",
    "Salernitana": "Arechi",  # Nota: não está na lista
    "Sampdoria": "Luigi Ferraris",
    "Sassuolo": "MAPEI Stadium",
    "Spezia": "Alberto Picco",
    "Torino": "Olimpico Grande Torino",
    "Udinese": "Friuli",
    "Venezia": "Pier Luigi Penzo",
    "Verona": "Marcantonio Bentegodi",
    
    # 🇫🇷 França
    "Amiens": "Stade de la Licorne",
    "Angers": "Raymond Kopa Stadium",
    "Annecy": "Parc des Sports",
    "Auxerre": "Abbé-Deschamps",
    "Bastia": "Armand Cesari",
    "Brest": "Francis-Le Blé",
    "Clermont": "Gabriel Montpied",
    "Dunkerque": "Stade Marcel-Tribut",
    "Guingamp": "Roudourou",
    "Laval": "Francis-Le Blé",
    "Le Havre": "Océane Stadium",
    "Lille": "Pierre-Mauroy Stadium",
    "Lorient": "Moustoir",
    "Lyon": "Groupama Stadium",
    "Marseille": "Vélodrome",
    "Metz": "Saint-Symphorien",
    "Monaco": "Louis II Stadium",
    "Montpellier": "Mosson",
    "Nancy": "Marcel Picot",
    "Nantes": "La Beaujoire",
    "Nice": "Allianz Riviera",
    "Paris FC": "Stade Sébastien Charléty",
    "Paris SG": "Parc des Princes",
    "Pau FC": "Nouste Camp",
    "Reims": "Auguste-Delaune",
    "Rennes": "Roazhon Park",
    "Strasbourg": "Meinau",
    "Toulouse": "Stadium de Toulouse",
    
    # 🇩🇪 Alemanha
    "Augsburg": "WWK Arena",
    "Bayern Munich": "Allianz Arena",
    "Bielefeld": "SchücoArena",
    "Bochum": "Vonovia Ruhrstadion",
    "Braunschweig": "Eintracht-Stadion",
    "Bremen": "Weserstadion",
    "Darmstadt": "Merck-Stadion am Böllenfalltor",
    "Dresden": "DDV-Stadion",
    "Dortmund": "Signal Iduna Park",
    "Dresden": "DDV-Stadion",
    "Ein Frankfurt": "Deutsche Bank Park",
    "Freiburg": "Europa-Park Stadion",
    "Greuther Furth": "Sportpark Ronhof",
    "Hamburg": "Volksparkstadion",
    "Heidenheim": "Voith-Arena",
    "Hertha": "Olympiastadion Berlin",
    "Hoffenheim": "PreZero Arena",
    "Kaiserslautern": "Fritz-Walter-Stadion",
    "Karlsruhe": "Wildparkstadion",
    "Kiel": "Holstein-Stadion",
    "Köln": "RheinEnergieStadion",
    "Leipzig": "Red Bull Arena",
    "Leverkusen": "BayArena",
    "Magdeburg": "MDCC-Arena",
    "Mainz": "MEWA Arena",
    "M'gladbach": "Borussia-Park",
    "Nürnberg": "Max-Morlock-Stadion",
    "Paderborn": "Benteler-Arena",
    "Schalke 04": "Veltins-Arena",
    "St. Pauli": "Millerntor-Stadion",
    "Stuttgart": "Mercedes-Benz Arena",
    "Union Berlin": "Stadion An der Alten Försterei",
    "Wolfsburg": "Volkswagen Arena",
    
    # 🇺🇸 Estados Unidos
    "Atlanta Utd": "Mercedes-Benz Stadium",
    "Austin FC": "Q2 Stadium",
    "CF Montreal": "Stade Saputo",
    "Charlotte": "Bank of America Stadium",
    "Chicago Fire": "Soldier Field",
    "Colorado Rapids": "Dick's Sporting Goods Park",
    "Columbus Crew": "Lower.com Field",
    "DC United": "Audi Field",
    "FC Cincinnati": "TQL Stadium",
    "Houston Dynamo": "Shell Energy Stadium",
    "Inter Miami": "Chase Stadium",
    "LA Galaxy": "Dignity Health Sports Park",
    "Los Angeles FC": "BMO Stadium",
    "Minnesota United": "Allianz Field",
    "Nashville SC": "GEODIS Park",
    "New England Revolution": "Gillette Stadium",
    "New York City": "Yankee Stadium",
    "New York Red Bulls": "Red Bull Arena",
    "Orlando City": "Inter&Co Stadium",
    "Philadelphia Union": "Subaru Park",
    "Portland Timbers": "Providence Park",
    "Real Salt Lake": "America First Field",
    "San Diego FC": "Snapdragon Stadium",
    "San Jose Earthquakes": "PayPal Park",
    "Seattle Sounders": "Lumen Field",
    "Sporting Kansas City": "Children's Mercy Park",
    "St. Louis City": "Energizer Park",
    "Toronto FC": "BMO Field",
    "Vancouver Whitecaps": "BC Place",
    
    # 🇯🇵 Japão
    "Albirex Niigata": "Denka Big Swan Stadium",
    "Avispa Fukuoka": "Best Denki Stadium",
    "Cerezo Osaka": "Yanmar Stadium Nagai",
    "Consadole Sapporo": "Sapporo Dome",
    "Gamba Osaka": "Panasonic Stadium Suita",
    "Kashima Antlers": "Kashima Soccer Stadium",
    "Kashiwa Reysol": "Hitachi Kashiwa Soccer Stadium",
    "Kawasaki Frontale": "Todoroki Athletics Stadium",
    "Kyoto": "Sanga Stadium by Kyocera",
    "Nagoya Grampus": "Toyota Stadium",
    "Sagan Tosu": "Ekimae Real Estate Stadium",
    "Sanfrecce Hiroshima": "Edion Stadium Hiroshima",
    "Shimizu S-Pulse": "IAI Stadium Nihondaira",
    "Urawa Reds": "Saitama Stadium 2002",
    "Vissel Kobe": "Noevir Stadium Kobe",
    "Yokohama F. Marinos": "Nissan Stadium",
    "Yokohama FC": "NHK Spring Mitsuzawa Football Stadium",
    
    # 🇨🇳 China
    "Beijing Guoan": "Workers' Stadium",
    "Changchun Yatai": "Development Area Stadium",
    "Chengdu Rongcheng": "Chengdu Phoenix Mountain Football Stadium",
    "Dalian Pro": "Dalian Sports Centre Stadium",
    "Guangzhou FC": "Tianhe Stadium",
    "Henan Songshan Longmen": "Hanghai Stadium",
    "Meizhou Hakka": "Wuhua County Olympic Sports Centre",
    "Nantong Zhiyun": "Nantong Olympic Sports Centre",
    "Qingdao Hainiu": "Qingdao Tiantai Stadium",
    "Shandong Taishan": "Jinan Olympic Sports Center Stadium",
    "Shanghai Port": "Pudong Football Stadium",
    "Shanghai Shenhua": "Shanghai Stadium",
    "Shenzhen": "Shenzhen Universiade Sports Centre",
    "Tianjin Jinmen Tiger": "Tianjin Olympic Centre Stadium",
    "Wuhan Three Towns": "Wuhan Sports Center Stadium",
    "Zhejiang Professional": "Huzhou Olympic Sports Centre",
    
    # 🇷🇺 Rússia
    "Akhmat Grozny": "Akhmat-Arena",
    "CSKA Moscow": "VEB Arena",
    "Dynamo Moscow": "VTB Arena",
    "Krasnodar": "Krasnodar Stadium",
    "Lokomotiv Moscow": "RZD Arena",
    "Rostov": "Rostov Arena",
    "Rubin Kazan": "Ak Bars Arena",
    "Spartak Moscow": "Otkritie Arena",
    "Sochi": "Fisht Olympic Stadium",
    "Zenit": "Gazprom Arena",
    
    # 🇹🇷 Turquia
    "Alanyaspor": "Bahçeşehir Okulları Stadium",
    "Antalyaspor": "Antalya Stadium",
    "Besiktas": "Tüpraş Stadium",
    "Buyuksehyr": "Buca Arena",
    "Eyupspor": "Eyüp Stadium",
    "Fenerbahce": "Şükrü Saracoğlu Stadium",
    "Galatasaray": "Rams Park",
    "Genclerbirligi": "Eryaman Stadium",
    "Goztep": "Göztepe Gürsel Aksel Stadium",
    "Karagumruk": "Şükrü Saracoğlu Stadium",  # Nota: joga no estádio do Fenerbahce
    "Kasimpasa": "Recep Tayyip Erdoğan Stadium",
    "Kayserispor": "Kadir Has Stadium",
    "Kocaelispor": "İzmit Stadium",
    "Samsunspor": "Samsun 19 Mayıs Stadium",
    "Trabzonspor": "Papara Park",
    
    # 🇧🇪 Bélgica
    "Anderlecht": "Lotto Park",
    "Antwerp": "Bosuilstadion",
    "Charleroi": "Stade du Pays de Charleroi",
    "Club Brugge": "Jan Breydel Stadium",
    "Cercle Brugge": "Jan Breydel Stadium",
    "Eupen": "Kehrwegstadion",
    "Genk": "Cegeka Arena",
    "Gent": "Ghelamco Arena",
    "Mechelen": "AFAS-stadion Achter de Kazerne",
    "Standard": "Stade Maurice Dufrasne",
    "Westerlo": "Het Kuipje",
    
    # 🇳🇱 Holanda
    "Ajax": "Johan Cruyff Arena",
    "AZ Alkmaar": "AFAS Stadion",
    "Excelsior": "Van Donge & De Roo Stadion",
    "Feyenoord": "De Kuip",
    "Go Ahead Eagles": "De Adelaarshorst",
    "Groningen": "Euroborg",
    "Heerenveen": "Abe Lenstra Stadion",
    "Heracles": "Erve Asito",
    "Nijmegen": "Goffertstadion",
    "PSV Eindhoven": "Philips Stadion",
    "Sparta Rotterdam": "Het Kasteel",
    "Twente": "De Grolsch Veste",
    "Utrecht": "Stadion Galgenwaard",
    "Volendam": "Kras Stadion",
    "Zwolle": "MAC³PARK Stadion",
    
    # 🇨🇭 Suíça
    "Basel": "St. Jakob-Park",
    "Grasshoppers": "Letzigrund",
    "Lausanne": "Stade de la Tuilière",
    "Lugano": "Cornaredo Stadium",
    "Luzern": "Swissporarena",
    "Servette": "Stade de Genève",
    "Sion": "Stade Tourbillon",
    "St. Gallen": "Kybunpark",
    "Winterthur": "Stadion Schützenwiese",
    "Xamax": "Stade de la Maladière",
    "Young Boys": "Wankdorf Stadium",
    
    # 🇮🇪 Irlanda
    "Athlone": "Athlone Town Stadium",
    "Bohemians": "Dalymount Park",
    "Bray": "Carlisle Grounds",
    "Cork City": "Turners Cross",
    "Derry City": "Ryan McBride Brandywell Stadium",
    "Drogheda": "Weavers Park",
    "Dundalk": "Oriel Park",
    "Finn Harps": "Finn Park",
    "Galway": "Eamonn Deacy Park",
    "Shamrock Rovers": "Tallaght Stadium",
    "Shelbourne": "Tolka Park",
    "Sligo Rovers": "The Showgrounds",
    "St. Patricks": "Richmond Park",
    "Waterford": "RSC Arena",
    "Wexford": "Ferrycarrig Park",
    
    # 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia
    "Aberdeen": "Pittodrie Stadium",
    "Airdrie Utd": "Excelsior Stadium",
    "Arbroath": "Gayfield Park",
    "Celtic": "Celtic Park",
    "Dundee": "Dens Park",
    "Dundee United": "Tannadice Park",
    "Dunfermline": "East End Park",
    "Hamilton": "Fountain of Youth Stadium",
    "Hearts": "Tynecastle Park",
    "Hibernian": "Easter Road",
    "Inverness C": "Caledonian Stadium",
    "Kilmarnock": "Rugby Park",
    "Livingston": "Tony Macaroni Arena",
    "Motherwell": "Fir Park",
    "Partick": "Firhill Stadium",
    "Queen of Sth": "Palmerston Park",
    "Raith Rvs": "Stark's Park",
    "Rangers": "Ibrox Stadium",
    "Ross County": "Global Energy Stadium",
    "St Johnstone": "McDiarmid Park",
    "St Mirren": "SMiSA Stadium",
    
    # 🇵🇱 Polónia
    "Arka Gdynia": "Stadion Miejski w Gdyni",
    "Cracovia": "Stadion Cracovii",
    "Gornik Zabrze": "Arena Zabrze",
    "Jagiellonia": "Stadion Miejski w Białymstoku",
    "Korona Kielce": "Suzuki Arena",
    "Lech Poznan": "Stadion Miejski w Poznaniu",
    "Legia": "Polish Army Stadium",
    "Pogon Szczecin": "Stadion Miejski im. Floriana Krygiera",
    "Rakow": "Stadion Miejski w Częstochowie",
    "Slask Wroclaw": "Tarczyński Arena",
    "Widzew Lodz": "Stadion Miejski Widzewa",
    "Wisla": "Stadion Miejski w Krakowie",
    "Wisla Plock": "Stadion im. Kazimierza Górskiego",
    
    # 🇷🇴 Roménia
    "CFR Cluj": "Dr. Constantin Rădulescu Stadium",
    "FCSB": "Arena Națională",
    "Rapid Bucuresti": "Rapid-Giulești Stadium",
    "Universitatea Craiova": "Ion Oblemenco Stadium",
    "Voluntari": "Anghel Iordănescu Stadium",
    
    # 🇲🇽 México
    "Atlas": "Jalisco Stadium",
    "Club America": " Azteca",
    "Club Leon": "Nou Camp",
    "Club Tijuana": "Caliente Stadium",
    "Cruz Azul": "Azteca",
    "Guadalajara Chivas": "Estadio Akron",
    "Juarez": "Olímpico Benito Juárez",
    "Mazatlan FC": "de Mazatlán",
    "Monterrey": "BBVA",
    "Necaxa": "Victoria",
    "Pachuca": "Hidalgo",
    "Puebla": "Cuauhtémoc",
    "Queretaro": "Corregidora",
    "Santos Laguna": "Corona",
    "Tigres UANL": "Universitario",
    "Toluca": "Nemesio Díez",
    
    # 🇨🇴 Colômbia
    "Atletico Nacional": "Atanasio Girardot",  # Nota: não está na lista
    "Deportivo Cali": "Palogrande",  # Nota: não está na lista
    "Junior": "Metropolitano",  # Nota: não está na lista
    "Millonarios": "El Campín",  # Nota: não está na lista
    
    # 🇻🇪 Venezuela
    "Caracas FC": "Olímpico de la UCV",  # Nota: não está na lista
    "Deportivo Táchira": "Polideportivo de Pueblo Nuevo",  # Nota: não está na lista
    
    # Equipas sem estádio confirmado (mantém placeholder)
    "Academica Clinceni": "[ESTÁDIO]",
    "Admira": "BSFZ-Arena",  # Já preenchido
    "Astra": "[ESTÁDIO]",
    "Bistrita": "[ESTÁDIO]",
    "Calarasi": "[ESTÁDIO]",
    "Ceahlaul": "[ESTÁDIO]",
    "Chindia Targoviste": "[ESTÁDIO]",
    "Concordia": "[ESTÁDIO]",
    "Corona Brasov": "[ESTÁDIO]",
    "Csikszereda M. Ciuc": "[ESTÁDIO]",
    "Daco-Getica Bucuresti": "[ESTÁDIO]",
    "Din. Bucuresti": "[ESTÁDIO]",
    "FC Arges": "[ESTÁDIO]",
    "FC Botosani": "[ESTÁDIO]",
    "FC Brasov": "[ESTÁDIO]",
    "FC Hermannstadt": "[ESTÁDIO]",
    "FC Rapid Bucuresti": "Rapid-Giulești Stadium",
    "FC Voluntari": "Anghel Iordănescu Stadium",
    "FK Anzi Makhackala": "[ESTÁDIO]",
    "Gaz Metan Medias": "[ESTÁDIO]",
    "Gloria Buzau": "[ESTÁDIO]",
    "Metaloglobus Bucharest": "[ESTÁDIO]",
    "Mioveni": "[ESTÁDIO]",
    "Navodari": "[ESTÁDIO]",
    "Otelul": "[ESTÁDIO]",
    "Poli Iasi": "[ESTÁDIO]",
    "Poli Timisoara": "[ESTÁDIO]",
    "Polonia Warszawa": "[ESTÁDIO]",
    "Portuguesa": "[ESTÁDIO]",
    "PreuÃen MÃ¼nster": "Preußenstadion",
    "R. Volgograd": "Volgograd Arena",
    "RAAL La Louviere": "[ESTÁDIO]",
    "Radomiak Radom": "[ESTÁDIO]",
    "Ruch Chorzow": "[ESTÁDIO]",
    "Sandecja Nowy S.": "[ESTÁDIO]",
    "Sepsi Sf. Gheorghe": "[ESTÁDIO]",
    "Sligo Rovers": "The Showgrounds",
    "St. Gilloise": "Joseph Marien Stadium",
    "Stal Mielec": "[ESTÁDIO]",
    "Targu Mures": "[ESTÁDIO]",
    "Termalica B-B.": "[ESTÁDIO]",
    "Tigre": "José Dellagiovanna",
    "Tosno": "[ESTÁDIO]",
    "Tranmere": "Prenton Park",
    "Treaty United": "[ESTÁDIO]",
    "Unirea Slobozia": "[ESTÁDIO]",
    "UTA Arad": "[ESTÁDIO]",
    "Viitorul Constanta": "[ESTÁDIO]",
    "Zaglebie": "[ESTÁDIO]",
    "Zaglebie Sosnowiec": "[ESTÁDIO]",
    "Zawisza": "[ESTÁDIO]",
}


# --- LISTA LEVE DE TODAS AS EQUIPAS (SÓ NOMES E LIGA) ---
@st.cache_data(ttl=86400)  # atualiza uma vez por dia
def build_team_league_map():
    team_league_map = {}
    for league_name, cfg in LEAGUE_CONFIG.items():
        # Carregar apenas o CSV bruto (sem processar estatísticas)
        df = load_league_data(cfg["code"], cfg["season"])
        if df.empty:
            continue
        
        # Corrigir BOM
        if df.columns[0].startswith("ï»¿"):
            df.columns = df.columns.str.replace("ï»¿", "", regex=False)

        # Detectar colunas de equipas
        if 'HomeTeam' in df.columns:
            teams = set(df['HomeTeam'].dropna().unique()) | set(df['AwayTeam'].dropna().unique())
        elif 'Home' in df.columns:
            teams = set(df['Home'].dropna().unique()) | set(df['Away'].dropna().unique())
        else:
            continue

        for team in teams:
            # Garantir que não há duplicados com nomes iguais em ligas diferentes
            label = f"{team} ({league_name})"
            team_league_map[label] = {
                "team": team,
                "league": league_name
            }
    
    return team_league_map


@st.cache_data(ttl=7200, show_spinner=False)
def load_season_data(league_code, season_folder):
    """
    Carrega dados de uma temporada específica.
    season_folder: ex: '2425', '2324'
    """
    url = f"https://www.football-data.co.uk/mmz4281/{season_folder}/{league_code}.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
        df = pd.read_csv(StringIO(response.text))
        return df
    except Exception:
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


# ================================================
# FUNÇÕES DE CÁLCULO
# ================================================


def get_current_matchday(df, is_new_league=False):
    """
    Calcula a jornada atual.
    Para ligas novas, filtra por 2025 antes de contar.
    """
    if df.empty:
        return 1

    # --- Filtrar por 2025 nas ligas novas ---
    if is_new_league and 'Date' in df.columns:
        try:
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df[df['Date'].dt.year == 2025]
        except Exception:
            pass  # fallback: usar todos os dados

    # Detectar colunas
    if 'HomeTeam' in df.columns:
        home_col, away_col = 'HomeTeam', 'AwayTeam'
    elif 'Home' in df.columns:
        home_col, away_col = 'Home', 'Away'
    else:
        return 1

    from collections import defaultdict
    games_per_team = defaultdict(int)

    for _, row in df.iterrows():
        ht = row[home_col]
        at = row[away_col]
        if pd.notna(ht) and pd.notna(at):
            games_per_team[ht] += 1
            games_per_team[at] += 1

    if not games_per_team:
        return 1

    max_games = max(games_per_team.values())
    return max_games + 1


def plural(num, singular, plural_form):
    return f"{num} {singular}" if num == 1 else f"{num} {plural_form}"

def calculate_stats(df, league_name):
    if df.empty:
        return {}

    if df.columns[0].startswith("ï»¿"):
        df.columns = df.columns.str.replace("ï»¿", "", regex=False)

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

    if is_new_league and 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df[df['Date'].dt.year == 2025].copy()
        except Exception:
            pass

    required = [home_col, away_col, hg_col, ag_col, res_col]
    if not all(c in df.columns for c in required):
        return {}
    df = df[required].dropna()
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

        wins = len(home[home[res_col] == 'H']) + len(away[away[res_col] == 'A'])
        draws = len(home[home[res_col] == 'D']) + len(away[away[res_col] == 'D'])
        losses = len(home[home[res_col] == 'A']) + len(away[away[res_col] == 'H'])
        gf = home[hg_col].sum() + away[ag_col].sum()
        ga = home[ag_col].sum() + away[hg_col].sum()
        clean = len(home[home[ag_col] == 0]) + len(away[away[hg_col] == 0])
        fail = len(home[home[hg_col] == 0]) + len(away[away[ag_col] == 0])

        h_games = len(home)
        h_w = len(home[home[res_col] == 'H'])
        h_d = len(home[home[res_col] == 'D'])
        h_l = len(home[home[res_col] == 'A'])
        h_gf = home[hg_col].sum()
        h_ga = home[ag_col].sum()
        h_clean = len(home[home[ag_col] == 0])
        h_fail = len(home[home[hg_col] == 0])

        a_games = len(away)
        a_w = len(away[away[res_col] == 'A'])
        a_d = len(away[away[res_col] == 'D'])
        a_l = len(away[away[res_col] == 'H'])
        a_gf = away[ag_col].sum()
        a_ga = away[hg_col].sum()
        a_clean = len(away[away[hg_col] == 0])
        a_fail = len(away[away[ag_col] == 0])

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

def calc_rank(df):
    if df.empty:
        return {}

    if df.columns[0].startswith("ï»¿"):
        df.columns = df.columns.str.replace("ï»¿", "", regex=False)

    # Detectar layout e tipo de liga
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

    # --- FILTRAR POR 2025 NAS LIGAS NOVAS ---
    if is_new_league and 'Date' in df.columns:
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            df = df[df['Date'].dt.year == 2025].copy()
        except Exception:
            pass  # fallback: usar todos os dados

    required = [home_col, away_col, hg_col, ag_col, res_col]
    if not all(col in df.columns for col in required):
        return {}
    df = df[required].dropna()

    teams = {}
    for _, row in df.iterrows():
        ht = row[home_col]
        at = row[away_col]
        hg = row[hg_col]
        ag = row[ag_col]
        res = row[res_col]

        if ht not in teams:
            teams[ht] = {"p": 0, "gm": 0, "gs": 0}
        if at not in teams:
            teams[at] = {"p": 0, "gm": 0, "gs": 0}

        teams[ht]["gm"] += hg
        teams[ht]["gs"] += ag
        teams[at]["gm"] += ag
        teams[at]["gs"] += hg

        if res == 'H':
            teams[ht]["p"] += 3
        elif res == 'A':
            teams[at]["p"] += 3
        else:
            teams[ht]["p"] += 1
            teams[at]["p"] += 1

    ranking = sorted(teams.items(), key=lambda x: (x[1]["p"], x[1]["gm"] - x[1]["gs"]), reverse=True)
    return {team: (i + 1, data["p"]) for i, (team, data) in enumerate(ranking)}
# Mapeamento: país -> códigos de ligas
COUNTRY_LEAGUES = {
    "Espanha": ["SP1", "SP2"],
    "Inglaterra": ["E0", "E1", "E2", "E3"],
    "Itália": ["I1", "I2"],
    "Alemanha": ["D1", "D2"],
    "França": ["F1", "F2"],
    "Portugal": ["P1"],
    "Brasil": ["BRA"],
    "Argentina": ["ARG"],
    # Adicione mais conforme necessário
}

def get_country_from_league(league_name):
    """Extrai o país do nome da liga (ex: 'Espanha - LaLiga' -> 'Espanha')"""
    return league_name.split(" - ", 1)[0]

##### h2h #####

def get_h2h_results(home_team, away_team, home_liga, away_liga, df_current, is_new_league):
    """
    Retorna lista de resultados H2H das últimas 3 temporadas (2023/24, 2024/25, 2025).
    Cada item: (resultado, gols_home, gols_away)
    """
    h2h = []

    # --- 1. Temporada atual (2025) ---
    if not df_current.empty:
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
                if row[res_col] == 'H':
                    res = 'A'
                elif row[res_col] == 'A':
                    res = 'H'
                else:
                    res = 'D'
            h2h.append((res, g_home, g_away))

    # --- 2. Temporadas anteriores (2024/25 e 2023/24) ---
    if home_liga == away_liga:
        # Obter código da liga
        league_code = None
        for name, cfg in LEAGUE_CONFIG.items():
            if name == home_liga:
                league_code = cfg["code"]
                break

        if league_code:
            # Carregar 2024/25
            df_2425 = load_season_data(league_code, "2425")
            # Carregar 2023/24
            df_2324 = load_season_data(league_code, "2324")

            for df_prev in [df_2425, df_2324]:
                if df_prev.empty:
                    continue

                if 'HomeTeam' in df_prev.columns:
                    home_col, away_col = 'HomeTeam', 'AwayTeam'
                    hg_col, ag_col = 'FTHG', 'FTAG'
                    res_col = 'FTR'
                elif 'Home' in df_prev.columns:
                    home_col, away_col = 'Home', 'Away'
                    hg_col, ag_col = 'HG', 'AG'
                    res_col = 'Res'
                else:
                    continue

                mask1 = (df_prev[home_col] == home_team) & (df_prev[away_col] == away_team)
                mask2 = (df_prev[home_col] == away_team) & (df_prev[away_col] == home_team)
                df_h2h_prev = df_prev[mask1 | mask2]

                for _, row in df_h2h_prev.iterrows():
                    if row[home_col] == home_team:
                        g_home = row[hg_col]
                        g_away = row[ag_col]
                        res = row[res_col]
                    else:
                        g_home = row[ag_col]
                        g_away = row[hg_col]
                        if row[res_col] == 'H':
                            res = 'A'
                        elif row[res_col] == 'A':
                            res = 'H'
                        else:
                            res = 'D'
                    h2h.append((res, g_home, g_away))

    # Manter apenas os últimos 5 confrontos (mais recentes no final)
    return h2h[-5:]
# ================================================
# MAPA LEVE DE EQUIPAS
# ================================================

@st.cache_data(ttl=86400)
def build_team_league_map():
    team_league_map = {}
    for league_name, cfg in LEAGUE_CONFIG.items():
        df = load_league_data(cfg["code"], cfg["season"])
        if df.empty:
            continue
        if df.columns[0].startswith("ï»¿"):
            df.columns = df.columns.str.replace("ï»¿", "", regex=False)
        if 'HomeTeam' in df.columns:
            teams = set(df['HomeTeam'].dropna().unique()) | set(df['AwayTeam'].dropna().unique())
        elif 'Home' in df.columns:
            teams = set(df['Home'].dropna().unique()) | set(df['Away'].dropna().unique())
        else:
            continue
        for team in teams:
            label = f"{team} ({league_name})"
            team_league_map[label] = {"team": team, "league": league_name}
    return team_league_map

# ================================================
# INTERFACE E SELEÇÃO
# ================================================

team_league_map = build_team_league_map()
team_labels = sorted(team_league_map.keys(), key=lambda x: x.lower())

home_label = st.sidebar.selectbox("Equipa da CASA", team_labels, key="home_team")
away_label = st.sidebar.selectbox("Equipa VISITANTE", team_labels, key="away_team")

if home_label == away_label:
    st.warning("Escolha duas equipas diferentes.")
    st.stop()

h_info = team_league_map[home_label]
a_info = team_league_map[away_label]
home_team = h_info["team"]
home_liga = h_info["league"]
away_team = a_info["team"]
away_liga = a_info["league"]

@st.cache_data(ttl=3600, show_spinner=False)
def get_stats_and_df(league_name):
    cfg = LEAGUE_CONFIG[league_name]
    df = load_league_data(cfg["code"], cfg["season"])
    stats = calculate_stats(df, league_name) if not df.empty else {}
    return stats, df

stats_home, df_h = get_stats_and_df(home_liga)
stats_away, df_a = get_stats_and_df(away_liga)

s_home = stats_home.get(home_team, {})
s_away = stats_away.get(away_team, {})

if not s_home or not s_away:
    st.error("Erro ao carregar dados da equipa.")
    st.stop()


# ================================================
# ULTIMOS RESULTADOS
# ================================================

def get_last_5_results(df, team_name, is_home_team=True):
    """
    Retorna os últimos 5 resultados da equipa (V, E, D).
    """
    if df.empty:
        return []

    # Detectar layout
    if 'HomeTeam' in df.columns:
        home_col, away_col = 'HomeTeam', 'AwayTeam'
        res_col = 'FTR'
    elif 'Home' in df.columns:
        home_col, away_col = 'Home', 'Away'
        res_col = 'Res'
    else:
        return []

    results = []
    for _, row in df.iterrows():
        if row[home_col] == team_name:
            # É jogo em casa
            if row[res_col] == 'H':
                results.append('V')
            elif row[res_col] == 'A':
                results.append('D')
            else:
                results.append('E')
        elif row[away_col] == team_name:
            # É jogo fora
            if row[res_col] == 'A':
                results.append('V')
            elif row[res_col] == 'H':
                results.append('D')
            else:
                results.append('E')

    # Retornar os últimos 5 (mais recentes no final)
    return results[-5:][::-1]

# === ÚLTIMOS 5 RESULTADOS COM CORES ===
def get_last_5_results_colored(df, team_name):
    if df.empty:
        return []
    if 'HomeTeam' in df.columns:
        home_col, away_col, res_col = 'HomeTeam', 'AwayTeam', 'FTR'
    elif 'Home' in df.columns:
        home_col, away_col, res_col = 'Home', 'Away', 'Res'
    else:
        return []
    
    results = []
    for _, row in df.iterrows():
        if row[home_col] == team_name:
            # Jogo em casa
            if row[res_col] == 'H':
                results.append('<span style="color:#64D14B; font-weight:bold;">V</span>')  # Verde
            elif row[res_col] == 'A':
                results.append('<span style="color:#C92C2C; font-weight:bold;">D</span>')  # Vermelho
            else:
                results.append('<span style="color:#FFC700; font-weight:bold;">E</span>')  # Amarelo
        elif row[away_col] == team_name:
            # Jogo fora
            if row[res_col] == 'A':
                results.append('<span style="color:#64D14B; font-weight:bold;">V</span>')  # Verde
            elif row[res_col] == 'H':
                results.append('<span style="color:#C92C2C; font-weight:bold;">D</span>')  # Vermelho
            else:
                results.append('<span style="color:#FFC700; font-weight:bold;">E</span>')  # Amarelo
    return results[-5:][::-1]

# Obter resultados coloridos
last5_home_html = get_last_5_results_colored(df_h, home_team)
last5_away_html = get_last_5_results_colored(df_a, away_team)

# Formatar como string
form_home = " ".join(last5_home_html) if last5_home_html else '<span style="color:#999;">– – – – –</span>'
form_away = " ".join(last5_away_html) if last5_away_html else '<span style="color:#999;">– – – – –</span>'
# ================================================
# PARÂMETROS CONTEXTUAIS (AUSENCIAS, EXPULSÕES, DESCANSO)
# ================================================

aus_casa = st.sidebar.selectbox(f"Ausências em {home_team}", ["Nenhuma", "Ausência ofensiva", "2+ Ausências ofensivas", "Ausência defensiva", "2+ Ausências defensivas"], key="aus_casa")
aus_fora = st.sidebar.selectbox(f"Ausências em {away_team}", ["Nenhuma", "Ausência ofensiva", "2+ Ausências ofensivas", "Ausência defensiva", "2+ Ausências defensivas"], key="aus_fora")
exp_casa = st.sidebar.number_input("Expulsões recentes CASA", min_value=0, max_value=5, value=0)
exp_fora = st.sidebar.number_input("Expulsões recentes FORA", min_value=0, max_value=5, value=0)
desc_casa = st.sidebar.number_input("Dias de descanso CASA", min_value=1, max_value=10, value=3)
desc_fora = st.sidebar.number_input("Dias de descanso FORA", min_value=1, max_value=10, value=3)

# ================================================
# CÁLCULO DE CLASSIFICAÇÃO
# ================================================

rank_h = calc_rank(df_h) if not df_h.empty else {}
rank_a = calc_rank(df_a) if not df_a.empty else {}

total_h = len(rank_h) or 20
total_a = len(rank_a) or 20

pos_casa = rank_h.get(home_team, (total_h, 0))[0]
pts_casa = rank_h.get(home_team, (0, 0))[1]
pos_fora = rank_a.get(away_team, (total_a, 0))[0]
pts_fora = rank_a.get(away_team, (0, 0))[1]

# ================================================
# H2H
# ================================================

is_new_league = ('Home' in df_h.columns) if not df_h.empty else ('Home' in df_a.columns)
h2h_results = get_h2h_results(
    home_team=home_team,
    away_team=away_team,
    home_liga=home_liga,
    away_liga=away_liga,
    df_current=df_h if home_liga == away_liga else pd.DataFrame(),
    is_new_league=is_new_league
)

# ================================================
# DETECÇÃO DE TOP 5
# ================================================

top5_casa = False
top5_fora = False
top5_casa_opponent = None
top5_fora_opponent = None
top5_casa_result = None
top5_fora_result = None

if len(rank_h) >= 5:
    top5_teams = list(rank_h.keys())[:5]
    for _, r in df_h.iterrows():
        if 'HomeTeam' in r:
            ht, at = r['HomeTeam'], r['AwayTeam']
        elif 'Home' in r:
            ht, at = r['Home'], r['Away']
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
    for _, r in df_a.iterrows():
        if 'HomeTeam' in r:
            ht, at = r['HomeTeam'], r['AwayTeam']
        elif 'Home' in r:
            ht, at = r['Home'], r['Away']
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



# ================================================
# PROBABILIDADES (EXEMPLO SIMPLES - AJUSTE CONFORME SUA LÓGICA)
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
if aus_casa == "Ausência ofensiva":
    media_gm_casa *= 0.5
elif aus_casa == "2+ Ausências ofensivas":
    media_gm_casa *= 0.25
elif aus_casa == "Ausência defensiva":
    media_gs_casa *= 1.5
elif aus_casa == "2+ Ausências defensivas":
    media_gs_casa *= 1.75

if aus_fora == "Ausência ofensiva":
    media_gm_fora *= 0.5
elif aus_fora == "2+ Ausências ofensivas":
    media_gm_fora *= 0.25
elif aus_fora == "Ausência defensiva":
    media_gs_fora *= 1.5
elif aus_fora == "2+ Ausências defensivas":
    media_gs_fora *= 1.75

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


# Determinar pick para frase
if p1 > 0.5:
    pick = "1"
elif p2 > 0.5:
    pick = "2"
elif px > 0.4:
    pick = "X"
elif p1 + px > 0.75:
    pick = "1X"
elif px + p2 > 0.75:
    pick = "X2"
else:
    pick = "X"


# Escolha final
probs = {"1": p1, "X": px, "2": p2}
sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
(first_key, first_val), (second_key, second_val), (third_key, third_val) = sorted_items

if (first_val - second_val) < 25:
    order = {"1": 0, "X": 1, "2": 2}
    pick = "".join(sorted([first_key, second_key], key=lambda x: order[x]))
else:
    pick = first_key


       
resultado_hip = f"{(media_gm_casa+media_gs_fora)/2:.0f} - {(media_gm_fora+media_gs_casa)/2:.0f}"
# === RESUMO NARRATIVO ESTILO FLASHSCORE ===
linhas = []

# --- INTRODUÇÃO GERAL ---
# Calcular jornada (usar a liga da casa se forem iguais, senão usar a da casa)
# Detectar se é liga nova
is_new_league = ('Home' in df_h.columns) if not df_h.empty else ('Home' in df_a.columns)

df_jornada = df_h if home_liga == away_liga else df_h
matchday = get_current_matchday(df_jornada, is_new_league=is_new_league)

stadium = STADIUMS.get(home_team, "Estádio [não disponível]")
linhas.append('<br style="margin-bottom: 20px;">')
linhas.append("")
linhas.append(f"**{home_team}** e **{away_team}** defrontam-se na **{matchday}ª jornada** da {home_liga if home_liga == away_liga else 'competição'}, no Estádio **{stadium}**, em {home_team}.")

linhas.append("")
# --- ANÁLISE DA EQUIPA DA CASA ---

linhas.append(f"**{home_team}** ocupa atualmente a **{pos_casa}ª posição** na tabela após {s_home['jogos']} jogos, com **{s_home['vitorias']} vitórias**, {s_home['empates']} empates e **{s_home['derrotas']} derrotas**.")
linhas.append("<br>")
linhas.append(f"O registo de golos nesta temporada é de **{s_home['gols_marcados']:.0f}/{s_home['gols_sofridos']:.0f}**, resultando numa diferença de **{s_home['gols_marcados'] - s_home['gols_sofridos']:.0f} golos** e um total de **{pts_casa} pontos** somados.")
linhas.append("<br>")
linhas.append(f"Em casa, {home_team} disputou {s_home['jogos_casa']} jogos, registando **{s_home['v_casa']} vitórias**, **{s_home['e_casa']} empates** e **{s_home['d_casa']} derrotas**, com média de **{s_home['media_gm_casa']} golos marcados** e **{s_home['media_gs_casa']} sofridos** por jogo.")
linhas.append("<br>")
if s_home['sem_sofrer_casa'] > 0:
    linhas.append("<br>"f"{highlight(f"DESTAQUE:")}  **{s_home['sem_sofrer_casa']} jogos sem sofrer golos** em casa — evidência de solidez defensiva e forte ambiente no estádio.")
if s_home['sem_marcar_casa'] > 0:
    linhas.append("<br>"f"{highlight(f"DESTAQUE:")}  Falhou em marcar em **{s_home['sem_marcar_casa']} jogos** em casa — sinal de dificuldade ofensiva ou bloqueio tático.")

# --- FATORES ADICIONAIS PARA A CASA ---
fatores_casa = []
if aus_casa == "Ausência ofensiva":
    fatores_casa.append(f"{highlight(f"DESTAQUE:")}  **{aus_casa} em {home_team}** compromete o seu desempenho criativo e explorador, afetando a profundidade do plantel e podendo também resultar num jogo com menos golos marcados.")
if aus_casa == "2+ Ausências ofensivas":
    fatores_casa.append(f"{highlight(f"DESTAQUE:")}  **{aus_casa} em {home_team}** condicionam de forma substancial o eixo ofensivo, restringindo a profundidade e a versatilidade do plantel, o que conduz a uma quebra na dinâmica ofensiva e a um modelo de jogo menos projetado em ações de ataque.")
if aus_casa == "Ausência defensiva":
    fatores_casa.append(f"{highlight(f"DESTAQUE:")}  **{aus_casa} em {home_team}** compromete o seu desempenho organizativo e de contenção, afetando a consistência do setor recuado e podendo também resultar num jogo com maior exposição defensiva e mais golos sofridos.")
if aus_casa == "2+ Ausências defensivas":
    fatores_casa.append(f"{highlight(f"DESTAQUE:")}  **{aus_casa} em {home_team}** condicionam de forma substancial o eixo defensivo, restringindo a coesão e a capacidade de reação do setor, o que conduz a uma quebra na consistência coletiva e a um modelo de jogo menos equilibrado e mais vulnerável em ações de contenção.")

if exp_casa > 0:
    fatores_casa.append("<br>"f"{highlight(f"DESTAQUE:")}  **{home_team}: {plural(exp_casa, 'expulsão', 'expulsões')} recente(s)** — risco disciplinar que pode condicionar a estratégia e a rotação.")

if desc_casa < 3:
    fatores_casa.append(f"{highlight(f"DESTAQUE:")}  **{home_team} com apenas {plural(desc_casa, 'dia', 'dias')} de descanso** — possível fadiga física e mental.")

if fatores_casa:
    linhas.append("<br>")
    for f in fatores_casa:
        linhas.append(f"{f}")
# --- ANÁLISE DA EQUIPA VISITANTE ---
linhas.append("")
linhas.append(f"**{away_team}** está atualmente em **{pos_fora}º lugar** na tabela após {s_away['jogos']} jogos, com **{s_away['vitorias']} vitórias**, {s_away['empates']} empates e **{s_away['derrotas']} derrotas**.")
linhas.append("<br>")
linhas.append(f"O registo de golos nesta temporada é de **{s_away['gols_marcados']:.0f}/{s_away['gols_sofridos']:.0f}**, resultando numa diferença de **{s_away['gols_marcados'] - s_away['gols_sofridos']:.0f} golos** e contam com **{pts_fora} pontos** conquistados.")
linhas.append("<br>")
linhas.append(f"Fora de casa, {away_team} realizou {s_away['jogos_fora']} jogos, registando **{s_away['v_fora']} vitórias**, **{s_away['e_fora']} empates** e **{s_away['d_fora']} derrotas**, com média de **{s_away['media_gm_fora']} golos marcados** e **{s_away['media_gs_fora']} sofridos** por jogo.")
linhas.append("<br>")
if s_away['sem_sofrer_fora'] > 0:
    linhas.append("<br>"f"{highlight(f"DESTAQUE:")}  **{s_away['sem_sofrer_fora']} jogos sem sofrer golos** fora de casa — demonstração de organização tática e capacidade de contenção.")
if s_away['sem_marcar_fora'] > 0:
    linhas.append("<br>"f"{highlight(f"DESTAQUE:")}  Não marcou em **{s_away['sem_marcar_fora']} jogos** fora de casa — indicação de bloqueio ofensivo ou falta de eficácia em espaços reduzidos.")

# --- FATORES ADICIONAIS PARA A FORA ---
fatores_fora = []
if aus_fora == "Ausência ofensiva":
    fatores_fora.append(f"{highlight(f"DESTAQUE:")}  **{aus_fora} em {away_team}** alteram o equilíbrio da equipa, especialmente em zonas-chave do campo.")
if aus_fora == "2+ Ausências ofensivas":
    fatores_fora.append(f"{highlight(f"DESTAQUE:")}  **{aus_fora} em {away_team}** resultam numa limitação do eixo atacante, o que leva a equipa a perder profundidade e a ver diminuída a sua habitual dinâmica ofensiva, o que se traduz num jogo com menos situações de ataque.")
if aus_fora == "Ausência defensiva":
    fatores_fora.append(f"{highlight(f"DESTAQUE:")}  **{aus_fora} em {away_team}** altera o equilíbrio da equipa, especialmente em zonas mais defensivas e baixas do campo.")
if aus_fora == "2+ Ausências defensivas":
    fatores_fora.append(f"{highlight(f"DESTAQUE:")}  **{aus_fora} em {away_team}** resultam numa limitação do eixo defensivo, o que leva a equipa a perder solidez e a ver diminuída a sua habitual organização sem bola, o que se traduz num jogo com maior vulnerabilidade e mais situações de perigo consentidas.")
if exp_fora > 0:
    fatores_fora.append("<br>"f"{highlight(f"DESTAQUE:")}  **{away_team}: {plural(exp_fora, 'expulsão', 'expulsões')} recente(s)** — potencial desequilíbrio na estrutura defensiva.")
if desc_fora < 3:
    fatores_fora.append("<br>"f"{highlight(f"DESTAQUE:")}  **{away_team} com apenas {plural(desc_fora, 'dia', 'dias')} de descanso** — risco de desgaste acumulado.")

if fatores_fora:
    linhas.append("<br>")
    for f in fatores_fora:
        linhas.append(f"{f}")
# --- CONFRONTOS DIRETOS ---
if h2h_results:
    linhas.append("")
    linhas.append("**Confrontos diretos recentes:**")
    linhas.append("<br>")
    for res, g_h, g_a in h2h_results:  # mais recente primeiro
        if res == 'H':
            linhas.append("<br>"f"**{home_team} {int(g_h)}-{int(g_a)} {away_team}**")
        elif res == 'A':
            linhas.append("<br>"f"**{away_team} {int(g_a)}-{int(g_h)} {home_team}**")
        else:
            linhas.append("<br>"f"**{home_team} {int(g_h)}-{int(g_a)} {away_team}**")

# --- TOP 5 / CONTEXTUALIZAÇÃO ---
top5_fatores = []
if top5_casa:
    stats_opponent = stats_home.get(top5_casa_opponent, {})
    if stats_opponent:
        media_gm_fora = stats_opponent.get("media_gm_fora", 0)
        media_gs_fora = stats_opponent.get("media_gs_fora", 0)
        sem_sofrer_fora = stats_opponent.get("sem_sofrer_fora", 0)
        sem_marcar_fora = stats_opponent.get("sem_marcar_fora", 0)

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

        pos_opponent = rank_h.get(top5_casa_opponent, (len(rank_h), 0))[0]

        if pos_opponent == 1:
            frase_opponent = f"contra **{top5_casa_opponent}**, a equipa líder da {home_liga} — num jogo intenso e revelador das suas capacidades."
        elif pos_opponent == 2:
            frase_opponent = f"contra **{top5_casa_opponent}**, a segunda classificada da {home_liga}— um resultado de grande impacto."
        elif pos_opponent <= 3:
            frase_opponent = f"contra **{top5_casa_opponent}**, o terceiro classificado da {home_liga}— um sinal de maturidade e qualidade."
        else:
            frase_opponent = f"contra **{top5_casa_opponent}**, uma das equipas de elite da {home_liga} — refltindo numa moral elevada e confiança reforçada."

        if media_gm_fora > 1.8 or media_gs_fora < 1.2 or sem_sofrer_fora > 3:
            frase_opponent = f"contra **{top5_casa_opponent}**, uma equipa forte fora de casa — um resultado que demonstra a força da **{home_team}** em sair derrotada no seu canteiro, Estádio {stadium}."

        top5_fatores.append(""f"**{home_team} {top5_casa_result}** {frase_opponent}")
    else:
        top5_fatores.append(""f"**{home_team} {top5_casa_result}** contra **{top5_casa_opponent}**, uma das equipas mais fortes nesta edição da {home_liga} — sinal de robustez e dominância mesmo contra adversários difíceis e disciplinados.")

if top5_fora:
    stats_opponent = stats_away.get(top5_fora_opponent, {})
    if stats_opponent:
        media_gm_casa = stats_opponent.get("media_gm_casa", 0)
        media_gs_casa = stats_opponent.get("media_gs_casa", 0)
        sem_sofrer_casa = stats_opponent.get("sem_sofrer_casa", 0)
        sem_marcar_casa = stats_opponent.get("sem_marcar_casa", 0)

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

        pos_opponent = rank_a.get(top5_fora_opponent, (len(rank_a), 0))[0]

        if pos_opponent == 1:
            frase_opponent = f"contra **{top5_fora_opponent}**, a atual líder da competição — um feito extraordinário na sua jornada na {away_liga}."
        elif pos_opponent == 2:
            frase_opponent = f"contra **{top5_fora_opponent}**, a segunda classificada da {away_liga} — um resultado de grande impacto."
        elif pos_opponent <= 3:
            frase_opponent = f"contra **{top5_fora_opponent}**, a terceira classificada da {away_liga} — um sinal de maturidade e qualidade."
        else:
            frase_opponent = f"contra **{top5_fora_opponent}**, uma das equipas mais fortes deste ano na {away_liga} — demonstração de capacidade para superar adversários de alto nível."

        if media_gm_casa > 1.8 or media_gs_casa < 1.2 or sem_sofrer_casa > 3:
            frase_opponent = f"contra **{top5_fora_opponent}**, umas das principais equipas da corrida ao título, revelando estar ao nível dos atuais líderes da {away_liga}."

        top5_fatores.append("<br>"f"**{away_team} {top5_fora_result}** {frase_opponent}")
    else:
        top5_fatores.append("<br>"f"**{away_team} {top5_fora_result}** contra **{top5_fora_opponent}**, um dos colossos da {away_liga}, atualmente, demonstrando de capacidade para superar adversários de alto nível.")

if top5_fatores:
    linhas.append("")
    linhas.extend(top5_fatores)

# --- INTERPRETAÇÃO TÁTICA FINAL ---
linhas.append("")
linhas.append("**Interpretação tática:**")

def generate_dynamic_phrase(home_team, away_team, pick, p1, px, p2):
    """
    Gera uma frase de interpretação tática única com vocabulário rico e estrutura variada.
    """
    
    # === BLOCOS MODULARES ===
    subjects_1 = [
        f"Diante da **fortaleza caseira** de **{home_team}**",
        f"Com **{home_team}** a erguer-se como **senhor do seu território**",
        f"Face à **consistência tática** de **{home_team}** em casa",
        f"Dada a **autoridade ofensiva** de **{home_team}** no seu reduto",
        f"Considerando a **resiliência defensiva** de **{home_team}** em casa"
    ]
    
    subjects_2 = [
        f"Apesar da **fragilidade itinerante** de **{away_team}**",
        f"contra um **{away_team}** que tropeça sistematicamente fora de casa",
        f"enquanto **{away_team}** luta para encontrar identidade longe do seu lar",
        f"frente a uma **{away_team}** marcada por hesitações externas",
        f"numa altura em que **{away_team}** carece de clareza ofensiva fora de portas"
    ]
    
    verbs_1 = [
        "a vitória da casa impõe-se como desfecho natural",
        "os três pontos tendem a permanecer sob o teto do anfitrião",
        "o prognóstico favorece claramente os donos do espetáculo",
        "a balança pende inequivocamente para o lado caseiro",
        "a noite promete pertencer aos senhores da casa"
    ]
    
    subjects_2_win = [
        f"**{away_team}** chega com a **mentalidade de quem não teme fronteiras**",
        f"Enquanto **{home_team}** oscila entre ambição e inconstância",
        f"Com **{away_team}** a transformar-se numa **máquina de capitalizar erros alheios**",
        f"Longe de ser um mero visitante, **{away_team}** atua como **predador de redutos**",
        f"Diante da **vulnerabilidade caseira** de **{home_team}**"
    ]
    
    verbs_2 = [
        "a vitória do visitante emerge como prognóstico tecnicamente fundamentado",
        "a equipa visitante parte com argumentos sólidos para levar os três pontos",
        "o desfecho mais coerente aponta para a superioridade dos forasteiros",
        "a conjuntura favorece claramente os que chegam de fora",
        "a vitória fora de casa surge como consequência de um projeto tático superior"
    ]
    
    subjects_draw = [
        f"Num embate onde **ataque e defesa se neutralizam**",
        f"Quando dois blocos compactos se encontram",
        f"Face à **paridade tática** entre as formações",
        f"Num duelo marcado por **inteligência posicional**",
        f"Diante do **respeito mútuo** que define este confronto"
    ]
    
    verbs_draw = [
        "o empate emerge como o veredito mais justo",
        "o resultado igualado é a conclusão matemática mais lógica",
        "a partilha dos pontos é o desfecho que honra a competitividade",
        "o equilíbrio justo se expressa na igualdade do marcador",
        "o empate representa o reconhecimento tácito de forças equivalentes"
    ]
    
    # === LÓGICA DE SELEÇÃO ===
    if pick == "1":
        subject = random.choice(subjects_1)
        complement = random.choice(subjects_2)
        verb = random.choice(verbs_1)
        return f"{subject} {complement}, {verb}."
    
    elif pick == "2":
        subject = random.choice(subjects_2_win)
        verb = random.choice(verbs_2)
        return f"{subject}, {verb}."
    
    elif pick == "X":
        subject = random.choice(subjects_draw)
        verb = random.choice(verbs_draw)
        return f"{subject}, {verb}."
    
    elif pick == "1X":
        phrases = [
            f"**{home_team}** construiu uma **fortaleza quase inexpugnável** em casa, enquanto **{away_team}** não demonstra capacidade de assalto fora — a não derrota da equipa da casa é praticamente garantida.",
            f"Mesmo que a vitória não se concretize, **{home_team}** possui **argumentos defensivos robustos** para assegurar, no mínimo, a partilha dos pontos frente a um **{away_team}** carente de mordente ofensivo.",
            f"Com **resiliência tática** em casa e o **apoio incondicional do seu público**, **{home_team}** raramente sucumbe no seu reduto — **{away_team}** terá um desafio hercúleo para levar algo mais do que um empate.",
            f"A **base defensiva sólida** de **{home_team}** contrasta com a **inconsistência estrutural** de **{away_team}** fora de casa, criando um cenário onde a não derrota da equipa anfitriã é o desfecho mais coerente.",
            f"**{home_team}** domina os seus domínios com autoridade, enquanto **{away_team}** se debate com **falta de eficácia externa** — a aposta em 1X é sinónimo de prudência inteligente."
        ]
        return random.choice(phrases)
    
    elif pick == "X2":
        phrases = [
            f"**{away_team}** demonstra **maturidade competitiva** fora de casa, contrastando com a **instabilidade caseira** de **{home_team}** — a não derrota da equipa visitante é um prognóstico sólido.",
            f"Enquanto **{home_team}** luta por consistência no seu reduto, **{away_team}** apresenta-se como uma **unidade coesa e pragmática fora de portas** — a conjuntura favorece claramente os visitantes.",
            f"Com **disciplina defensiva exemplar** e **eficácia em momentos-chave**, **{away_team}** possui o perfil ideal para capitalizar os **lapsos caseiros** de **{home_team}**.",
            f"**{away_team}** transformou-se numa **especialista em neutralizar redutos hostis**, e **{home_team}** tem sido generoso em conceder oportunidades em casa — a aposta em X2 reflete uma análise realista.",
            f"Num confronto onde **{home_team}** falha em impor o seu jogo em casa e **{away_team}** demonstra **capacidade de adaptação tática fora**, o empate ou vitória do visitante emerge como o cenário mais plausível."
        ]
        return random.choice(phrases)
    
    else:
        return f"A análise aponta para **{pick}** como resultado mais provável."

frase_final = generate_dynamic_phrase(home_team, away_team, pick, p1, px, p2)
linhas.append(frase_final)

resumo = "\n".join(linhas)

# ================================================
# EXIBIÇÃO
# ================================================
st.markdown(
        f"<div style='text-align: center; margin-top: 12px; font-size: 1.4em; font-weight: bold;'>"
        f"ESCOLHA: <b>{pick}</b> <small style='font-weight: normal; font-size: 0.9em;'>({resultado_hip})</small>"
        f"</div>",
        unsafe_allow_html=True
    )
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.4em;'>{home_team}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-family: monospace; font-size: 1.2em; color: #555;'>{form_home}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 1em;'>{p1:.2f}%</div>", unsafe_allow_html=True)

with col2:
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.4em;'>Empate</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 1em;'>{px:.2f}%</div>", unsafe_allow_html=True)


with col3:
    st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.4em;'>{away_team}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-family: monospace; font-size: 1.2em; color: #555;'>{form_away}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size: 1em;'>{p2:.2f}%</div>", unsafe_allow_html=True)



st.markdown(resumo, unsafe_allow_html=True)

st.caption("Dados: football-data.co.uk • Temporada 2025/26")