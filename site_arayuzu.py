import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import datetime
import textwrap
import io
import zipfile
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# --- KABUK TASARIM MÜDAHALESİ (CSS ENJEKSİYONU) ---
st.set_page_config(page_title="Yiğit'in Borsa Radarı", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label { font-size: 14px !important; }
    hr { margin-top: 0.5rem !important; margin-bottom: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE (HAFIZA) AYARLARI ---
if 'baslangic_degeri' not in st.session_state: st.session_state['baslangic_degeri'] = 1
if 'bitis_degeri' not in st.session_state: st.session_state['bitis_degeri'] = 50

def slider_guncelle():
    st.session_state['baslangic_degeri'] = st.session_state['aralik_slider'][0]
    st.session_state['bitis_degeri'] = st.session_state['aralik_slider'][1]

def kutu_guncelle():
    if st.session_state['baslangic_degeri'] > st.session_state['bitis_degeri']:
        st.session_state['bitis_degeri'] = st.session_state['baslangic_degeri']
    st.session_state['aralik_slider'] = (st.session_state['baslangic_degeri'], st.session_state['bitis_degeri'])

if 'aralik_slider' not in st.session_state:
    st.session_state['aralik_slider'] = (st.session_state['baslangic_degeri'], st.session_state['bitis_degeri'])


# ==============================================================================
# BÖLÜM 1: YİĞİT'İN FİNANSAL HESAPLAMA MOTORU
# ==============================================================================
bist_listesi = [
    # --- 1. KADEME: BIST 30 (1-30) ---
    "ENKAI.IS", "DSTKF.IS", "KCHOL.IS", "TUPRS.IS", "THYAO.IS", "FROTO.IS", "TCELL.IS", "TTKOM.IS", "EREGL.IS", "ASTOR.IS",
    "GUBRF.IS", "MGROS.IS", "TAVHL.IS", "PGSUS.IS", "EKGYO.IS", "PETKM.IS", "ULKER.IS", "KRDMD.IS", "AKBNK.IS", "ISCTR.IS",
    "YKBNK.IS", "SAHOL.IS", "GARAN.IS", "BIMAS.IS", "ASELS.IS", "SISE.IS", "SASA.IS", "TOASO.IS", "TRALT.IS", "AEFES.IS",

    # --- 2. KADEME: BIST 50 (Sadece BIST 30 dışındakiler) (31-50) ---
    "VAKBN.IS", "HALKB.IS", "CCOLA.IS", "BRSAN.IS", "ARCLK.IS", "TRMET.IS", "DOHOL.IS", "CIMSA.IS", "ALARK.IS", "MAVI.IS",
    "BTCIM.IS", "HEKTS.IS", "MIATK.IS", "DOAS.IS", "SOKM.IS", "OYAKC.IS", "BRISA.IS", "KONTR.IS", "KUYAS.IS", "PASEU.IS",

    # --- 3. KADEME: BIST 100 (Sadece BIST 50 dışındakiler) (51-100) ---
    "KLRHO.IS", "ENJSA.IS", "MPARK.IS", "AKSEN.IS", "KTLEV.IS", "ECILC.IS", "ISMEN.IS", "BSOKE.IS", "EFOR.IS", "AKSA.IS",
    "GENIL.IS", "GRSEL.IS", "TSKB.IS", "CWENE.IS", "DAPGM.IS", "TKFEN.IS", "EUPWR.IS", "GESAN.IS", "KCAER.IS", "EGEEN.IS",
    "FENER.IS", "GSRAY.IS", "CANTE.IS", "QUAGR.IS", "ESEN.IS", "NATEN.IS", "KARTN.IS", "SOKE.IS", "ULUUN.IS", "NETAS.IS",
    "FONET.IS", "HUNER.IS", "KFEIN.IS", "OTKAR.IS", "ALTNY.IS", "BALSU.IS", "BRYAT.IS", "AGHOL.IS", "ZOREN.IS", "ODAS.IS",
    "TUKAS.IS", "ENERY.IS", "GLRMK.IS", "ANSGR.IS", "GRTHO.IS", "MAGEN.IS", "YAYLA.IS", "FMIZP.IS", "LOGO.IS", "IZENR.IS",

    # --- 4. KADEME: BIST 500 (Geri Kalan Hisseler) (101-500+) ---
    "ISBTR.IS", "QNBTR.IS", "HEDEF.IS", "TERA.IS", "PKENT.IS", "TURSG.IS", "QNBFK.IS", "ZRGYO.IS", "AHGAZ.IS", "PEKGY.IS",
    "AYGAZ.IS", "TBORG.IS", "SELEC.IS", "TTRAK.IS", "IEYHO.IS", "KRDMB.IS", "CVKMD.IS", "AKCNS.IS", "RYSAS.IS", "SARKY.IS",
    "KRDMA.IS", "BASGZ.IS", "YGGYO.IS", "GLYHO.IS", "TRENJ.IS", "ECZYT.IS", "LYDYE.IS", "SKBNK.IS", "CMENT.IS", "TEHOL.IS",
    "MOGAN.IS", "TRHOL.IS", "POLTK.IS", "ALBRK.IS", "ARASE.IS", "AKFYE.IS", "KONYA.IS", "VERUS.IS", "SNPAM.IS", "BFREN.IS",
    "AYDEM.IS", "ASUZU.IS", "SUNTK.IS", "BANVT.IS", "LMKDC.IS", "FZLGY.IS", "SDTTR.IS", "PSGYO.IS", "KZBGY.IS", "EGPRO.IS",
    "ULUSE.IS", "ALFAS.IS", "YEOTK.IS", "ESCAR.IS", "IHAAS.IS", "KLSER.IS", "PATEK.IS", "KSTUR.IS", "AYCES.IS", "SMRTG.IS",
    "AKGRT.IS", "VESBE.IS", "A1CAP.IS", "TMSN.IS", "ICBCT.IS", "TRCAS.IS", "BINHO.IS", "AKFGY.IS", "BARMA.IS", "EUREN.IS",
    "IZMDC.IS", "GARFA.IS", "ALGYO.IS", "EBEBK.IS", "GLCVY.IS", "BMSTL.IS", "KORDS.IS", "BUCIM.IS", "VESTL.IS", "GEREL.IS",
    "OFSYM.IS", "KARSN.IS", "INGRM.IS", "VKGYO.IS", "BIGTK.IS", "EGGUB.IS", "PRKAB.IS", "NTGAZ.IS", "IZFAS.IS", "ADEL.IS",
    "ALCAR.IS", "HATSN.IS", "BOSSA.IS", "GMTAS.IS", "KOPOL.IS", "BIOEN.IS", "BOBET.IS", "MAALT.IS", "ALKA.IS", "BLUME.IS",
    "TEZOL.IS", "KAREL.IS", "AYEN.IS", "DITAS.IS", "ATAKP.IS", "ASGYO.IS", "TUREX.IS", "KGYO.IS", "GOKNR.IS", "TSPOR.IS",
    "PARSN.IS", "DOKTA.IS", "GIPTA.IS", "INTEM.IS", "CRDFA.IS", "KAPLM.IS", "KMPUR.IS", "AGROT.IS", "ARSAN.IS", "MANAS.IS",
    "YATAS.IS", "EKOS.IS", "KATMR.IS", "GOLTS.IS", "MNDTR.IS", "EGEPO.IS", "ONCSM.IS", "DESA.IS", "BORSK.IS", "HOROZ.IS",
    "KONKA.IS", "EDATA.IS", "ORGE.IS", "MERIT.IS", "SUWEN.IS", "PENTA.IS", "ADESE.IS", "PLTUR.IS", "SEGYO.IS", "MEKAG.IS",
    "BAGFS.IS", "BRKVY.IS", "BURVA.IS", "TKNSA.IS", "GSDHO.IS", "AZTEK.IS", "TSGYO.IS", "ORMA.IS", "PAPIL.IS", "TATGD.IS",
    "ERCB.IS", "YUNSA.IS", "DUNYH.IS", "KLSYN.IS", "MNDRS.IS", "BVSAN.IS", "GOODY.IS", "USAK.IS", "CEMAS.IS", "AYES.IS",
    "BRLSM.IS", "PNLSN.IS", "ATATP.IS", "BLCYT.IS", "PETUN.IS", "TURGG.IS", "LIDFA.IS", "DZGYO.IS", "GZNMI.IS", "BEGYO.IS",
    "MEDTR.IS", "KTSKR.IS", "MACKO.IS", "OSMEN.IS", "FORMT.IS", "NUGYO.IS", "KUVVA.IS", "ISSEN.IS", "SAYAS.IS", "CELHA.IS",
    "PRKME.IS", "SELVA.IS", "YYAPI.IS", "KNFRT.IS", "ARTMS.IS", "BEYAZ.IS", "RUBNS.IS", "MAKTK.IS", "BALAT.IS", "KRGYO.IS",
    "PINSU.IS", "BAKAB.IS", "LRSHO.IS", "LUKSK.IS", "BYDNR.IS", "TEKTU.IS", "ARENA.IS", "PAMEL.IS", "CONSE.IS", "VBTYZ.IS",
    "NIBAS.IS", "INTEK.IS", "ISBIR.IS", "DAGI.IS", "BIZIM.IS", "EDIP.IS", "OZSUB.IS", "BORLS.IS", "EGSER.IS", "MTRKS.IS",
    "IHLGM.IS", "RTALB.IS", "MERKO.IS", "PKART.IS", "OZRDN.IS", "VRGYO.IS", "DURDO.IS", "BMSCH.IS", "DOGUB.IS", "OSTIM.IS",
    "SUMAS.IS", "PENGD.IS", "SKTAS.IS", "KERVN.IS", "VANGD.IS", "YKSLN.IS", "OBASE.IS", "COSMO.IS", "GSDDE.IS", "ZEDUR.IS",
    "KRPLS.IS", "MARTI.IS", "MMCAS.IS", "FADE.IS", "RNPOL.IS", "SODSN.IS", "VKING.IS", "IHGZT.IS", "OYAYO.IS", "EPLAS.IS",
    "EKIZ.IS", "AVOD.IS", "BAYRK.IS", "SEKUR.IS", "IZINV.IS", "PRZMA.IS", "ICUGS.IS", "FLAP.IS", "HATEK.IS", "KRTEK.IS",
    "VKFYO.IS", "YONGA.IS", "ETILR.IS", "PSDTC.IS", "ORCAY.IS", "IHYAY.IS", "MEGAP.IS", "IHEVA.IS", "BRMEN.IS", "MZHLD.IS",
    "OYLUM.IS", "AKYHO.IS", "ERSU.IS", "RODRG.IS", "IDGYO.IS", "ATSYH.IS", "EUYO.IS", "ISDMR.IS", "DOCO.IS", "TABGD.IS",
    "ISFIN.IS", "JANTS.IS", "CLEBI.IS", "DEVA.IS", "POLHO.IS", "SANKO.IS", "CATES.IS", "REEDR.IS", "ACSEL.IS", "ADGYO.IS",
    "AFYON.IS", "AGESA.IS", "AKENR.IS", "AKSGY.IS", "ALCTL.IS", "ALKIM.IS", "ALVES.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS",
    "ARZUM.IS", "ATAGY.IS", "AVGYO.IS", "AVHOL.IS", "BIENY.IS", "BIGCH.IS", "BJKAS.IS", "BNTAS.IS", "BRKO.IS", "BRKSN.IS",
    "BURCE.IS", "CEMTS.IS", "CEOEM.IS", "CRFSA.IS", "CUSAN.IS", "DARDL.IS", "DERHL.IS", "DERIM.IS", "DESPC.IS", "DGGYO.IS",
    "DGNMO.IS", "DIRIT.IS", "DMRGD.IS", "DNISI.IS", "DOFER.IS", "DYOBY.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENSRI.IS",
    "ERBOS.IS", "ESCOM.IS", "EYGYO.IS", "FORTE.IS", "FRIGO.IS", "GENTS.IS", "GLRYH.IS", "HKTM.IS", "HLGYO.IS", "HUBVC.IS",
    "HURGZ.IS", "IHLAS.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INVEO.IS", "INVES.IS", "ISGSY.IS", "ISKUR.IS", "ISYAT.IS",
    "KENT.IS", "BESLR.IS", "KIMMR.IS", "KLGYO.IS", "KLNMA.IS", "GWIND.IS", "KRONT.IS", "KRVGD.IS", "KUTPO.IS", "ARDYZ.IS",
    "KZGYO.IS", "LIDER.IS", "LINK.IS", "LKMNH.IS", "MAKIM.IS", "MARKA.IS", "MEPET.IS", "MERCN.IS", "METRO.IS", "LYDHO.IS",
    "MOBTL.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRYO.IS", "NUHCM.IS", "BERA.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS",
    "PAGYO.IS", "PCILT.IS", "PNSUT.IS", "PRDGS.IS", "RALYH.IS", "RAYSG.IS", "RYGYO.IS", "SAMAT.IS", "SANEL.IS", "SANFM.IS",
    "SEKFK.IS", "SEYKM.IS", "SILVR.IS", "SMART.IS", "SNICA.IS", "GATEG.IS", "SONME.IS", "SRVGY.IS", "TARKM.IS", "TATEN.IS",
    "TDGYO.IS", "TGSAS.IS", "TLMAN.IS", "TMPOL.IS", "TRGYO.IS", "TRILC.IS", "TUCLK.IS", "UFUK.IS", "ULAS.IS", "ULUFA.IS",
    "UNLU.IS", "YAPRK.IS", "YBTAS.IS", "YESIL.IS", "GOZDE.IS", "NTHOL.IS", "KLKIM.IS"
]

def hisse_verileri_getir(sembol):
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period="3y", interval="1d")
        if df.empty or len(df) < 200:
            return None, None
            
        df.ta.rsi(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.mfi(length=14, append=True)
        df.ta.ema(length=200, append=True)
        
        try:
            df.ta.vwap(append=True)
            vwap_col = [col for col in df.columns if 'VWAP' in col][0]
        except:
            vwap_col = None

        try:
            info = hisse.info
            # PD/DD için Yahoo'nun kullanabileceği alternatif anahtarları sırayla deniyoruz:
            pddd = info.get('priceToBook') or info.get('trailingPriceToBook') or info.get('forwardPriceToBook') or 'Bilinmiyor'
            borc = info.get('netDebtToEbitda', 'Bilinmiyor')
        except:
            pddd, borc = 'Bilinmiyor', 'Bilinmiyor'

        temel = {'PD_DD': pddd, 'Borc_FAVOK': borc, 'VWAP_Col': vwap_col, 'mevsimsel_pozitif': False}
        return df, temel
    except:
        return None, None

def uyum_hesapla(deger, hedef, esik, yon="dusuk"):
    if deger is None or (isinstance(deger, str) and deger == 'Bilinmiyor'): return 0.0
    try: deger = float(deger)
    except: return 0.0

    if yon == "dusuk":
        if deger <= hedef: return 100.0
        if deger >= esik: return 0.0
        return 50.0 + ((esik - deger) / (esik - hedef)) * 50.0
    else:
        if deger >= hedef: return 100.0
        if deger <= esik: return 0.0
        return 50.0 + ((deger - esik) / (hedef - esik)) * 50.0

def senaryo_yuzde_tespit(df, temel, secilen_senaryo):
    son = df.iloc[-1]
    rsi = son.get('RSI_14', 50); mfi = son.get('MFI_14', 50); adx = son.get('ADX_14', 0)
    pddd = temel.get('PD_DD', 99); kapanis = son['Close']; ema200 = son.get('EMA_200', kapanis)
    ema_fark = abs(kapanis - ema200) / ema200

    uyum1 = uyum2 = 0; baslik = ""

    if secilen_senaryo == 'a': 
        uyum1 = uyum_hesapla(rsi, hedef=20, esik=32, yon="dusuk")
        uyum2 = uyum_hesapla(mfi, hedef=15, esik=28, yon="dusuk")
        baslik = "Yay Gevşemesi (Tepki Alımı)"
    elif secilen_senaryo == 'b': 
        uyum1 = uyum_hesapla(rsi, hedef=65, esik=52, yon="yuksek")
        uyum2 = uyum_hesapla(adx, hedef=35, esik=22, yon="yuksek")
        baslik = "Roket Kalkışı (Momentum)"
    elif secilen_senaryo == 'c': 
        uyum1 = uyum_hesapla(rsi, hedef=85, esik=70, yon="yuksek")
        uyum2 = uyum_hesapla(mfi, hedef=80, esik=65, yon="yuksek")
        baslik = "Yorgunluk Sinyali (Zirve)"
    elif secilen_senaryo == 'd': 
        uyum1 = uyum_hesapla(pddd, hedef=0.7, esik=1.5, yon="dusuk")
        uyum2 = uyum_hesapla(adx, hedef=40, esik=25, yon="yuksek")
        baslik = "Ucuzluk Tuzağı (Trap)"
    elif secilen_senaryo == 'e': 
        uyum1 = uyum_hesapla(pddd, hedef=1.0, esik=2.0, yon="dusuk")
        uyum2 = uyum_hesapla(ema_fark, hedef=0.01, esik=0.05, yon="dusuk")
        baslik = "Güvenli Liman (Value)"

    if uyum1 < 50 or uyum2 < 50: return 0.0, baslik
    return (uyum1 + uyum2) / 2.0, baslik

def pdf_bellege_uret(df, sembol, temel, son, puan, ema_etiket, vwap_deger, rsi_val, mfi_val, adx_val, pddd, senaryo_adi, senaryo_metni, tepki_potansiyeli=0):
    pdf_buffer = io.BytesIO()
    pdf = PdfPages(pdf_buffer)
    
    df_3m = df.tail(63)
    df_1y = df.tail(252)
    df_3y = df

    # --- SAYFA 1: TEKNİK KİMLİK VE KISA VADE ---
    fig1 = plt.figure(figsize=(15, 12))
    gs1 = gridspec.GridSpec(3, 1, height_ratios=[1.5, 3, 1], hspace=0.4)
    fig1.suptitle(f"{sembol} - TEKNİK ANALİZ RAPORU", fontsize=20, fontweight='bold', color='navy')

    ax_metin = plt.subplot(gs1[0])
    ax_metin.axis('off')
    
    # --- YENİ DÜZENLİ VE ŞIK TABLO GÖRÜNÜMÜ ---
    # Arka plan kutusu
    box = plt.Rectangle((0.02, 0.0), 0.96, 1.0, fill=True, color="#f8f9fa", ec="gray", lw=1.5, transform=ax_metin.transAxes, zorder=0)
    ax_metin.add_patch(box)

    # 1. Başlık Satırı
    ax_metin.text(0.05, 0.88, "TARAMA TÜRÜ / PUAN:", fontweight='bold', color='navy', fontsize=12, transform=ax_metin.transAxes)
    mod_metin = f"{puan:.1f} / 100.0" if puan > 0 else "Senaryo Algoritması (Kriter Eşleşmesi)"
    ax_metin.text(0.25, 0.88, mod_metin, fontsize=12, transform=ax_metin.transAxes)

    # Değerleri Yuvarlama ve Formatlama
    if isinstance(vwap_deger, float) or (isinstance(vwap_deger, str) and vwap_deger.replace('.','',1).isdigit()):
        v_str = f"{float(vwap_deger):.2f} TL"
    else:
        v_str = str(vwap_deger)

    try: pddd_str = f"{float(pddd):.2f}"
    except: pddd_str = str(pddd)

    # Kolon X Koordinatları (Tablo Hizalaması)
    c1_k = 0.05; c1_v = 0.15
    c2_k = 0.35; c2_v = 0.40
    c3_k = 0.65; c3_v = 0.76

    # 2. Satır
    y1 = 0.70
    ax_metin.text(c1_k, y1, "KAPANIŞ:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c1_v, y1, f"{son['Close']:.2f} TL", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_k, y1, "RSI:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_v, y1, f"{rsi_val:.1f}", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_k, y1, "PD/DD:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_v, y1, pddd_str, fontsize=11, transform=ax_metin.transAxes)

    # 3. Satır
    y2 = 0.52
    ax_metin.text(c1_k, y2, "EMA(200):", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c1_v, y2, f"{son.get('EMA_200', 0):.2f} TL", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_k, y2, "MFI:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_v, y2, f"{mfi_val:.1f}", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_k, y2, "BORÇ/FAVÖK:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_v, y2, str(temel.get('Borc_FAVOK', 'Bilinmiyor')), fontsize=11, transform=ax_metin.transAxes)

    # 4. Satır
    y3 = 0.34
    ax_metin.text(c1_k, y3, "VWAP:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c1_v, y3, v_str, fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_k, y3, "ADX:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_v, y3, f"{adx_val:.1f}", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_k, y3, "TREND YÖNÜ:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    t_color = 'darkgreen' if 'POZİTİF' in ema_etiket else 'darkred'
    ax_metin.text(c3_v, y3, ema_etiket, fontweight='bold', color=t_color, fontsize=11, transform=ax_metin.transAxes)

    # 5. Satır (Senaryo ve Özel Bildirimler)
    y4 = 0.16
    ekstra = []
    if senaryo_adi: ekstra.append(f"[>>] SENARYO: {senaryo_adi}")
    if senaryo_metni: ekstra.append(f"-> {senaryo_metni}")
    if temel.get('mevsimsel_pozitif'): ekstra.append("[+] MEVSİMSELLİK: Hisse tarihsel olarak bu dönemlerde yükseliş eğiliminde.")
    if tepki_potansiyeli > 0: ekstra.append("[!] TEPKİ POTANSİYELİ: Hisse teknik olarak aşırı gerilmiş. Sıçrama olası.")
    
    if ekstra:
        wrapped = textwrap.fill("  |  ".join(ekstra), width=125)
        ax_metin.text(0.05, y4, wrapped, color='darkred', fontweight='bold', fontsize=10, transform=ax_metin.transAxes, verticalalignment='top')
    # --- DÜZENLEME SONU ---

    ax1 = plt.subplot(gs1[1])
    ax1.set_title("3 Aylık Grafik (Kısa Vade)", fontsize=14, pad=10)
    ax1.plot(df_3m.index, df_3m['Close'], color='#1f77b4', linewidth=2, label='Günlük Kapanış Fiyatı')
    if 'EMA_200' in df_3m.columns:
        ax1.plot(df_3m.index, df_3m['EMA_200'], color='#ff7f0e', linestyle='--', linewidth=1.5, label='EMA 200 (Ana Trend)')
    ax1.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
    ax1.grid(True, which='both', linestyle='--', alpha=0.4)
    ax1.set_ylabel("Fiyat (TL)", fontweight='bold')

    ax2 = plt.subplot(gs1[2], sharex=ax1)
    ax2.bar(df_3m.index, df_3m['Volume'], color='#7f7f7f', alpha=0.7, label='İşlem Hacmi')
    ax2.legend(loc='upper left', frameon=True, fontsize=9)
    ax2.set_ylabel("Hacim", fontweight='bold')
    
    pdf.savefig(fig1, bbox_inches='tight')

    # --- SAYFA 2: ORTA VE UZUN VADE ---
    fig2 = plt.figure(figsize=(15, 12))
    gs2 = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 3, 1], hspace=0.45)
    fig2.suptitle(f"{sembol} - ORTA VE UZUN VADE PERSPEKTİFİ", fontsize=18, fontweight='bold', color='darkred')

    ax3 = plt.subplot(gs2[0])
    ax3.set_title("1 Yıllık Grafik (Orta Vade)", fontsize=14, pad=10)
    ax3.plot(df_1y.index, df_1y['Close'], color='#2ca02c', linewidth=2, label='Günlük Kapanış Fiyatı')
    if 'EMA_200' in df_1y.columns:
        ax3.plot(df_1y.index, df_1y['EMA_200'], color='#ff7f0e', linestyle='--', linewidth=1.5, label='EMA 200')
    ax3.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.4)
    ax3.set_ylabel("Fiyat (TL)", fontweight='bold')

    ax4 = plt.subplot(gs2[1], sharex=ax3)
    ax4.bar(df_1y.index, df_1y['Volume'], color='#7f7f7f', alpha=0.7, label='İşlem Hacmi')
    ax4.legend(loc='upper left', frameon=True, fontsize=9)
    ax4.set_ylabel("Hacim", fontweight='bold')

    ax5 = plt.subplot(gs2[2])
    ax5.set_title("3 Yıllık Grafik (Uzun Vade)", fontsize=14, pad=10)
    ax5.plot(df_3y.index, df_3y['Close'], color='#9467bd', linewidth=2, label='Günlük Kapanış Fiyatı')
    if 'EMA_200' in df_3y.columns:
        ax5.plot(df_3y.index, df_3y['EMA_200'], color='#ff7f0e', linestyle='--', linewidth=1.8, label='EMA 200')
    ax5.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
    ax5.grid(True, linestyle='--', alpha=0.4)
    ax5.set_ylabel("Fiyat (TL)", fontweight='bold')

    ax6 = plt.subplot(gs2[3], sharex=ax5)
    ax6.bar(df_3y.index, df_3y['Volume'], color='#7f7f7f', alpha=0.7, label='İşlem Hacmi')
    ax6.legend(loc='upper left', frameon=True, fontsize=9)
    ax6.set_ylabel("Hacim", fontweight='bold')

    pdf.savefig(fig2, bbox_inches='tight')
    
    pdf.close()
    plt.close('all')
    return pdf_buffer.getvalue()

# ==============================================================================
# BÖLÜM 2: YAN MENÜ (KUMANDA PANELİ)
# ==============================================================================
st.sidebar.title("⚙️ Kumanda Paneli")
mod_secimi = st.sidebar.radio("Tarama Modu", ["Çoklu Hisse Tarama", "Tekli Hisse Tarama"])

tekli_sembol = ""
if mod_secimi == "Çoklu Hisse Tarama":
    toplam_sayi = len(bist_listesi)
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📏 Arama Aralığı (1-{toplam_sayi})")
    
    st.sidebar.markdown("<div style='color: #666; font-size: 13px; margin-bottom: 10px; line-height: 1.4;'>ℹ️ Çoklu tarama sadece Borsa İstanbul'da geçerlidir. Sisteme kayıtlı 500+ hisse arasından taramak istediğiniz aralığı aşağıdaki çubuktan veya kutucuklardan belirleyebilirsiniz.</div>", unsafe_allow_html=True)
    
    st.sidebar.slider("Kaydırma Çubuğu", min_value=1, max_value=toplam_sayi, key='aralik_slider', on_change=slider_guncelle)
    # Mobilde sıkışmayı önlemek için sütunları kaldırdık, alt alta koyduk
    baslangic = st.sidebar.number_input("Başlangıç Hisse No:", min_value=1, max_value=toplam_sayi, key='baslangic_degeri', on_change=kutu_guncelle)
    bitis = st.sidebar.number_input("Bitiş Hisse No:", min_value=1, max_value=toplam_sayi, key='bitis_degeri', on_change=kutu_guncelle)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Strateji Seçimi")
    strateji = st.sidebar.selectbox("Yöntem:", ["Lütfen Seçiniz...", "Senaryo Algoritması", "Risk Profili", "Manuel Kriterler"])
    
    alt_secim = None
    rsi_sinir = mfi_sinir = pddd_sinir = adx_sinir = 0
    if strateji == "Senaryo Algoritması":
        alt_secim = st.sidebar.selectbox("📌 Alt Kategori:", ["a. Yay Gevşemesi", "b. Roket Kalkışı", "c. Yorgunluk Sinyali", "d. Ucuzluk Tuzağı", "e. Güvenli Liman"])
    elif strateji == "Risk Profili":
        alt_secim = st.sidebar.slider("Risk İştahınız (0: Güvenli, 100: Agresif)", 0, 100, 50)
    elif strateji == "Manuel Kriterler":
        st.sidebar.info("👉 Sağ taraftan tavsiye edilen Filtre Stratejilerini görebilirsiniz.")
        st.sidebar.markdown("**Manuel Sınırlar**")
        rsi_sinir = st.sidebar.number_input("RSI Sınırı (Altında)", value=45.0)
        mfi_sinir = st.sidebar.number_input("MFI Sınırı (Altında)", value=45.0)
        pddd_sinir = st.sidebar.number_input("PD/DD Sınırı (Altında)", value=2.0)
        adx_sinir = st.sidebar.number_input("ADX Sınırı (Üstünde)", value=20.0)

elif mod_secimi == "Tekli Hisse Tarama":
    tekli_sembol = st.sidebar.text_input("Hisse Kodu Girin (Örn: THYAO.IS):", value="THYAO.IS").upper()
    
    st.sidebar.markdown("""
    <div style='color: #666; font-size: 13px; margin-top: -10px; margin-bottom: 10px; line-height: 1.4;'>
    <b>⚠️⚠️İşlem gören her bir hissenin işlem gördüğü borsaya göre bir uzantısı vardır. Aratmalarınız sonuç bulması için bu uzantıları lütfen ekleyiniz. </b><br>
    <b>Hisse Kodu Uzantıları:</b><br>
    • <b>Türkiye (BİST):</b> <code>.IS</code> (Örn: THYAO.IS)<br>
    • <b>ABD Borsaları:</b> Uzantı yok (Örn: AAPL, TSLA)<br>
    • <b>Almanya (XETRA):</b> <code>.DE</code> (Örn: VOW3.DE)<br>
    • <b>İngiltere (Londra):</b> <code>.L</code> (Örn: BP.L)<br>
    • <b>Çin (Shanghai):</b> <code>.SS</code> (Örn: 600519.SS)<br>
    • <b>Hong Kong:</b> <code>.HK</code> (Örn: 0700.HK)
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
buton_sutun1, buton_sutun2 = st.sidebar.columns(2)
baslat = buton_sutun1.button("▶️ BAŞLAT", use_container_width=True)
durdur = buton_sutun2.button("🛑 DURDUR", use_container_width=True)

if durdur:
    # 1. Hafızadaki tüm eski tarama verilerini sil
    if 'eslesenler_hafiza' in st.session_state:
        del st.session_state['eslesenler_hafiza']
    if 'bronz_hafiza' in st.session_state:
        del st.session_state['bronz_hafiza']
    if 'hatali_hafiza' in st.session_state:
        del st.session_state['hatali_hafiza']
        
    # 2. Ekrana geçici olarak uyarıyı bas
    uyari_kutusu = st.empty()
    uyari_kutusu.warning("🛑 İşlem durduruldu. Hafıza temizlendi, ana ekrana dönülüyor...")
    
    # 3. İki saniye bekletip sayfayı otomatik yenile (Ana ekrana atar)
    import time
    time.sleep(2)
    st.rerun()

# --- SİTE KÜNYESİ VE HAKLAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <p><b>Yiğit'in Borsa Radarı</b><br>
    © 2026 Tüm Hakları Saklıdır.</p>
    <p>👨‍💻 Geliştirici: <b>Yiğit Efe Devecioğlu</b><br>
    ✉️ İletişim: <i>deveciogluyigitefe@gmail.com</i></p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# BÖLÜM 3: ANA EKRAN VE TARAMA MOTORU
# ==============================================================================

st.title("🚀 Yiğit'in Borsa Radarı")

# Hafızada daha önceden yapılmış bir tarama var mı kontrolü
arama_gecmisi_var = 'eslesenler_hafiza' in st.session_state

# Sadece Başlat'a basılmadıysa VE hafızada sonuç yoksa rehberi göster!
if not baslat and not arama_gecmisi_var:
    
    st.info("👋 **Hoş Geldiniz**  \nBu site tamamen amatör ruhla ve bireysel çabayla geliştirilmiştir. Amacım, finansal piyasalara yeni giren veya verileri daha hızlı taramak isteyen kişilere yardımcı olacak ekonomik ve istatistiksel tabanlı bir araç sunmaktır. Kesinlikle **yatırım tavsiye içermez**, arkasındaki algoritma tamamen geçmiş verilere dayalı istatistiki ve ekonomik tabanlıdır.  \nBir hata, öneri veya şikayetiniz olursa sol menüdeki e-posta adresim üzerinden benimle iletişime geçebilirsiniz.")
    st.markdown("<p style='font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>⚠️Yasal yükümlülükler gereği 'Yasal Uyarı ve Çekince Metni'miz sitenin en altında bulunmaktadır.\n\n<a href='#yasal-uyari-hedefi' target='_self'><b>Buraya tıklayarak</b></a> metne ulaşabilirsiniz. Lütfen siteyi kullanmadan önce okuyunuz⚠️</p> \n\n👈Sol menüden tercihlerinizi belirleyip hisse(leri) taramaya başlatabilirsiniz.", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 📚 Başucu Rehberi")
    
    col1, col2 = st.columns(2)
        
    # 🧠 Akıllı Kutu Mantığı: Manuel seçilirse sadece Tavsiyeler açık kalır, diğerleri kapanır.
    manuel_mod_aktif = (mod_secimi == "Çoklu Hisse Tarama" and strateji == "Manuel Kriterler")
    diger_kutular_acik = not manuel_mod_aktif

    with col1:
        with st.expander("📈 İndikatörler ve Temel Metrikler", expanded=diger_kutular_acik):
            st.markdown("""
            - **RSI (Göreceli Güç Endeksi):** 0-100 arası hız ölçer. 30 altı aşırı satım (tepki gelebilir), 70 üstü aşırı alımdır (düzeltme gelebilir).
            - **MFI (Para Akışı Endeksi):** RSI'ın hacimli versiyonudur. Fiyat artarken MFI artmıyorsa asıl para çıkıyordur. 20 altı aşırı satım, 80 üstü aşırı alımdır.
            - **ADX (Ortalama Yönsel Endeks):** Trendin gücünü ölçer. 25 üstü güçlü trend, 20 altı yatay/testere piyasasıdır.
            - **VWAP (Ağırlıklı Ortalama):** Gün içi adil fiyattır. Fiyat VWAP üstündeyse alıcılar baskındır.
            - **PD/DD:** Şirketin defter değerine göre pahalılığını gösterir. 1-2 makul, 5+ genelde pahalıdır.
            - **EMA 200:** Uzun vadeli ana trend yönüdür. Fiyat üstündeyse hisse sağlıklıdır.
            - **Net Borç / FAVÖK:** Borç ödeme kapasitesidir. 3'ün altı güvenli kabul edilir.
            """)
            
        with st.expander("📊 Grafikler ve Formasyonlar (Görsel Rehber)", expanded=diger_kutular_acik):
            st.markdown("**1. Boğa Piyasası [Bull Market]:**  \n Fiyatların merdiven çıkar gibi sürekli yeni zirveler yaptığı, alıcıların iştahlı olduğu bereketli dönem. \"Malda kalma\" zamanıdır.")
            st.markdown("---")

            st.markdown("**2. Ayı Piyasası [Bear Market]:**  \n Fiyatların asansörle iner gibi sürekli yeni dipler yaptığı, korkunun hakim olduğu dönem. Nakitte bekleme veya açığa satış zamanıdır.")
            st.markdown("---")

            st.markdown("**3. İkili Tepe / M Formasyonu [Double Top]:**  \n Fiyatın aynı tavanı iki kez yoklayıp kıramamasıdır. \"Buradan ötesi yok, malı boşaltıyorlar\" diyen güçlü bir düşüş sinyalidir.")
            try: st.image("Görseller/ikili_tepe.jpg")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'ikili_tepe.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**4. İkili Dip / W Formasyonu [Double Bottom]:**  \n Fiyatın aynı tabandan iki kez destek bulup sekmesidir. \"Dibi gördük, artık yön yukarı\" diyen güçlü bir yükseliş sinyalidir.")
            try: st.image("Görseller/ikili_dip.jpg")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'ikili_dip.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**5. Omuz Baş Omuz (OBO) Formasyonu [Head and Shoulders]:**  \n Ortada büyük bir zirve (baş), yanlarda daha küçük iki zirve (omuzlar). Yükseliş partisinin bittiğini gösterir, boyun çizgisi aşağı kırılırsa kaçılır.")
            try: st.image("Görseller/obo.jpg")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'obo.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**6. Ters OBO Formasyonu [Inverse Head and Shoulders]:**  \n OBO'nun tepetaklak halidir. Ortada derin bir kuyu, yanlarda sığ iki kuyu. Düşüşün bittiğini ve sağlam bir yükseliş trendinin başlayacağını müjdeler.")
            try: st.image("Görseller/tobo.jpg")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'tobo.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**7. Kulplu Fincan Formasyonu [Cup and Handle]:**  \n Fiyat önce büyük bir çanak (fincan) çizer, sonra küçük bir düzeltme (kulp) yapar. Kulp yukarı kırıldığında, hisse fincanın derinliği kadar yukarı fırlamaya hazırlanır.")
            try: st.image("Görseller/fincan_kulp.jpg")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'fincan_kulp.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**8. Takoz Formasyonu [Wedge Pattern]:**  \n Fiyatın gittikçe daralan bir huniye sıkışmasıdır. Yükselen takoz (Ayı) genelde aşağı doğru patlar, düşen takoz (Boğa) ise yay gibi gerilip yukarı doğru patlar.")
            try: st.image("Görseller/takoz.png")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'takoz.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**9. Bayrak Formasyonu [Flag Pattern]:**  \n Sert bir hareket sonrası dikdörtgen şeklinde kısa bir mola. Direk yukarıysa (Boğa Bayrağı) moladan sonra yükseliş devam eder, direk aşağıysa (Ayı Bayrağı) düşüş devam eder.")
            try: st.image("Görseller/bayrak.png")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'bayrak.jpg' ekleyin]")
            st.markdown("---")

            st.markdown("**10. Flama Formasyonu [Pennant Pattern]:**  \n Bayrağın dikdörtgen değil, küçük bir simetrik üçgen halidir. Mantık aynıdır: Sert hareket (direk) -> kısa üçgen mola -> aynı yönde sert kopuş.")
            try: st.image("Görseller/flama.png")
            except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'flama.jpg' ekleyin]")

    with col2:
        with st.expander("🎯 Senaryo Sözlüğü", expanded=diger_kutular_acik):
            st.markdown("""
            - **Yay Gevşemesi:** Hisse o kadar çok satıldı ki satacak kimse kalmadı. 'Bedava' diyen alıcılar gelirse yay gibi fırlayabilir.
            - **Roket Kalkışı:** Hisse rüzgarı arkasına aldı. Güçlü şekilde yükseliyor, trene binmek için son çağrı olabilir.
            - **Yorgunluk Sinyali:** Zirveye çıktı ama nefesi kesiliyor. Fiyat yükselse de para çıkışı var, iniş başlayabilir.
            - **Ucuzluk Tuzağı:** Şirket kağıt üzerinde ucuz ama düşüş henüz bitmemiş olabilir. *Düşen bıçak tutulmaz.*
            - **Güvenli Liman:** Fırtınalı havada sığınılacak yer. Hızlı kazandırmaz ama kolay kolay da kaybettirmez.
            """)
            
        with st.expander("💡 Tavsiye Edilen Filtre Stratejileri", expanded=manuel_mod_aktif):
            st.markdown(
                "**1. Dip Avcısı (Yüksek Risk):**<br>"
                "Panikle satılan ucuz hisseler.<br>"
                "*(RSI: <35 | MFI: <30 | PD/DD: <2 | ADX: >25)*<br><br>"
                "**2. Dengeli Trend (Orta Risk):**<br>"
                "Arkasına güçlü trend almış istikrarlı hisseler.<br>"
                "*(RSI: <55 | MFI: <50 | PD/DD: <4 | ADX: >20)*<br><br>"
                "**3. Değer Yatırımcısı (Düşük Risk):**<br>"
                "Teknik coşkudan ziyade ucuzluğa odaklanır.<br>"
                "*(RSI: <45 | MFI: <45 | PD/DD: <1.5 | ADX: >15)*",
                unsafe_allow_html=True
            )

else:
    # --- YUKARI KAYDIRMA VE HAFIZA KONTROLÜ ---
    # Başlat tuşuna basıldığında ekranı hemen en tepeye fırlat
    if baslat:
        st.components.v1.html(
            """
            <script>
                setTimeout(function() {
                    window.parent.document.querySelector('.main').scrollTo({top: 0, behavior: 'smooth'});
                }, 100);
            </script>
            """,
            height=0
        )
    
    # EĞER YENİ BİR TARAMA İSTENİYORSA (Sadece butona basıldıysa burası çalışır)
    if baslat:
        taranacak_liste = bist_listesi[baslangic-1:bitis] if mod_secimi == "Çoklu Hisse Tarama" else [tekli_sembol]
        toplam_hisse = len(taranacak_liste)
        
        ilerleme_cubugu = st.progress(0.0)
        durum_metni = st.empty()
        gecici_eslesenler = []
        gecici_bronz_liste = []

        import time # Çubuğun mobilde donmasını engellemek için
        
        for i, sembol in enumerate(taranacak_liste):
            durum_metni.text(f"⏳ [{i+1}/{toplam_hisse}] Taranıyor: {sembol} ...")
            ilerleme_cubugu.progress((i + 1) / toplam_hisse)
            time.sleep(0.01) # Arayüze nefes aldırır
            
            df, temel = hisse_verileri_getir(sembol)
            if df is None: continue
            
            uyum_puani = 0
            senaryo_adi = ""
            
            if mod_secimi == "Çoklu Hisse Tarama":
                if strateji == "Senaryo Algoritması" and alt_secim:
                    harf = alt_secim.split(".")[0]
                    uyum_puani, senaryo_adi = senaryo_yuzde_tespit(df, temel, harf)
                
                elif strateji == "Risk Profili" and alt_secim is not None:
                    son = df.iloc[-1]
                    rsi_val = son.get('RSI_14', 50); mfi_val = son.get('MFI_14', 50); adx_val = son.get('ADX_14', 0); pddd = temel.get('PD_DD', 10)
                    risk = alt_secim
                    if risk < 25: rsi_w, mfi_w, adx_w, pddd_w = 0.10, 0.10, 0.10, 0.70; rsi_tip = "normal"; senaryo_adi = "Güvenli Liman"
                    elif risk < 50: rsi_w, mfi_w, adx_w, pddd_w = 0.30, 0.25, 0.15, 0.30; rsi_tip = "normal"; senaryo_adi = "Dengeli Trend Modu"
                    elif risk < 75: rsi_w, mfi_w, adx_w, pddd_w = 0.40, 0.10, 0.40, 0.10; rsi_tip = "yuksek"; senaryo_adi = "Momentum"
                    else: rsi_w, mfi_w, adx_w, pddd_w = 0.45, 0.45, 0.05, 0.05; rsi_tip = "dip"; senaryo_adi = "Agresif (Dip Avcısı)"
                    
                    if rsi_tip == "dip": r_p = 10 if rsi_val < 25 else (7 if rsi_val < 35 else 0)
                    elif rsi_tip == "yuksek": r_p = 10 if rsi_val > 55 else (5 if rsi_val > 50 else 0)
                    else: r_p = 10 if rsi_val < 45 else (5 if rsi_val < 55 else 0)
                    
                    m_p = 10 if mfi_val < 30 else (5 if mfi_val < 45 else 0)
                    a_p = 10 if adx_val > 25 else (5 if adx_val > 20 else 0)
                    p_p = 10 if (isinstance(pddd, (int, float)) and pddd < 1.5) else (5 if (isinstance(pddd, (int, float)) and pddd < 3) else 0)
                    
                    puan = (r_p * rsi_w) + (m_p * mfi_w) + (a_p * adx_w) + (p_p * pddd_w)
                    if temel.get('mevsimsel_pozitif'): puan += 1
                    uyum_puani = (puan / 11.0) * 100 
                    senaryo_adi = f"{senaryo_adi} (Puan: {puan:.1f}/11)"

                elif strateji == "Manuel Kriterler":
                    son = df.iloc[-1]
                    rsi_val = son.get('RSI_14', 50); mfi_val = son.get('MFI_14', 50); adx_val = son.get('ADX_14', 0); pddd = temel.get('PD_DD', 10)
                    puan = 0
                    if rsi_val < rsi_sinir: puan += 1
                    if mfi_val < mfi_sinir: puan += 2
                    if adx_val > adx_sinir: puan += 1
                    if isinstance(pddd, (int, float)) and pddd < pddd_sinir: puan += 2
                    if temel.get('mevsimsel_pozitif'): puan += 1
                    uyum_puani = (puan / 7.0) * 100 
                    senaryo_adi = f"Manuel Kriter Eşleşmesi (Puan: {puan}/7)"
            else:
                uyum_puani = 100
                senaryo_adi = "Tekli İnceleme"

            if uyum_puani >= 75:
                son = df.iloc[-1]
                kapanis = son['Close']
                ema200 = son.get('EMA_200', kapanis)
                ema_etiket = "POZİTİF (Fiyat > EMA200)" if kapanis > ema200 else "NEGATİF (Fiyat < EMA200)"
                
                # VWAP Değerini yakalama düzeltmesi
                vwap_sutun = temel.get('VWAP_Col')
                vwap_degeri = son.get(vwap_sutun, 'Bilinmiyor') if vwap_sutun else 'Bilinmiyor'
                
                pdf_bytes = pdf_bellege_uret(
                    df, sembol, temel, son, uyum_puani, ema_etiket, 
                    vwap_degeri, son.get('RSI_14', 50), 
                    son.get('MFI_14', 50), son.get('ADX_14', 0), 
                    temel.get('PD_DD', 'Bilinmiyor'), senaryo_adi, ""
                )
                gecici_eslesenler.append({"sembol": sembol, "uyum": uyum_puani, "pdf": pdf_bytes})

            elif mod_secimi == "Çoklu Hisse Tarama" and strateji == "Senaryo Algoritması" and uyum_puani >= 50:
                gecici_bronz_liste.append({"sembol": sembol, "uyum": uyum_puani})

        # Tarama bitti, sonuçları HAFIZAYA kaydet (İndirme butonuna basınca silinmesin diye)
        st.session_state['eslesenler_hafiza'] = gecici_eslesenler
        st.session_state['bronz_hafiza'] = gecici_bronz_liste
        durum_metni.empty()
        ilerleme_cubugu.empty()

    # --- EKRANA YAZDIRMA BÖLÜMÜ (HAFIZADAN OKUR) ---
    eslesenler = st.session_state.get('eslesenler_hafiza', [])
    bronz_liste = st.session_state.get('bronz_hafiza', [])

    # Eğer hafızada tarama sonucu varsa ekrana bas (Butona basılmasa da hep ekranda kalır)
    if 'eslesenler_hafiza' in st.session_state:
        if len(eslesenler) == 0:
            st.warning("⚠️ Seçtiğiniz kriterlere uygun hisse bulunamadı. Kriterleri esnetmeyi deneyin.")
        else:
            st.success(f"🎉 Tarama Tamamlandı! {len(eslesenler)} adet eşleşme bulundu.")

            if st.button("🏠 Ana Ekrana Dön", use_container_width=True):
                if 'eslesenler_hafiza' in st.session_state: del st.session_state['eslesenler_hafiza']
                if 'bronz_hafiza' in st.session_state: del st.session_state['bronz_hafiza']
                if 'hatali_hafiza' in st.session_state: del st.session_state['hatali_hafiza']
                st.rerun()
            
            if len(eslesenler) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for hisse in eslesenler:
                        zip_file.writestr(f"{hisse['sembol']}_Analiz.pdf", hisse['pdf'])
                
                st.download_button(
                    label="📦 TÜM RAPORLARI ZIP OLARAK İNDİR",
                    data=zip_buffer.getvalue(),
                    file_name="Borsa_Raporlari.zip",
                    mime="application/zip",
                    type="primary"
                )
                st.markdown("---")

            for hisse in eslesenler:
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    st.markdown(f"**🟢 {hisse['sembol']}**")
                with col2:
                    st.markdown(f"Uyum: **%{hisse['uyum']:.1f}**")
                with col3:
                    st.download_button(
                        label="📄 Raporu İndir",
                        data=hisse['pdf'],
                        file_name=f"{hisse['sembol']}_Rapor.pdf",
                        mime="application/pdf",
                        key=hisse['sembol']
                    )
                st.markdown("---")
                
            if len(bronz_liste) > 0:
                with st.expander("🔍 Kısmi Uyum Sağlayan Diğer Hisseler (%50 - %74)"):
                    st.info("Bu hisseler senaryoya yaklaşmış ancak henüz tam olgunlaşmamıştır.")
                    bronz_liste.sort(key=lambda x: x['uyum'], reverse=True)
                    for br in bronz_liste:
                        st.markdown(f"- **{br['sembol']}** (Uyum: %{br['uyum']:.1f})")
# --- SAYFA ALTI (FOOTER) YASAL UYARI METNİ ---
st.markdown("---")
st.markdown("""
<div id='yasal-uyari-hedefi' style='text-align: justify; color: gray; font-size: 11px; padding: 10px;'>
    <b>⚖️ Yasal Uyarı ve Çekince Metni:</b><br><br>
    - Burada yer alan yatırım bilgi, yorum ve algoritmik sonuçları <b>kesinlikle yatırım danışmanlığı kapsamında değildir</b>.<br>
    - Sistemdeki algoritmalar tamamen geçmiş verilere ve matematiksel indikatörlere dayanmaktadır. Geçmiş fiyat hareketleri, gelecekteki hareketleri garanti etmez. Hiçbir veri veya senaryo eşleşmesi <b>Al, Sat veya Tut tavsiyesi içermez.</b><br>
    - Veriler 3. parti sağlayıcılardan (Yahoo Finance vb.) çekilmekte olup <b>genellikle 15 dakika gecikmeli</b> olarak yansıyabilmektedir. Olası veri hatalarından, gecikmelerden, kesintilerden veya bu araca dayanarak alacağınız finansal kararlardan doğabilecek maddi/manevi zararlardan geliştirici (Yiğit Efe Devecioğlu) hiçbir şekilde sorumlu tutulamaz. Lütfen yatırımlarınızı kendi risk profilinize ve araştırmalarınıza göre yapınız.
</div>

""", unsafe_allow_html=True)

















