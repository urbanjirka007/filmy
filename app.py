import streamlit as st
from tmdbv3api import TMDb, Movie
import requests

# Nastavení stránky
st.set_page_config(page_title="Filmový Zápisník", page_icon="🎬", layout="centered")
st.title("🎬 Filmový Zápisník do Notion")

# 1. KONFIGURACE API KLÍČŮ
# !!! SEM VLOŽ SVŮJ TMDB KLÍČ (nyní je tu prázdný text, bez něj vyhledávání vyhodí chybu) !!!
TMDB_API_KEY = "1c1dcf69150a811c9196c338045983a3" 
NOTION_TOKEN = "ntn_p75258623695St2zIkmATryx6pmfPexDXD3gEjupbLs01a"
NOTION_DATABASE_ID = "1b3cdbdc7dd84b0099add0811623d9b7"

# Inicializace TMDB
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
tmdb.language = "cs-CZ"
movie_service = Movie()

# Funkce pro odeslání dat do Notion
def ulozit_do_notion(titulek, popis, poster_url, hodnoceni, datum_vydani):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Omezení délky popisu pro Notion property (max 2000 znaků)
    zkraceny_popis = popis[:1900] + "..." if len(popis) > 1900 else popis
    
    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Název": {
                "title": [
                    { "text": { "content": titulek } }
                ]
            },
            "Hodnocení": {
                "number": float(hodnoceni) if hodnoceni else 0.0
            },
            "Datum vydání": {
                "rich_text": [
                    { "text": { "content": str(datum_vydani) } }
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{ "type": "text", "text": { "content": "Popis filmu" } }]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{ "type": "text", "text": { "content": zkraceny_popis if zkraceny_popis else "Bez popisu." } }]
                }
            }
        ]
    }
    
    # Pokud máme plakát, přidáme ho jako cover (obálku) stránky a také do obsahu
    if poster_url:
        payload["cover"] = {
            "type": "external",
            "external": { "url": poster_url }
        }
        payload["children"].append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": { "url": poster_url }
            }
        })
        
    response = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
    return response

# Vyhledávací pole v aplikaci
query = st.text_input("Zadej název filmu:", "", placeholder="Např. Inception")

if query:
    results = movie_service.search(query)
    if results:
        film = results[0]
        details = movie_service.details(film.id)
        
        st.write("---")
        st.header(details.title)
        
        col1, col2 = st.columns([1, 2])
        poster_url = f"https://image.tmdb.org/t500{details.poster_path}" if details.poster_path else None
        
        with col1:
            if poster_url:
                st.image(poster_url, use_column_width=True)
            else:
                st.info("Plakát není k dispozici.")
                
        with col2:
            st.subheader("O čem to je:")
            st.write(details.overview if details.overview else "Český popis není k dispozici.")
            st.markdown(f"**⭐ Hodnocení:** {details.vote_average} / 10")
            st.markdown(f"**📅 Vydáno:** {details.release_date}")
            st.write("")
            
            # Tlačítko pro uložení
            if st.button("🚀 Uložit film do Notion", type="primary"):
                with st.spinner("Ukládám do Notion..."):
                    res = ulozit_do_notion(
                        details.title,
                        details.overview,
                        poster_url,
                        details.vote_average,
                        details.release_date
                    )
                    if res.status_code == 200:
                        st.success("🎉 Film byl úspěšně uložen do tvého Notion!")
                    else:
                        st.error(f"Chyba při ukládání: {res.status_code}")
                        st.json(res.json())
    else:
        st.warning("Film nebyl nalezen.")
