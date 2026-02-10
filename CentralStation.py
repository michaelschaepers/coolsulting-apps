# ----------------------------------------------------------------------------
# DATEI: CentralStation.py
# STAND: 10.02.2026 - 09:05 Uhr
# BESCHREIBUNG: Haupt-Cockpit (Fix: Alle CSS-Klammern verdoppelt!)
# ----------------------------------------------------------------------------
import streamlit as st
import os
import base64
import importlib

# ============================================================
# SEITE KONFIGURIEREN (Muss zwingend als erstes stehen)
# ============================================================
st.set_page_config(page_title="°central STATION", layout="wide")

def get_font_as_base64(font_path):
    if os.path.exists(font_path):
        with open(font_path, "rb") as font_file:
            return base64.b64encode(font_file.read()).decode()
    return None

def main():
    # --- DESIGN VARIABLEN ---
    BG_COLOR = "#36A9E1"            # Hellblau (Hintergrund & Akzente)
    TEXT_GRAY = "#3C3C3B"           # Grau (Standard Text)
    FONT_FILE = "POE Vetica UI.ttf"

    # --- CSS SCHUTZ (Wird IMMER geladen) ---
    font_base64 = get_font_as_base64(FONT_FILE)
    if font_base64:
        # WICHTIG: Alle CSS-Klammern muessen hier doppelt sein {{ }}
        st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'POE Helvetica UI';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        
        /* Globaler Font-Fix */
        html, body, [data-testid="stAppViewContainer"], * {{
            font-family: 'POE Helvetica UI', sans-serif !important;
        }}
        
        /* Hintergrund */
        .stApp {{ background-color: {BG_COLOR}; }}
        
        /* Header Klassen */
        .cs-welcome {{ 
            font-size: 34px !important; 
            text-align: center; 
            color: {TEXT_GRAY} !important; 
            margin-top: -50px !important; 
        }}
        .cs-title-line {{ 
            font-size: 52px !important; 
            font-weight: bold !important; 
            text-align: center; 
            margin-top: -35px !important; 
            line-height: 1.0 !important; 
        }}
        .white-part {{ color: white !important; }}
        .gray-part {{ color: {TEXT_GRAY} !important; }}
        
        /* HR Linie */
        hr {{ 
            border: 1px solid {TEXT_GRAY} !important; 
            opacity: 0.3 !important; 
            margin: 15px 0 !important; 
        }}

        /* --- STYLING FÜR DAS AUSWAHLFELD (MODUSFELD) --- */
        div[data-baseweb="select"] {{ 
            background-color: white !important; 
            border-radius: 12px !important; 
            border: 2px solid {TEXT_GRAY} !important; 
        }}
        
        /* Text im Auswahlfeld: HELLBLAU */
        div[data-baseweb="select"] div {{
            color: {BG_COLOR} !important;
            font-weight: bold !important;
        }}
        
        /* Icon (Pfeil) im Auswahlfeld: HELLBLAU */
        div[data-baseweb="select"] svg {{
            fill: {BG_COLOR} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.error(f"Schriftdatei '{FONT_FILE}' nicht gefunden!")

    # ============================================================
    # HEADER - DIESER TEIL BLEIBT IMMER SICHTBAR
    # ============================================================
    st.markdown('<p class="cs-welcome">Willkommen im Cockpit der</p>', unsafe_allow_html=True)

    _, col_m, _ = st.columns([1, 1.2, 1]) 
    with col_m:
        logo_path = "Coolsulting_Logo_ohneHG_outlines_weiß.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
    
    st.markdown(f"""
        <div class="cs-title-line">
            <span class="white-part">°Central</span> <span class="gray-part">STATION</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- NAVIGATION ---
    tool_wahl = st.selectbox("Anwendung auswählen und starten:", 
                             ["Übersicht", 
                              "Heizlastberechnung für Wärmepumpen (WP Modul 1)", 
                              "WP Quick-Kalkulator (Quickie)"])

    st.markdown("---")

    # ============================================================
    # DYNAMISCHER INHALT (Hier laden die Module UNTER dem Header)
    # ============================================================
    if tool_wahl == "Übersicht":
        st.markdown(f'<p style="color: {TEXT_GRAY};">System-Status: Bereit</p>', unsafe_allow_html=True)

    elif tool_wahl == "Heizlastberechnung für Wärmepumpen (WP Modul 1)":
        try:
            import Waermepumpen_Auslegung as wp_modul
            importlib.reload(wp_modul)
            wp_modul.main() 
        except ImportError:
            try:
                # Fallback Kleinschreibung
                import waermepumpen_Auslegung as wp_modul
                importlib.reload(wp_modul)
                wp_modul.main()
            except Exception as e:
                st.error(f"Fehler: Modul-Datei 'Waermepumpen_Auslegung.py' nicht gefunden. ({e})")
        except Exception as e:
            st.error(f"Fehler beim Laden von Modul 1: {e}")

    elif tool_wahl == "WP Quick-Kalkulator (Quickie)":
        try:
            import WP_Quick_Kalkulator as quickie
            importlib.reload(quickie)
            quickie.main()
        except Exception as e:
            st.error(f"Fehler beim Laden des Quickies: {e}")

if __name__ == '__main__':
    main()