import streamlit as st
import pandas as pd
import random

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

# --------------------------------------------------
# Daten laden (Excel)
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("tabelle_1_main.xlsx")
    df = df.fillna("")
    return df


df = load_data()


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
        )

        st.markdown("")
        st.markdown(
            """
            <div style="
                position: fixed;
                bottom: 10px;
                left: 10px;
                font-size: 0.8em;
                color: gray;
            ">
                GIP-Projekt von MUBIS und RUB <br>Mit Unterstützung vom DAAD
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            "Suchoption",
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

    # Noch keine Suche ausgeführt
    if results is None:
        return

    # Suche ohne Treffer
    if results.empty:
        st.markdown(
            "<h5 style='color:gray'>Treffer gefunden: 0 </h5>",
            unsafe_allow_html=True,
            )
        st.info("Versuche einen anderen Suchbegriff oder ändere die Filter.")
        return

    # Treffer vorhanden
    st.markdown(f"<h5 style='color:gray'>Treffer gefunden: {len(results)} </h5>", unsafe_allow_html=True,)

    for idx, row in results.reset_index(drop=True).iterrows():
        if st.button(row["phrasem_de"], key=row["phrasem_id"]):
            st.session_state.selected_phrasem_id = row["phrasem_id"]
            st.session_state.current_index = idx
            st.session_state.view = "detail"
            st.rerun()



def show_phrasem_card():
    results = st.session_state.search_results
    idx = st.session_state.current_index

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
        st.markdown(f"**Anmerkung:** {phrasem['hinweis_tailbar']}")

    if phrasem["grammatik_anhaar"]:
        st.markdown(f"**Grammatische Besonderheit:** {phrasem['grammatik_anhaar']}")

    if phrasem["herkunft_garal"]:
        st.markdown(f"**Herkunft:** {phrasem['herkunft_garal']}")
    
    st.markdown("**Beispiele:**")
    for b in ["beispiel_1", "beispiel_2", "beispiel_3"]:
        if phrasem[b]:
            st.write("•", phrasem[b])

    st.divider()

    if st.session_state.random_mode:

        if st.button("🎲 Weiteres zufälliges Phrasem"):
            show_random_phrasem()

    else:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("← Zurück zur Trefferliste"):
                st.session_state.view = "search"
                st.rerun()

        with col2:
            if st.button("Weiteres Phrasem"):
                if st.session_state.current_index + 1 < len(st.session_state.search_results):
                    st.session_state.current_index += 1
                    st.rerun()
                else:
                    st.session_state.view = "search"
                    st.rerun()


def show_random_phrasem():
    random_row = df.sample(1).iloc[0]

    st.session_state.random_mode = True
    st.session_state.search_results = df.loc[[random_row.name]]
    st.session_state.current_index = 0
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


elif page == "Zufälliges Phrasem":
    st.session_state.random_mode = True
    show_random_phrasem()
    show_phrasem_card()


elif page == "Liste nach Themen":
    st.session_state.view = "search"
    st.session_state.random_mode = False

    st.header("📚 Phraseme nach Themen")
    for theme in get_all_themes(df):
        st.subheader(theme)
        subset = df[
            (df["thema_1"] == theme)
            | (df["thema_2"] == theme)
            | (df["thema_3"] == theme)
        ]
        for _, row in subset.iterrows():
            st.write("–", row["phrasem_de"])


elif page == "Theorie Phraseologie":
    st.session_state.view = "search"
    st.session_state.random_mode = False

    st.header("Theorie Phraseologie")
    st.write("Hier kommt später die Theorie …")


elif page == "Impressum":
    st.session_state.view = "search"
    st.session_state.random_mode = False

    st.header("Impressum")
    st.write("Kontakt, Impressum, Projektbeschreibung")
