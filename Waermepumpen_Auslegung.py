# ==========================================
# DATEI: Waermepumpen_Auslegung.py
# ZEITSTEMPEL: 10.02.2026 - 17:50 Uhr
# VERSION: 3.8
#
# ÄNDERUNGEN:
# 1. TEXT: Platzhalter bei "Projekt / Kunde" auf "z.B.: Elke Muster" geändert.
# 2. VERSIONING: App Version auf 3.8 hochgesetzt.
# 3. BEIBEHALTEN: Striktes Header-Format, gedrehte X-Achse (Kalt -> Warm), Logo & Text oben bündig (Y=10), Disclaimer mit geistigem Eigentum.
# ==========================================

import streamlit as st
import os
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import tempfile

# Globale Variable für die App-Version (wird in UI und PDF genutzt)
APP_VERSION = "3.8"

# ==========================================
# 1. PDF KLASSE
# ==========================================
class PDF(FPDF):
    def __init__(self, font_family="Helvetica"):
        super().__init__()
        self.font_family = font_family

    def header(self):
        # Coolsulting Blau
        blue = (54, 169, 225)
        self.set_fill_color(*blue)
        self.rect(0, 0, 210, 40, 'F') 
        
        # Feste Y-Koordinate für perfekte obere Bündigkeit von Logo und Text
        start_y = 10
        
        # Weisses Logo (Breite 100)
        logo = "Coolsulting_Logo_ohneHG_outlines_weiß.png"
        if os.path.exists(logo):
            self.image(logo, x=10, y=start_y, w=100)
            
        # Text exakt auf denselben Y-Startpunkt setzen
        self.set_y(start_y)
        self.set_font(self.font_family, 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, 'Wärmepumpen-Auslegung', align='R', ln=True)
        
        self.set_font(self.font_family, '', 12)
        self.cell(0, 6, 'Modul 1: Heizlast-Berechnung', align='R', ln=True)
        
        # App Version unter Modul 1
        self.set_font(self.font_family, 'I', 10)
        self.cell(0, 6, f'App Version: {APP_VERSION}', align='R', ln=True)
        
        self.ln(15) # Abstand zum Content

    def footer(self):
        self.set_y(-25)
        self.set_font(self.font_family, 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, f'Seite {self.page_no()}', align='C', ln=True)
        
        # Disclaimer
        self.set_font(self.font_family, '', 7)
        self.set_text_color(150, 150, 150)
        disclaimer = ("HINWEIS: Diese Berechnung ist eine überschlägige Auslegung auf Basis der Nutzerangaben "
                      "und geistiges Eigentum des Erstellers. Sie dient als Orientierungshilfe und ersetzt keine "
                      "detaillierte Heizlastberechnung nach DIN EN 12831. Alle Angaben ohne Gewähr. "
                      "Eine fachgerechte Detailplanung ist erforderlich.")
        self.multi_cell(0, 3, disclaimer, align='C')

