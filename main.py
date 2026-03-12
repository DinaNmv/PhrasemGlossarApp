#Code - Version 11.03.2026 15.30 - Neue Hintergrund- und Schriftfarbe, Navi expanded, gip

import streamlit as st
import pandas as pd
import random
import re
import os
import time
import streamlit.components.v1 as components
import base64

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Anklickbares Phrasem (Button):
st.markdown("""
<style>
div.stButton > button {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    color: #33c7f7;
    text-align: left;
}
div.stButton > button {
    color: #33c7f7;
    font-size: 0.95rem;
}

}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Initialisierung Session State
# --------------------------------------------------
if "selected_phrasem_id" not in st.session_state:
    st.session_state.selected_phrasem_id = None

if "search_results" not in st.session_state:
    st.session_state.search_results = None

if "view" not in st.session_state:
    st.session_state.view = "search"   # results | card

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "random_mode" not in st.session_state:
    st.session_state.random_mode = False

if "active_results" not in st.session_state:
    st.session_state.active_results = None

if "active_index" not in st.session_state:
    st.session_state.active_index = 0

if "active_source" not in st.session_state:
    st.session_state.active_source = None

if "last_page" not in st.session_state:
    st.session_state.last_page = "Startseite"

if "list_scroll_key" not in st.session_state:
    st.session_state.list_scroll_key = None



# --------------------------------------------------
# Daten laden (Excel)
# --------------------------------------------------

@st.cache_data
def load_data(file_path, file_mtime):
    df = pd.read_excel(file_path)
    df = df.fillna("")
    df = df.astype(str)  # alles als String erzwingen
    return df

file_path = "tabelle_1_main.xlsx"
file_mtime = os.path.getmtime(file_path)

df = load_data(file_path, file_mtime)

#DEBUG TESTEN:

#st.write("DEBUG – Spaltennamen aus Excel:")
#for c in df.columns:
    #st.write(f"→ '{c}'")

#import os
#st.write("DEBUG – Excel-Datei existiert:", os.path.exists("tabelle_1_main.xlsx"))


# --------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------
def get_all_themes(dataframe):
    themes = set()
    for col in ["thema_1", "thema_2", "thema_3"]:
        themes.update(dataframe[col].unique())
    themes.discard("")
    return sorted(themes)

# Spalten, die bei der Textsuche berücksichtigt werden
SEARCH_COLUMNS = [
    "phrasem_de",
    "thema_1",
    "thema_2",
    "thema_3",
]

# aus Phrasem + Themen einen Suchtext:
def row_contains_any(row, words):
    text = " ".join(str(row[col]) for col in SEARCH_COLUMNS).lower()

    text_words = text.split()
    normalized_text_words = [normalize_word(w) for w in text_words]

    normalized_query_words = [normalize_word(w) for w in words]

    return any(
        qw in tw
        for qw in normalized_query_words
        for tw in normalized_text_words
    )


def row_contains_all(row, words):
    text = " ".join(str(row[col]) for col in SEARCH_COLUMNS).lower()

    text_words = text.split()
    normalized_text_words = [normalize_word(w) for w in text_words]

    normalized_query_words = [normalize_word(w) for w in words]

    return all(
        any(qw in tw for tw in normalized_text_words)
        for qw in normalized_query_words
    )


#Wortsuche optimierung
def normalize_word(word):
    word = word.lower()
    endings = [
        "lich", "keit", "heit", "ung", "en", "er", "e", "n", "s"
    ]

    for end in endings:
        if word.endswith(end) and len(word) > len(end) + 3:
            word = word[:-len(end)]
            break

    return word

# -----------------------------
# Textsuche (Phrasem + Themen)
# -----------------------------

def search_phrasemes(df, query, mode, theme_filter, style_filter):
    results = df.copy()

    if query:
        words = query.lower().split()

        if mode == "OR":
            mask = results.apply(
                lambda row: row_contains_any(row, words),
                axis=1
            )
            results = results[mask]

        elif mode == "AND":
            mask = results.apply(
                lambda row: row_contains_all(row, words),
                axis=1
            )
            results = results[mask]

        elif mode == "EXACT":
            query_l = query.lower()
            mask = results.apply(
                lambda row: query_l in " ".join(
                    str(row[col]).lower() for col in SEARCH_COLUMNS
                ),
                axis=1
            )
            results = results[mask]

    # -----------------------------
    # Themenfilter (Selectbox)
    # -----------------------------
    if theme_filter:
        results = results[
            (results["thema_1"] == theme_filter)
            | (results["thema_2"] == theme_filter)
            | (results["thema_3"] == theme_filter)
        ]

    # -----------------------------
    # Sprachstilfilter
    # -----------------------------
    if style_filter:
        results = results[
            results["sprachstil_hereglee"] == style_filter
        ]

    return results.sort_values("phrasem_de")


# --------------------------------------------------
# Text-Highlighting (Phrasem & deutsche Wörter)
# --------------------------------------------------


def highlight_words(text, highlight_words, gray=False):

    if not isinstance(text, str):
        return text

    if not isinstance(highlight_words, str) or not highlight_words.strip():
        return text

    words = [w.strip() for w in highlight_words.split(";") if w.strip()]

    # längere Wörter zuerst → verhindert Teil-Ersetzungen
    words = sorted(words, key=len, reverse=True)

    for w in words:

        # Wortgrenzen verwendet
        pattern = re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE)

        if gray:
            replacement = lambda m: f"<span style='color:#ADBED2'><em>{m.group(0)}</em></span>"
        else:
            replacement = lambda m: f"<em>{m.group(0)}</em>"

        text = pattern.sub(replacement, text)

    return text


# -----------------------------
# Phraseme nach Themen - Die Liste
# -----------------------------

def show_list_by_themes():
    st.header("🗂️ Phraseme nach Themen")


    for theme in get_all_themes(df):
        expanded = (
            "active_theme" in st.session_state
            and st.session_state.active_theme == theme
        )

        with st.expander(theme, expanded=expanded):

            subset = df[
                (df["thema_1"] == theme)
                | (df["thema_2"] == theme)
                | (df["thema_3"] == theme)
            ].reset_index(drop=True)

            for idx, row in subset.iterrows():

                if st.button(
                    f"– {row['phrasem_de']}",
                    key=f"accordion_{theme}_{row['phrasem_id']}"
                ):
                    st.session_state.active_results = subset
                    st.session_state.active_index = idx
                    st.session_state.active_source = "list"
                    st.session_state.active_theme = theme  # NEU
                    st.session_state.view = "detail"
                    st.rerun()


# --------------------------------------------------
# UI-Komponenten
# --------------------------------------------------
def sidebar_navigation():
    with st.sidebar:
        page = st.radio(
            "Menü",
            [
                "Startseite",
                "Phraseme nach Themen",
                "Zufälliges Phrasem",
                "Theorie Phraseologie",
                "Impressum",
            ],
            key="page_radio"
        )

        # Abstand nach unten
        #st.markdown("<br><br><br><br>", unsafe_allow_html=True)

        # Footer im Sidebar
        st.markdown("") 
        st.markdown( """ <div style=" position: fixed; bottom: 10px; left: 10px; font-size: 0.8em; color:#9f9fa5; "> GIP-Projekt von MUBIS und RUB <br>Mit Unterstützung vom DAAD <br> <br></div> """, unsafe_allow_html=True, )

    # Seitenwechsel-Logik AUSSERHALB des Sidebars
    if "last_page" not in st.session_state:
        st.session_state.last_page = page

    if page != st.session_state.last_page:
        st.session_state.view = "search"
        st.session_state.random_mode = False
        st.session_state.last_page = page

    return page


# STARTSEITE:

def show_search_page():

    st.markdown(
    """
    <h1 style="color:#33c7f7;">Phraseologisches Glossar</h1>
    <h3 style="color:#9f9fa5;">Deutsch – Mongolisch</h3>
    """,
    unsafe_allow_html=True,
)
    st.markdown(
    "<div style='margin-top: 20px;'></div>",
    unsafe_allow_html=True,
)

    with st.form("search_form"):

        query = st.text_input(
            "Suchbegriff:",
            key="search_query",
            placeholder="z. B. Liebe, blau, spielen..."
        )

        search_mode = st.radio(
            "Suchoption:",
            ["OR", "AND", "EXACT"],
            format_func=lambda x: {
                "OR": "eines der Wörter",
                "AND": "alle Wörter",
                "EXACT": "genauer Text",
            }[x],
            horizontal=True,
            key="search_mode",
        )

        themes = get_all_themes(df)
        selected_theme = st.selectbox(
            "Thema filtern:",
            [""] + themes,
            key="theme_filter"
        )

        styles = sorted(df["sprachstil_hereglee"].unique())
        selected_style = st.selectbox(
            "Sprachstil:",
            [""] + styles,
            key="style_filter"
        )

        submitted = st.form_submit_button("Suchen")

    # Enter ODER Button → gleicher Code
    if submitted:
        results = search_phrasemes(
            df,
            query,
            search_mode,
            selected_theme,
            selected_style
        )

        st.session_state.search_results = results
        st.session_state.selected_phrasem_id = None
        st.session_state.view = "search"
        st.rerun()


def show_results():
    results = st.session_state.search_results

    if results is None:
        return

    if results.empty:
        st.info("Keine Treffer gefunden.")
        return

    st.markdown(
        f"<h5 style='color:#9f9fa5'>Treffer gefunden: {len(results)}</h5>",
        unsafe_allow_html=True,
    )

    results = results.reset_index(drop=True)

    for idx, row in results.iterrows():
        if st.button(row["phrasem_de"], key=f"search_{row['phrasem_id']}"):
            st.session_state.active_results = results
            st.session_state.active_index = idx
            st.session_state.active_source = "search"
            st.session_state.view = "detail"
            st.rerun()


def show_phrasem_card():
    results = st.session_state.active_results
    idx = st.session_state.active_index

    if results is None or results.empty:
        st.warning("Kein Phrasem ausgewählt.")
        return

    phrasem = results.iloc[idx]

    st.markdown(
        f"<h2 style='color:#33c7f7'>{phrasem['phrasem_de']}</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(f"**Bedeutung:** {phrasem['bedeutung']}")

    themen = [
        phrasem[t]
        for t in ["thema_1", "thema_2", "thema_3"]
        if str(phrasem[t]).strip()
    ]
    if themen:
        st.markdown(f"**Thema:** {' – '.join(themen)}")

    if phrasem["sprachstil_hereglee"]:
        st.markdown(f"**Register:** {phrasem['sprachstil_hereglee']}")

    if phrasem["hinweis_tailbar"]:
        text = highlight_words(
            phrasem["hinweis_tailbar"],
            phrasem.get("highlight_words", "")
        )
        st.markdown("**Anmerkung:**")
        st.markdown(f"{text}", unsafe_allow_html=True)

    if phrasem["grammatik_anhaar"]:
        text = highlight_words(
            phrasem["grammatik_anhaar"],
            phrasem.get("highlight_words", "")
        )
        st.markdown("**Grammatische Besonderheit:**")
        st.markdown(f"{text}", unsafe_allow_html=True)

    if phrasem["herkunft_garal"]:
        text = highlight_words(
            phrasem["herkunft_garal"],
            phrasem.get("highlight_words", "")
        )
        st.markdown("**Herkunft:**")
        st.markdown(f"{text}", unsafe_allow_html=True)

    st.markdown("**Beispiele:**")
    for b in ["beispiel_1", "beispiel_2", "beispiel_3", "beispiel_4", "beispiel_5", "beispiel_6"]:
        if phrasem.get(b):
            text = highlight_words(
                phrasem[b],
                phrasem.get("highlight_words", ""),
                gray=True
            )
            st.markdown(f"• {text}", unsafe_allow_html=True)


    if phrasem.get("aequivalent_adil"):

        st.markdown("**Äquivalente und Varianten:**")

        items = [x.strip() for x in phrasem["aequivalent_adil"].split(";") if x.strip()]

        for i in items:
            st.markdown(
                f"– <span style='color:#ADBED2'><em>{i}</em></span>",
                unsafe_allow_html=True
            )




    st.divider()

    # -------- Navigation --------
    col1, col2 = st.columns(2)

    # Button Styling Weiter/Zürück
    st.markdown("""
    <style>
    div.stButton > button:first-child {
    font-size: 28px;
    color: #ADBED2;
    background-color: transparent;
    border: none;
    }
    div.stButton > button:first-child:hover {
    color: #33c7f7;
    }
    </style>    
    """, unsafe_allow_html=True)


    with col1:
        if st.button("⟵ zurück"):
            if st.session_state.active_source == "list":
                st.session_state.view = "list"
            else:
                st.session_state.view = "search"
            st.rerun()



    with col2:
        if st.button("weiter ⟶"):
            if idx + 1 < len(results):
                st.session_state.active_index += 1
                st.rerun()
            else:
                # Ende → zurück
                if st.session_state.active_source == "search":
                    st.session_state.view = "search"
                elif st.session_state.active_source == "list":
                    st.session_state.view = "list"
                st.rerun()



def show_random_phrasem():
    random_row = df.sample(1)

    st.session_state.active_results = random_row.reset_index(drop=True)
    st.session_state.active_index = 0
    st.session_state.active_source = "random"
    st.session_state.view = "detail"


# --------------------------------------------------
# App-Logik
# --------------------------------------------------

page = sidebar_navigation()

if page == "Startseite":
    st.session_state.random_mode = False

    if st.session_state.view == "search":
        show_search_page()
        show_results()

    elif st.session_state.view == "detail":
        show_phrasem_card()

#if page == "Startseite":

    # Hintergrundbild laden
    #img_base64 = get_base64("background.png")

    #st.markdown(
        #f"""
        #<style>
        #.stApp {{
           # background-image: url("data:image/png;base64,{img_base64}");
           # background-size: cover;
            #background-position: center;
            #background-repeat: no-repeat;
        #}}
        #</style>
        #""",
        #unsafe_allow_html=True
    #)


elif page == "Phraseme nach Themen":
    st.session_state.random_mode = False

    if st.session_state.view == "detail":
        show_phrasem_card()
    else:
        st.session_state.view = "list"
        show_list_by_themes()


elif page == "Zufälliges Phrasem":
    st.header("🎲 Zufälliges Phrasem")
    st.session_state.random_mode = True
    show_random_phrasem()
    show_phrasem_card()


elif page == "Theorie Phraseologie":
    st.header("📚 Theorie Phraseologie")
    st.write("Hier kommt später die Theorie …")


elif page == "Impressum":
    st.header("Impressum")
    st.write("Impressum, Projektbeschreibung, Kontakt")

    st.markdown("---")

    st.markdown("""
    **Angaben gemäß § 5 TMG**

    Max Mustermann  
    Musterstraße 1  
    12345 Musterstadt  
    Deutschland  
    """)

    st.markdown("---")

    # GOOGLE FORM LINK
    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSe2kGpkTJuEx6G7T8ywPklhulf7lhob0eT_JlDrn442IgSZIQ/viewform?usp=dialog"

    components.iframe(
        form_url,
        height=550,
        scrolling=True
    )

    #st.markdown(
        #"[Google-Datenschutzerklärung](https://policies.google.com/privacy?hl=de)"
    #)



    st.markdown("---")
    
    if "version" in df.columns:
        st.caption(f"📊 Datenstand: {df.iloc[0]['version']}")
    else:
        st.caption("📊 Datenstand: nicht angegeben")
    st.write("  App-Version: 11.03.2026 15.30 - Neue Hintergrund- und Schriftfarbe, Navi expanded, gip")


