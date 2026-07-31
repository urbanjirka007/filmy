import streamlit as st
from tmdbv3api import TMDb, Movie
import requests

# Nastavení stránky
st.set_page_config(page_title="Filmový Zápisník", page_icon="🎬", layout="centered")
st.title("🎬 Filmový Zápisník do Notion")

# 1. KONFIGURACE API KLÍČŮ
TMDB_API_KEY = "1c1dcf69150a811c9196c338045983a3" 
NOTION_TOKEN = "ntn_p75258623695St2zIkmATryx6pmfPexDXD3gEjupbLs01a"
# Tady necháme ID přesně tak, jak jsi ho měl, a kód si ho sám vyčistí
NOTION_DATABASE_ID = "2b3b46036c594b3ba7d54c7e56dd763e?v=cd6dfdb83d5145628f15736ff61c7247"

# Inicializace TMDB
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
tmdb.language = "cs-CZ"
movie_service = Movie()

# Funkce pro odeslání dat do Notion
def ulozit_do_notion(titulek, popis, poster_url, hodnoceni, datum_vydani):
    # Automatické vyčištění ID databáze (odstranění pomlček, pokud tam jsou)
    clean_db_id = NOTION_DATABASE_ID.replace("-", "").strip()
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    zkraceny_popis = popis[:1900] + "..." if len(popis) > 1900 else popis
    
    payload = {
        "parent": { "database_id": clean_db_id },
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