def create_charts_for_pdf(load_b, load_ww, sperr_kw, norm_temp, bivalenz_temp, total_kw):
    """Generiert temporäre Bilder für das PDF mittels Matplotlib"""
    temp_files = []

    # 1. TORTENDIAGRAMM
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    labels = ['Gebäude', 'Warmwasser', 'Sperrzeit-Zuschlag']
    sizes = [load_b, load_ww, sperr_kw]
    colors = ['#FF4B4B', '#8B0000', '#3C3C3B'] 
    
    clean_labels, clean_sizes, clean_colors = [], [], []
    for l, s, c in zip(labels, sizes, colors):
        if s > 0.05:
            clean_labels.append(l)
            clean_sizes.append(s)
            clean_colors.append(c)

    ax1.pie(clean_sizes, labels=clean_labels, autopct='%1.1f%%', startangle=90, colors=clean_colors, textprops={'fontsize': 9})
    ax1.axis('equal')
    ax1.set_title("Leistungs-Verteilung", fontsize=12, fontweight='bold', pad=10)
    
    pie_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(pie_file.name, bbox_inches='tight', dpi=100)
    plt.close(fig1)
    temp_files.append(pie_file.name)

    # 2. HEIZLAST-KENNLINIE (Gedrehte X-Achse: Kalt links, Warm rechts)
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    x_temps = np.linspace(norm_temp - 2, 20, 50)
    heizgrenze = 15.0
    
    # WW ist die Grundlast. Gebäude-Heizlast kommt dazu, wenn T < 15°C
    y_loads = [(load_b * (heizgrenze - t) / (heizgrenze - norm_temp)) + load_ww if t < heizgrenze else load_ww for t in x_temps]
    
    ax2.plot(x_temps, y_loads, label='Heizlast + WW', color='#36A9E1', linewidth=2)
    
    # Bivalenzpunkt markieren
    ax2.axvline(x=bivalenz_temp, color='red', linestyle='--', label=f'Bivalenzpunkt ({bivalenz_temp}°C)')
    ax2.fill_between(x_temps, 0, y_loads, where=(x_temps <= bivalenz_temp), color='red', alpha=0.15, label='Backup-Betrieb')
    
    # Übergangszeit markieren (+7°C)
    ax2.axvline(x=7, color='green', linestyle=':', label='Übergangszeit (+7°C)')
    
    # WW Grundlast visualisieren (nur wenn WW > 0)
    if load_ww > 0.05:
        ax2.axhline(y=load_ww, color='#8B0000', linestyle=':', label='Warmwasser-Grundlast')
    
    # Text Teillast
    y_text_pos = total_kw * 0.2 if (total_kw * 0.2) > load_ww else load_ww + (total_kw * 0.1)
    ax2.text(5, y_text_pos, "Teillast-Bereich", color='#36A9E1', fontsize=9)

    ax2.set_xlim(norm_temp - 2, 20) # Kalt links, Warm rechts
    ax2.set_ylim(0, total_kw * 1.1)
    ax2.set_xlabel("Außentemperatur (°C)")
    ax2.set_ylabel("Leistung (kW)")
    ax2.set_title("Leistungsbedarf & Bivalenzpunkt", fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(fontsize=8)
    
    line_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(line_file.name, bbox_inches='tight', dpi=100)
    plt.close(fig2)
    temp_files.append(line_file.name)

    return temp_files

def create_pdf_report(projekt, bearbeiter, firma, flaeche, bauweise, wm2, total_kw, 
                      load_b, load_ww, sperr_kw, sperrzeit, 
                      norm_temp, vl_temp, system, bivalenz, backup_typ, infos, warnings, critical):
    
    # --- SETUP ---
    font_path = "POE Vetica UI.ttf"
    font_name = "Helvetica"
    pdf = PDF()
    
    if os.path.exists(font_path):
        try:
            pdf.add_font("POEVetica", "", font_path)
            pdf.add_font("POEVetica", "B", font_path) 
            pdf.add_font("POEVetica", "I", font_path)
            font_name = "POEVetica"
            pdf.font_family = font_name
        except: pass
    
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    text_dark = (60, 60, 59)
    pdf.set_text_color(*text_dark)
    
    # --- KOPFDATEN ---
    datum_heute = datetime.now().strftime("%d.%m.%Y")
    
    pdf.set_font(font_name, "B", 14)
    pdf.cell(0, 8, f"Projekt: {projekt}", ln=True)
    
    pdf.set_font(font_name, "", 10)
    head_info = f"Datum: {datum_heute}"
    if bearbeiter: head_info += f"  |  Bearbeiter: {bearbeiter}"
    if firma: head_info += f"  |  Firma: {firma}"
    
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, head_info, ln=True)
    pdf.set_text_color(*text_dark)
    pdf.ln(5)

    # --- HIGHLIGHT BOX ---
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    pdf.set_y(pdf.get_y() + 5)
    pdf.set_font(font_name, "B", 12)
    pdf.cell(0, 6, "Empfohlene Heizleistung (gemäß Auslegungsparameter):", align='C', ln=True)
    pdf.set_font(font_name, "B", 24)
    pdf.set_text_color(54, 169, 225) 
    pdf.cell(0, 10, f"{total_kw:.2f} kW", align='C', ln=True)
    pdf.set_text_color(*text_dark)
    pdf.ln(8)

    # --- TABELLE ---
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, "Detaillierte Lastaufstellung:", ln=True)
    pdf.set_font(font_name, "", 10)
    
    # Zeile 1
    pdf.cell(50, 6, "Gebäudedaten:", border=0)
    pdf.cell(90, 6, f"{flaeche} m²  |  {bauweise}", border=0)
    pdf.cell(0, 6, "", ln=True)
    
    # Zeile 1b (Werte)
    pdf.cell(50, 6, "", border=0)
    pdf.cell(90, 6, f"Spezifische Last: {wm2} W/m²", border=0)
    pdf.set_font(font_name, "B", 10)
    pdf.cell(0, 6, f"{load_b:.2f} kW", align='R', ln=True)
    
    # Zeile 2
    pdf.set_font(font_name, "", 10)
    pdf.cell(140, 6, f"Zuschlag Sperrzeit/Nachtbetrieb ({sperrzeit} Std./Tag)", border=0)
    pdf.set_font(font_name, "B", 10)
    pdf.cell(0, 6, f"+ {sperr_kw:.2f} kW", align='R', ln=True)
    
    # Zeile 3
    pdf.set_font(font_name, "", 10)
    pdf.cell(140, 6, "Warmwasser-Zuschlag", border=0)
    pdf.set_font(font_name, "B", 10)
    pdf.cell(0, 6, f"+ {load_ww:.2f} kW", align='R', ln=True)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    pdf.ln(6)

    # --- DIAGRAMME EINFÜGEN ---
    chart_paths = create_charts_for_pdf(load_b, load_ww, sperr_kw, norm_temp, bivalenz, total_kw)
    y_charts = pdf.get_y()
    
    # Pie Chart (Links)
    pdf.image(chart_paths[0], x=10, y=y_charts, w=90)
    # Line Chart (Rechts)
    pdf.image(chart_paths[1], x=105, y=y_charts, w=95)
    
    pdf.set_y(y_charts + 70) 

    # --- SYSTEM DATEN ---
    pdf.set_font(font_name, "B", 11)
    pdf.cell(0, 8, "System-Parameter:", ln=True)
    pdf.set_font(font_name, "", 10)
    
    col_w = 50
    pdf.cell(col_w, 6, "Norm-Außentemperatur:", border=0)
    pdf.cell(0, 6, f"{norm_temp} Grad C", ln=True)
    pdf.cell(col_w, 6, "Max. Vorlauftemperatur:", border=0)
    pdf.cell(0, 6, f"{vl_temp} Grad C", ln=True)
    pdf.cell(col_w, 6, "Wärmeverteilung:", border=0)
    pdf.cell(0, 6, f"{system}", ln=True)
    pdf.cell(col_w, 6, "Bivalenz / Backup:", border=0)
    pdf.cell(0, 6, f"{backup_typ} ab {bivalenz} Grad C", ln=True)
    pdf.ln(5)

    # --- HINWEISE ---
    if infos or warnings or critical:
        pdf.set_font(font_name, "B", 11)
        pdf.cell(0, 8, "Hinweise & Empfehlungen:", ln=True)
        pdf.set_font(font_name, "", 9)
        
        for i in infos:
            pdf.set_text_color(0, 100, 0)
            clean = i.replace('<b>','').replace('</b>','').replace('ℹ️ ','').replace('✅ ','').replace('❄️ ','')
            pdf.multi_cell(0, 5, f"INFO: {clean}")
        for w in warnings:
            pdf.set_text_color(200, 150, 0)
            clean = w.replace('⚠️ ','')
            pdf.multi_cell(0, 5, f"WARNUNG: {clean}")
        for c in critical:
            pdf.set_text_color(200, 0, 0)
            clean = c.replace('⛔ ','').replace('<b>','').replace('</b>','').replace('🔥 ','')
            pdf.multi_cell(0, 5, f"KRITISCH: {clean}")

    for p in chart_paths:
        try: os.remove(p)
        except: pass

    return bytes(pdf.output(dest='S'))

