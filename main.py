#Code - Version 08.02.2026 - Kursive Markierung Update2, Liste fertig

import streamlit as st
import pandas as pd
import random
import re

st.markdown("""
<style>
div.stButton > button {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    color: #1f77b4;
    text-align: left;
}
div.stButton > button {
    color: #1f77b4;
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
def load_data():
    df = pd.read_excel("tabelle_1_main.xlsx")
    df = df.fillna("")
    return df


df = load_data()

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


def search_phrasemes(df, query, mode, theme_filter, style_filter):
    results = df.copy()

    # --- Textsuche ---
    if query:
        query = query.lower()
        if mode == "OR":
            words = query.split()
            mask = results["phrasem_de"].str.lower().apply(
                lambda x: any(w in x for w in words)
            )
            results = results[mask]

        elif mode == "AND":
            words = query.split()
            mask = results["phrasem_de"].str.lower().apply(
                lambda x: all(w in x for w in words)
            )
            results = results[mask]

        elif mode == "EXACT":
            results = results[
                results["phrasem_de"].str.lower().str.contains(query, regex=False)
            ]

    # --- Themenfilter ---
    if theme_filter:
        mask = (
            (results["thema_1"] == theme_filter)
            | (results["thema_2"] == theme_filter)
            | (results["thema_3"] == theme_filter)
        )
        results = results[mask]

    # --- Sprachstilfilter ---
    if style_filter:
        results = results[results["sprachstil_hereglee"] == style_filter]

    return results.sort_values("phrasem_de")


# --------------------------------------------------
# Text-Highlighting (Phrasem & deutsche Wörter)
# --------------------------------------------------


def highlight_words(text, highlight_words):
    if not isinstance(text, str):
        return text

    if not isinstance(highlight_words, str) or not highlight_words.strip():
        return text

    # Wörter aus der Spalte
    words = [w.strip() for w in highlight_words.split(";") if w.strip()]

    # Längere Wörter zuerst (gemacht vor mach)
    words = sorted(words, key=len, reverse=True)

    for w in words:
        pattern = re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE)
        text = pattern.sub(r"_\g<0>_", text)

    return text




def show_list_by_themes():
    st.header("📚 Phraseme nach Themen")

    for theme in get_all_themes(df):
        with st.expander(theme, expanded=False):

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
                "Liste nach Themen",
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
        st.markdown( """ <div style=" position: fixed; bottom: 10px; left: 10px; font-size: 0.8em; color: gray; "> GIP-Projekt von MUBIS und RUB <br>Mit Unterstützung vom DAAD </div> """, unsafe_allow_html=True, )

    # 👉 Seitenwechsel-Logik AUSSERHALB des Sidebars
    if "last_page" not in st.session_state:
        st.session_state.last_page = page

    if page != st.session_state.last_page:
        st.session_state.view = "search"
        st.session_state.random_mode = False
        st.session_state.last_page = page

    return page



def show_search_page():
    #st.header("Phraseologisches Glossar")
    #st.subheader("Deutsch – Mongolisch")
    st.markdown(
    """
    <h1 style="color:#1f77b4;">Phraseologisches Glossar</h1>
    <h3 style="color:gray;">Deutsch – Mongolisch</h3>
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
            key="search_query"
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
        f"<h5 style='color:gray'>Treffer gefunden: {len(results)}</h5>",
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
        f"<h2 style='color:#1f77b4'>{phrasem['phrasem_de']}</h2>",
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
        st.markdown(text)

    if phrasem["grammatik_anhaar"]:
        text = highlight_words(
            phrasem["grammatik_anhaar"],
            phrasem.get("highlight_words", "")
        )
        st.markdown("**Grammatische Besonderheit:**")
        st.markdown(text)

    if phrasem["herkunft_garal"]:
        text = highlight_words(
            phrasem["herkunft_garal"],
            phrasem.get("highlight_words", "")
        )
        st.markdown("**Herkunft:**")
        st.markdown(text)

    st.markdown("**Beispiele:**")
    for b in ["beispiel_1", "beispiel_2", "beispiel_3"]:
        if phrasem.get(b):
            text = highlight_words(
                phrasem[b],
                phrasem.get("highlight_words", "")
            )
            st.markdown(f"• {text}")

    st.divider()

    # -------- Navigation --------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Zurück"):
            if st.session_state.active_source == "list":
                st.session_state.view = "list"
            else:
                st.session_state.view = "search"
            st.rerun()



    with col2:
        if st.button("Weiter"):
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


elif page == "Liste nach Themen":
    st.session_state.random_mode = False

    if st.session_state.view == "detail":
        show_phrasem_card()
    else:
        st.session_state.view = "list"
        show_list_by_themes()


elif page == "Zufälliges Phrasem":
    st.session_state.random_mode = True
    show_random_phrasem()
    show_phrasem_card()


elif page == "Theorie Phraseologie":
    st.header("Theorie Phraseologie")
    st.write("Hier kommt später die Theorie …")


elif page == "Impressum":
    st.header("Impressum")
    st.write("Kontakt, Impressum, Projektbeschreibung")

    
    if "version" in df.columns:
        st.caption(f"📊 Datenstand: {df.iloc[0]['version']}")
    else:
        st.caption("📊 Datenstand: nicht angegeben")