# ==========================================
# 2. MAIN APP
# ==========================================
def main():
    BG_COLOR = "#36A9E1"
    TEXT_MAIN = "#3C3C3B"
    INPUT_BG = "#FFFFFF"
    
    st.markdown(f"""
        <style>
        @font-face {{ font-family: 'POE Vetica UI'; src: url('POE Vetica UI.ttf') format('truetype'); }}
        * {{ color: {TEXT_MAIN} !important; font-family: 'POE Vetica UI', sans-serif !important; }}
        .stApp {{ background-color: {BG_COLOR}; }}
        
        /* Padding und Margin vom H1-Titel entfernen, um exakt auf Logo-Höhe zu rutschen */
        h1.header-text {{ margin-top: 0px !important; padding-top: 0px !important; color: {TEXT_MAIN} !important; }}
        .header-text {{ color: {TEXT_MAIN} !important; }}
        
        .modul-title {{ text-align: right; font-size: 40px; font-weight: bold; color: white !important; margin-top: -100px; position: relative; z-index: 1000; }}
        
        input, .stNumberInput div[data-baseweb="input"], .stSelectbox div[data-baseweb="select"], .stTextInput div[data-baseweb="input"] {{
            background-color: {INPUT_BG} !important; color: #36A9E1 !important; -webkit-text-fill-color: #36A9E1 !important; font-weight: bold !important; border: 2px solid {TEXT_MAIN} !important; border-radius: 8px !important;
        }}
        .stSlider div[data-baseweb="slider"] {{ padding-top: 25px !important; }}
        div.stButton > button {{ background-color: #FFFFFF !important; color: {TEXT_MAIN} !important; border: 2px solid {TEXT_MAIN} !important; font-weight: bold; width: 100%; }}
        .result-box {{ background-color: rgba(255,255,255,0.95); border-radius: 10px; padding: 20px; margin-top: 20px; border-left: 10px solid {TEXT_MAIN}; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }}
        .result-highlight {{ font-size: 36px !important; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'<h1 class="header-text">WP Auslegung</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="header-text" style="font-size: 20px; margin-bottom: 0px;">Heizlast nach Gebäudestandard (Modul 1)</p>', unsafe_allow_html=True)
        # Version direkt unter Modul 1
        st.markdown(f'<p class="header-text" style="font-size: 14px; opacity: 0.8; margin-top: 0px;">App Version: {APP_VERSION}</p>', unsafe_allow_html=True)
    with col2:
        logo = "Coolsulting_Logo_ohneHG_outlines_weiß.png"
        if os.path.exists(logo):
            st.image(logo, width="stretch")
        st.markdown('<div class="modul-title">Auslegung</div>', unsafe_allow_html=True)

    st.write("---")

    c_proj, c_bearb = st.columns(2)
    with c_proj:
        projekt = st.text_input("Projekt / Kunde", placeholder="z.B.: Elke Muster", key="m1_projekt")
    with c_bearb:
        bearbeiter = st.text_input("Bearbeiter / Firma", placeholder="Ihr Name / Firmenname", key="m1_bearbeiter")
        firma = ""
        if "/" in bearbeiter:
            parts = bearbeiter.split("/")
            bearbeiter = parts[0].strip()
            firma = parts[1].strip()

    standards_dict = {
        "Unsanierter Altbau (vor 1980, Einfachverglasung)": 150,
        "Teilsanierter Altbau (Fenster neu/Doppelverglasung)": 100,
        "Standard Bestand (Bj. 1990-2000, 'Teilweise Dämmung')": 60,
        "Neubau / Gut gedämmt (nach 2010)": 50,
        "KfW Effizienzhaus / Passivhaus": 30
    }

    def update_wm2():
        sel = st.session_state.m1_std_sel
        st.session_state.m1_wm2_manual = standards_dict[sel]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🏠 1. Gebäude & Betrieb")
        flaeche = st.number_input("Beheizte Fläche (m²)", 50, 2000, 160, step=10, key="m1_area")
        
        bauweise_select = st.selectbox("Bauzustand / Dämmung", list(standards_dict.keys()), index=2, key="m1_std_sel", on_change=update_wm2)
        standard_wm2 = standards_dict[bauweise_select]
        wm2_wert = st.number_input("Spezifische Heizlast (W/m²)", 10, 300, standard_wm2, step=5, key="m1_wm2_manual")
        
        st.markdown("<br>", unsafe_allow_html=True)
        sperrzeit = st.slider("EVU Sperrzeit/Ruhezeit-Nachtbetrieb (Std./Tag)", 0, 12, 6, key="m1_sperr")
        laufzeit = 24 - sperrzeit
        st.markdown(f"<span style='font-size:13px; color:white;'>Verfügbare Laufzeit: <b>{laufzeit} Stunden/Tag</b></span>", unsafe_allow_html=True)

    with c2:
        st.markdown("### 🌡️ 2. System-Parameter")
        norm_temp = st.slider("Norm-Außentemperatur (°C)", -25, 0, -14, key="m1_normtemp")
        vl_temp = st.slider("Max. Vorlauftemperatur (°C)", 30, 80, 55, key="m1_vl")
        heizsystem = st.selectbox("Wärmeverteilung", ["Fussbodenheizung", "Radiatoren (Heizkörper)", "Mix (FBH + HK)", "Luftheizung/Lüftung"], index=1, key="m1_system")
        
        st.markdown("---")
        hat_ww = st.checkbox("Warmwasser über diese WP?", value=False, key="m1_ww")
        if hat_ww:
            personen = st.slider("Personen / Nutzer", 1, 20, 3, key="m1_pers")
            ww_faktor = (1.45 * 2.0 * 365) / 2400
        else:
            st.markdown(f"<span style='font-size:12px; color:white; opacity:0.7;'>Deaktiviert (z.B. externer Boiler)</span>", unsafe_allow_html=True)
            personen = 0
            ww_faktor = 0

    st.write("---")
    st.markdown("### ⚙️ 3. Backup & Hybrid")
    col_biv1, col_biv2 = st.columns([1, 1])
    with col_biv1:
        betriebsart = st.radio("Betriebsweise", ["Monoenergetisch (WP + Heizstab)", "Bivalent (WP + Öl/Gas-Kessel)"], key="m1_betrieb")
    with col_biv2:
        if "Monoenergetisch" in betriebsart:
            bivalenz_punkt = st.slider("Bivalenzpunkt (Heizstab ein) °C", -20, 0, -15, key="m1_biv_mono")
            backup_source = "Heizstab"
        else:
            bivalenz_punkt = st.slider("Bivalenzpunkt (Kessel hilft) °C", -10, 10, 0, key="m1_biv_bi")
            backup_source = "Kessel (Bestand)"

    st.write("---")

    if st.button("AUSLEGUNG BERECHNEN"):
        load_building_base = (flaeche * wm2_wert) / 1000
        load_ww_base = personen * ww_faktor
        sperr_faktor = 24 / laufzeit
        load_building_real = load_building_base * sperr_faktor
        total_kw = load_building_real + load_ww_base
        sperr_aufschlag = load_building_real - load_building_base
        
        infos, warnings, critical = [], [], []
        if flaeche > 300 and hat_ww: infos.append("ℹ️ <b>Gewerbe-Hinweis:</b> WW-Bedarf prüfen.")
        if vl_temp <= 55: infos.append("✅ Vorlauftemperatur optimal.")
        elif 55 < vl_temp <= 65: infos.append("ℹ️ <b>Hochtemperatur:</b> R290/R744 empfohlen.")
        elif 65 < vl_temp <= 75: infos.append("🔥 <b>Sehr hohe Temp:</b> R290/R744 zwingend.")
        else: critical.append("⛔ <b>Kritisch:</b> >75°C erfordert Sanierung.")
        if vl_temp > 50 and "Fussbodenheizung" in heizsystem: warnings.append("⚠️ >50°C bei FBH prüfen!")

        res_c1, res_c2 = st.columns([1.2, 0.8])
        with res_c1:
            st.markdown(f"""
            <div class="result-box">
                <p style="font-size:18px; margin-bottom:5px;">Benötigte Heizleistung (bei {norm_temp}°C):</p>
                <p class="result-highlight">{total_kw:.2f} kW</p>
                <hr style="border-top: 1px solid #3C3C3B; margin: 15px 0;">
                <div class="tech-info">
                <b>📋 System-Check:</b><br>
                • Auslegung: <b>{vl_temp}°C</b> Vorlauf / {heizsystem}<br>
                • Laufzeit: {laufzeit} h (Faktor {sperr_faktor:.2f})<br>
                • Bivalenz: {backup_source} ab {bivalenz_punkt}°C
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for i in infos: st.markdown(f'<div class="high-temp-box" style="color: #0C5460;">{i}</div>', unsafe_allow_html=True)
            for w in warnings: st.markdown(f'<div class="warning-box" style="color: #856404;">{w}</div>', unsafe_allow_html=True)
            for c in critical: st.markdown(f'<div class="critical-box" style="color: #721C24;">{c}</div>', unsafe_allow_html=True)

        with res_c2:
            st.markdown('<p style="color:white; text-align:center; font-weight:bold; margin-top:20px;">Leistungs-Verteilung</p>', unsafe_allow_html=True)
            labels = ['Gebäude', 'Warmwasser', 'Sperrzeit']
            values = [load_building_base, load_ww_base, sperr_aufschlag]
            colors = ['#FF4B4B', '#8B0000', '#3C3C3B']
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, sort=False)])
            fig.update_traces(marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)))
            fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, width="stretch")

        st.write("---")
        st.markdown("### 📊 Heizlast-Verlauf & Teilleistung")
        
        # Berechnung Heizgrenze (15 Grad) und Kurven
        # Kalt links (-xx°C), warm rechts (+20°C)
        x_temps = np.linspace(norm_temp - 5, 20, 100)
        heizgrenze = 15.0
        
        y_loads = [(load_building_real * (heizgrenze - t) / (heizgrenze - norm_temp)) + load_ww_base if t < heizgrenze else load_ww_base for t in x_temps]
        
        fig_biv = go.Figure()
        fig_biv.add_trace(go.Scatter(x=x_temps, y=y_loads, mode='lines', name='Heizlast Gebäude + WW', line=dict(color='#36A9E1', width=3)))
        
        if load_ww_base > 0:
            fig_biv.add_hline(y=load_ww_base, line_dash="dot", line_color="#8B0000", annotation_text=f"Warmwasser ({load_ww_base:.2f} kW)", annotation_position="bottom left")

        # Annotation für die Übergangszeit passend zur normalen Leserichtung
        fig_biv.add_vline(x=7, line_width=2, line_dash="dot", line_color="green", annotation_text="Übergang (+7°C)", annotation_position="top right")
        fig_biv.add_vline(x=bivalenz_punkt, line_width=2, line_dash="dash", line_color="red", annotation_text="Bivalenzpunkt", annotation_position="top left")
        
        fig_biv.update_layout(
            title="Leistungsbedarf über Außentemperatur",
            xaxis_title="Außentemperatur (°C)",
            yaxis_title="Leistung (kW)",
            # autorange="reversed" wurde hier ENTFERNT -> Standard Ansicht (kalt nach warm)
            paper_bgcolor='rgba(255,255,255,0.9)',
            plot_bgcolor='rgba(255,255,255,0.9)',
            height=400
        )
        st.plotly_chart(fig_biv, width="stretch")
        
        last_uebergang = (load_building_real * (heizgrenze - 7) / (heizgrenze - norm_temp)) + load_ww_base if 7 < heizgrenze else load_ww_base

        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.2); padding:10px; border-radius:5px; color:white; font-size:13px;">
        ℹ️ <b>Erklärung zum Teillast-Verhalten:</b><br>
        • Bei der Auslegungstemperatur von <b>{norm_temp}°C</b> wird die volle Leistung von <b>{total_kw:.2f} kW</b> benötigt.<br>
        • In der typischen Übergangszeit (<b>+7°C</b>, siehe <span style="color:green; font-weight:bold;">grüne Markierung</span>) benötigt das Haus inkl. Warmwasser nur noch ca. <b>{last_uebergang:.2f} kW</b>.<br>
        • Ab 15°C Außentemperatur bleibt lediglich der reine Warmwasserbedarf (<b>{load_ww_base:.2f} kW</b>) als konstante Sommer-Grundlast übrig.<br>
        • Die Wärmepumpe muss demnach weit heruntermodulieren können, um häufiges Takten zu vermeiden.<br>
        • Ab <b>{bivalenz_punkt}°C</b> springt der {backup_source} als Backup ein.
        </div>
        """, unsafe_allow_html=True)

        st.write("---")
        st.markdown("### 📄 Bericht")
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name_pdf = f"Auslegung_{projekt.replace(' ', '_')}_{date_str}.pdf"

        pdf_bytes = create_pdf_report(
            projekt if projekt else "Unbenannt",
            bearbeiter, firma,
            flaeche, bauweise_select, wm2_wert, total_kw,
            load_building_real, load_ww_base, sperr_aufschlag, sperrzeit,
            norm_temp, vl_temp, heizsystem, bivalenz_punkt, backup_source,
            infos, warnings, critical
        )
        
        st.download_button(
            label="📄 PDF Report herunterladen",
            data=pdf_bytes,
            file_name=file_name_pdf,
            mime="application/pdf"
        )

if __name__ == '__main__':
    main()