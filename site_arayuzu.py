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
import time
import altair as alt
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    "GUBRF.IS", "MGROS.IS", "TAVHL.IS", "PGSUS.IS", "EKGYO.IS", "PETKM.IS", "KRDMD.IS", "AKBNK.IS", "ISCTR.IS",
    "YKBNK.IS", "SAHOL.IS", "GARAN.IS", "BIMAS.IS", "ASELS.IS", "SISE.IS", "SASA.IS", "TOASO.IS", "TRALT.IS", "AEFES.IS", "VAKBN.IS",

    # --- 2. KADEME: BIST 50 (Sadece BIST 30 dışındakiler) (31-50) ---
    "ULKER.IS", "HALKB.IS", "CCOLA.IS", "BRSAN.IS", "ARCLK.IS", "TRMET.IS", "CIMSA.IS", "ALARK.IS", "MAVI.IS", "TURSG.IS",
    "BTCIM.IS", "HEKTS.IS", "MIATK.IS", "DOAS.IS", "OYAKC.IS", "BRISA.IS", "KONTR.IS", "KUYAS.IS", "PASEU.IS", "CANTE.IS", 

    # --- 3. KADEME: BIST 100 (Sadece BIST 50 dışındakiler) (51-100) ---
    "KLRHO.IS", "ENJSA.IS", "MPARK.IS", "AKSEN.IS", "KTLEV.IS", "ECILC.IS", "ISMEN.IS", "BSOKE.IS", "EFOR.IS", "AKSA.IS",
    "GENIL.IS", "GRSEL.IS", "TSKB.IS", "CWENE.IS", "DAPGM.IS", "TKFEN.IS", "EUPWR.IS", "GESAN.IS",  
    "FENER.IS", "GSRAY.IS", "QUAGR.IS", "ESEN.IS", "NATEN.IS", "KARTN.IS", "SOKE.IS", "ULUUN.IS", "NETAS.IS", "SOKM.IS",
    "FONET.IS", "HUNER.IS", "KFEIN.IS", "OTKAR.IS", "ALTNY.IS", "BALSU.IS", "BRYAT.IS", "AGHOL.IS", "ZOREN.IS", "ODAS.IS", "SARKY.IS", "PAHOL.IS", "PSGYO.IS",
    "TUKAS.IS", "ENERY.IS", "GLRMK.IS", "ANSGR.IS", "GRTHO.IS", "MAGEN.IS", "YAYLA.IS", "FMIZP.IS", "LOGO.IS", "IZENR.IS", "CVKMD.IS", "EUREN.IS",  

    # --- 4. KADEME: BIST 500 (Geri Kalan Hisseler) (101-500+) ---
    "ISBTR.IS", "QNBTR.IS", "HEDEF.IS", "TERA.IS", "PKENT.IS", "QNBFK.IS", "ZRGYO.IS", "AHGAZ.IS", "PEKGY.IS", "DOHOL.IS",
    "AYGAZ.IS", "TBORG.IS", "SELEC.IS", "TTRAK.IS", "IEYHO.IS", "KRDMB.IS",  "AKCNS.IS", "RYSAS.IS", "EGEEN.IS", "KCAER.IS",
    "KRDMA.IS", "BASGZ.IS", "YGGYO.IS", "GLYHO.IS", "TRENJ.IS", "ECZYT.IS", "LYDYE.IS", "SKBNK.IS", "CMENT.IS", "TEHOL.IS",
    "MOGAN.IS", "TRHOL.IS", "POLTK.IS", "ALBRK.IS", "ARASE.IS", "AKFYE.IS", "KONYA.IS", "VERUS.IS", "SNPAM.IS", "BFREN.IS",
    "AYDEM.IS", "ASUZU.IS", "SUNTK.IS", "BANVT.IS", "LMKDC.IS", "FZLGY.IS", "SDTTR.IS",  "KZBGY.IS", "EGPRO.IS", "AKHAN.IS",
    "ULUSE.IS", "ALFAS.IS", "YEOTK.IS", "ESCAR.IS", "IHAAS.IS", "KLSER.IS", "PATEK.IS", "KSTUR.IS", "AYCES.IS", "SMRTG.IS",
    "AKGRT.IS", "VESBE.IS", "A1CAP.IS", "TMSN.IS", "ICBCT.IS", "TRCAS.IS", "BINHO.IS", "AKFGY.IS", "BARMA.IS", "AKSUE.IS",
    "IZMDC.IS", "GARFA.IS", "ALGYO.IS", "EBEBK.IS", "GLCVY.IS", "BMSTL.IS", "KORDS.IS", "BUCIM.IS", "VESTL.IS", "GEREL.IS",
    "OFSYM.IS", "KARSN.IS", "INGRM.IS", "VKGYO.IS", "BIGTK.IS", "EGGUB.IS", "PRKAB.IS", "NTGAZ.IS", "IZFAS.IS", "ADEL.IS",
    "TEZOL.IS", "KAREL.IS", "AYEN.IS", "DITAS.IS", "ATAKP.IS", "ASGYO.IS", "TUREX.IS", "KGYO.IS", "GOKNR.IS", "TSPOR.IS",
    "PARSN.IS", "DOKTA.IS", "GIPTA.IS", "INTEM.IS", "CRDFA.IS", "KAPLM.IS", "KMPUR.IS", "AGROT.IS", "ARSAN.IS", "MANAS.IS",
    "YATAS.IS", "EKOS.IS", "KATMR.IS", "GOLTS.IS", "MNDTR.IS", "EGEPO.IS", "ONCSM.IS", "DESA.IS", "BORSK.IS", "HOROZ.IS",
    "KONKA.IS", "EDATA.IS", "ORGE.IS", "MERIT.IS", "SUWEN.IS", "PENTA.IS", "ADESE.IS", "PLTUR.IS", "SEGYO.IS", "MEKAG.IS",
    "BAGFS.IS", "BRKVY.IS", "BURVA.IS", "TKNSA.IS", "GSDHO.IS", "AZTEK.IS", "ORMA.IS", "PAPIL.IS", "TATGD.IS",
    "ERCB.IS", "YUNSA.IS", "DUNYH.IS", "KLSYN.IS", "MNDRS.IS", "BVSAN.IS", "GOODY.IS", "USAK.IS", "CEMAS.IS", "AYES.IS",
    "BRLSM.IS", "PNLSN.IS", "ATATP.IS", "BLCYT.IS", "PETUN.IS", "TURGG.IS", "LIDFA.IS", "DZGYO.IS", "GZNMI.IS", "BEGYO.IS",
    "MEDTR.IS", "KTSKR.IS", "MACKO.IS", "OSMEN.IS", "FORMT.IS", "NUGYO.IS", "KUVVA.IS", "ISSEN.IS", "SAYAS.IS", "CELHA.IS",
    "PRKME.IS", "SELVA.IS", "YYAPI.IS", "KNFRT.IS", "ARTMS.IS", "BEYAZ.IS", "RUBNS.IS", "MAKTK.IS", "BALAT.IS", "KRGYO.IS",
    "PINSU.IS", "BAKAB.IS", "LRSHO.IS", "BYDNR.IS", "TEKTU.IS", "ARENA.IS", "PAMEL.IS", "CONSE.IS", "VBTYZ.IS",
    "NIBAS.IS", "INTEK.IS", "ISBIR.IS", "DAGI.IS", "BIZIM.IS", "EDIP.IS", "OZSUB.IS", "BORLS.IS", "MTRKS.IS",
    "IHLGM.IS", "RTALB.IS", "MERKO.IS", "OZRDN.IS", "VRGYO.IS", "DURDO.IS", "BMSCH.IS", "DOGUB.IS", "OSTIM.IS",
    "SUMAS.IS", "PENGD.IS", "SKTAS.IS", "KERVN.IS", "VANGD.IS", "YKSLN.IS", "COSMO.IS", "GSDDE.IS", "ZEDUR.IS",
    "KRPLS.IS", "MARTI.IS", "MMCAS.IS", "RNPOL.IS", "SODSN.IS", "IHGZT.IS", "OYAYO.IS", "EPLAS.IS",
    "EKIZ.IS", "AVOD.IS", "BAYRK.IS", "SEKUR.IS", "IZINV.IS", "PRZMA.IS", "ICUGS.IS", "FLAP.IS", "HATEK.IS",
    "VKFYO.IS", "YONGA.IS", "ETILR.IS", "PSDTC.IS", "ORCAY.IS", "IHYAY.IS", "MEGAP.IS", "IHEVA.IS", "BRMEN.IS", "MZHLD.IS",
    "OYLUM.IS", "AKYHO.IS", "ERSU.IS", "RODRG.IS", "IDGYO.IS", "ATSYH.IS", "EUYO.IS", "ISDMR.IS", "DOCO.IS", "TABGD.IS",
    "ISFIN.IS", "JANTS.IS", "CLEBI.IS", "DEVA.IS", "POLHO.IS", "SANKO.IS", "CATES.IS", "REEDR.IS", "ACSEL.IS", "ADGYO.IS",
    "AFYON.IS", "AGESA.IS", "AKENR.IS", "AKSGY.IS", "ALCTL.IS", "ALKIM.IS", "ALVES.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS",
    "ARZUM.IS", "ATAGY.IS", "AVGYO.IS", "AVHOL.IS", "BIENY.IS", "BIGCH.IS", "BJKAS.IS", "BNTAS.IS", "BRKO.IS", "BRKSN.IS",
    "BURCE.IS", "CEMTS.IS", "CEOEM.IS", "CRFSA.IS", "CUSAN.IS", "DARDL.IS", "DERHL.IS", "DESPC.IS", "DGGYO.IS",
    "DGNMO.IS", "DIRIT.IS", "DMRGD.IS", "DNISI.IS", "DOFER.IS", "DYOBY.IS", "EKSUN.IS", "ELITE.IS", "EMKEL.IS", "ENSRI.IS",
    "ESCOM.IS", "EYGYO.IS", "FORTE.IS", "FRIGO.IS", "GENTS.IS", "GLRYH.IS", "HKTM.IS", "HLGYO.IS", "HUBVC.IS",
    "HURGZ.IS", "IHLAS.IS", "IMASM.IS", "INDES.IS", "INFO.IS", "INVEO.IS", "INVES.IS", "ISGSY.IS", "ISKUR.IS", "ISYAT.IS",
    "KENT.IS", "BESLR.IS", "KIMMR.IS", "KLGYO.IS", "KLNMA.IS", "GWIND.IS", "KRONT.IS", "KRVGD.IS", "KUTPO.IS", "ARDYZ.IS",
    "KZGYO.IS", "LIDER.IS", "LINK.IS", "LKMNH.IS", "MAKIM.IS", "MARKA.IS", "MEPET.IS", "MERCN.IS", "METRO.IS", "LYDHO.IS",
    "MOBTL.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS", "MTRYO.IS", "NUHCM.IS", "BERA.IS", "OYYAT.IS", "OZGYO.IS", "OZKGY.IS",
    "PAGYO.IS", "PCILT.IS", "PNSUT.IS", "PRDGS.IS", "RALYH.IS", "RAYSG.IS", "RYGYO.IS", "SAMAT.IS", "SANEL.IS", "SANFM.IS",
    "SEKFK.IS", "SEYKM.IS", "SILVR.IS", "SMART.IS", "SNICA.IS", "GATEG.IS", "SONME.IS", "SRVGY.IS", "TARKM.IS", "TATEN.IS",
    "TDGYO.IS", "TGSAS.IS", "TLMAN.IS", "TMPOL.IS", "TRGYO.IS", "TRILC.IS", "TUCLK.IS", "UFUK.IS", "ULAS.IS", "ULUFA.IS",
    "UNLU.IS", "YAPRK.IS", "YBTAS.IS", "YESIL.IS", "GOZDE.IS", "NTHOL.IS", "KLKIM.IS", "ARFYE.IS", "ATATR.IS", "BESTE.IS", "FRMPL.IS", "MEYSU.IS", "NETCD.IS", "UCAYM.IS", "ZGYO.IS"
]

def _hisse_ham(sembol):
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
        except Exception as e:
            vwap_col = None

        try:
            info = hisse.info
            # PD/DD için Yahoo'nun kullanabileceği alternatif anahtarları sırayla deniyoruz:
            pddd = info.get('priceToBook') or info.get('trailingPriceToBook') or info.get('forwardPriceToBook') or 'Bilinmiyor'
            borc = _net_borc_favok(info)
            ham = {a: info.get(a) for a in HAM_ANAHTARLAR}
        except Exception as e:
            pddd, borc, ham = 'Bilinmiyor', 'Bilinmiyor', {}

        temel = {'PD_DD': pddd, 'Borc_FAVOK': borc, 'VWAP_Col': vwap_col, 'mevsimsel_pozitif': False,
                 'ham': ham, 'pddd_k': pddd_k(sembol), 'para': para_birimi(sembol)}
        return df, temel
    except Exception as e:
        return None, None

@st.cache_resource
def veri_havuzu():
    return {}

def hisse_verileri_getir(sembol, havuz=None):
    if havuz is not None:
        kayit = havuz.get(sembol)
        if kayit and time.time() - kayit[0] < 900:  # 15 dakika önbellek (başarısız çekimler saklanmaz)
            return kayit[1]
    sonuc = _hisse_ham(sembol)
    if havuz is not None and sonuc[0] is not None:
        havuz[sembol] = (time.time(), sonuc)
    return sonuc

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
    pddd = temel.get('PD_DD', 99); kapanis = son['Close']; ema200 = son.get('EMA_200', kapanis); k = temel.get('pddd_k', 1.0)
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
        uyum1 = uyum_hesapla(pddd, hedef=0.7 * k, esik=1.5 * k, yon="dusuk")
        uyum2 = uyum_hesapla(adx, hedef=40, esik=25, yon="yuksek")
        baslik = "Ucuzluk Tuzağı (Trap)"
    elif secilen_senaryo == 'e': 
        uyum1 = uyum_hesapla(pddd, hedef=1.0 * k, esik=2.0 * k, yon="dusuk")
        uyum2 = uyum_hesapla(ema_fark, hedef=0.01, esik=0.05, yon="dusuk")
        baslik = "Güvenli Liman (Value)"

    if uyum1 < 50 or uyum2 < 50: return 0.0, baslik
    return (uyum1 + uyum2) / 2.0, baslik

ABD_YEDEK_LISTE = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "V", "UNH", "XOM", "JNJ", "WMT", "PG",
                   "MA", "HD", "COST", "AVGO", "LLY", "CVX", "KO", "PEP", "ABBV", "MRK", "BAC", "ORCL", "CRM", "NFLX", "AMD"]
ABD_KAYNAKLAR = {
    "S&P 500": ["https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"],
    "S&P 400 (orta ölçekli)": ["https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"],
    "S&P 500 + S&P 400": ["https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"],
}
HAM_ANAHTARLAR = ['sector', 'industry', 'currency', 'marketCap', 'priceToBook', 'trailingPE', 'forwardPE', 'totalDebt', 'totalCash',
                  'ebitda', 'targetMeanPrice', 'recommendationKey', 'numberOfAnalystOpinions']
MAKS_ISCI = 6  # aynı anda kaç hisse indirilsin (Yahoo hız sınırı koyarsa düşür)

@st.cache_data(ttl=86400, show_spinner="ABD hisse listesi alınıyor...")
def abd_evreni_getir(kaynak):
    import requests
    sonuc = {}
    for url in ABD_KAYNAKLAR[kaynak]:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (BorsaRadari)"}, timeout=20)
        r.raise_for_status()
        for t in pd.read_html(io.StringIO(r.text)):
            if "Symbol" in t.columns and "GICS Sector" in t.columns:
                for s, sek in zip(t["Symbol"], t["GICS Sector"]):
                    sonuc.setdefault(str(s).strip().replace(".", "-"), str(sek))
                break
    if len(sonuc) < 50:
        raise ValueError("ABD listesi çekilemedi")
    return sonuc

def para_birimi(sembol):
    for uz, p in ((".IS", "TL"), (".DE", "€"), (".L", "GBp"), (".HK", "HK$"), (".SS", "¥")):
        if sembol.endswith(uz): return p
    return "$"

def pdf_para(sembol):
    return {"$": "USD", "HK$": "HKD"}.get(para_birimi(sembol), para_birimi(sembol))

def pddd_k(sembol):
    # PD/DD eşiklerinin çarpanı: BIST için 1, diğer piyasalar için 2.5 (başlangıç tahmini, kendi görüşüne göre ayarla)
    return 1.0 if sembol.endswith(".IS") else 2.5

def _net_borc_favok(info):
    if str(info.get('sector', '')) == 'Financial Services':
        return 'Finans (geçersiz)'
    try:
        favok, borc = float(info.get('ebitda')), info.get('totalDebt')
        if borc is not None and favok > 0:
            return round((float(borc) - float(info.get('totalCash') or 0)) / favok, 2)
    except (TypeError, ValueError):
        pass
    return 'Bilinmiyor'

def endeks_kodu(sembol):
    if sembol.endswith(".IS"): return "XU100.IS", "BIST 100"
    if "." not in sembol and not sembol.startswith("^"): return "^GSPC", "S&P 500"
    return None, None

@st.cache_data(ttl=900, show_spinner=False)
def endeks_getir(kod):
    try:
        e = yf.Ticker(kod).history(period="1y", interval="1d")
        return e if not e.empty else None
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def usdtry_getir():
    try:
        e = yf.Ticker("USDTRY=X").history(period="1y", interval="1d")
        return e if not e.empty else None
    except Exception:
        return None

@st.cache_data(ttl=21600, show_spinner=False)
def bilanco_tarihi(sembol):
    try:
        cal = yf.Ticker(sembol).calendar
        tarihler = cal.get('Earnings Date') if isinstance(cal, dict) else None
        gelecek = [pd.Timestamp(t).date() for t in (tarihler or []) if pd.Timestamp(t).date() >= datetime.date.today()]
        return min(gelecek) if gelecek else None
    except Exception:
        return None

def _yz(x):
    return "—" if x != x else f"%{x:+.1f}"

def gecmis_sinyal_testi(df, harf):
    kosullar = {
        'a': (df['RSI_14'] < 32) & (df['MFI_14'] < 28),
        'b': (df['RSI_14'] > 52) & (df['ADX_14'] > 22),
        'c': (df['RSI_14'] > 70) & (df['MFI_14'] > 65),
    }
    secilen, son_i = [], -999
    for i, s in enumerate(kosullar[harf].tolist()):
        if s and i - son_i >= 10:  # aynı olayı tekrar saymamak için sinyaller arası en az 10 gün
            secilen.append(i)
            son_i = i
    sonuc = {}
    for h in (5, 10, 20):
        ileri = (df['Close'].shift(-h) / df['Close'] - 1) * 100
        ornek = ileri.iloc[secilen].dropna()
        sonuc[h] = {"n": len(ornek), "ort": ornek.mean(), "pozitif": (ornek > 0).mean() * 100, "genel": ileri.mean(),
                    "toplam": ornek.sum(), "poz_n": (ornek > 0).sum(), "genel_n": ileri.count(), "genel_top": ileri.sum()}
    return sonuc

def strateji_acc_olustur():
    return {x: {h: {"n": 0, "top": 0.0, "poz": 0, "gn": 0, "gtop": 0.0} for h in (5, 10, 20)} for x in "abc"}

def strateji_topla(df, acc):
    for x in "abc":
        t = gecmis_sinyal_testi(df, x)
        for h in (5, 10, 20):
            a = acc[x][h]
            a["n"] += int(t[h]["n"]); a["top"] += float(t[h]["toplam"]); a["poz"] += int(t[h]["poz_n"])
            a["gn"] += int(t[h]["genel_n"]); a["gtop"] += float(t[h]["genel_top"])

def strateji_tablosu(acc):
    satirlar = []
    for x, ad in {"a": "Yay Gevşemesi", "b": "Roket Kalkışı", "c": "Yorgunluk Sinyali"}.items():
        def ort(a): return float('nan') if a["n"] == 0 else a["top"] / a["n"]
        a5, a10, a20 = acc[x][5], acc[x][10], acc[x][20]
        piyasa = a10["gtop"] / a10["gn"] if a10["gn"] else float('nan')
        satirlar.append({"Senaryo": ad, "Toplam sinyal": a10["n"], "5g ort.": _yz(ort(a5)), "10g ort.": _yz(ort(a10)), "20g ort.": _yz(ort(a20)),
                         "10g yükseliş oranı": (f"%{a10['poz'] / a10['n'] * 100:.0f}" if a10["n"] >= 10 else "—"),
                         "Piyasa 10g ort.": _yz(piyasa), "Fark (puan)": ("—" if a10["n"] == 0 or piyasa != piyasa else f"{ort(a10) - piyasa:+.1f}")})
    return satirlar

def destek_direnc(df, pencere=8, tolerans=0.02):
    d = df.tail(252)
    ust, alt, n = d['High'].tolist(), d['Low'].tolist(), len(d)
    pivotlar = []
    for i in range(pencere, n - pencere):
        if ust[i] == max(ust[i - pencere:i + pencere + 1]): pivotlar.append(ust[i])
        if alt[i] == min(alt[i - pencere:i + pencere + 1]): pivotlar.append(alt[i])
    kume = []
    for p in sorted(pivotlar):
        if kume and p <= kume[-1][0] * (1 + tolerans): kume[-1].append(p)
        else: kume.append([p])
    seviyeler = [(sum(k) / len(k), len(k)) for k in kume]
    kap = float(d['Close'].iloc[-1])
    destek = sorted([s for s in seviyeler if s[0] < kap], key=lambda s: kap - s[0])[:3]
    direnc = sorted([s for s in seviyeler if s[0] > kap], key=lambda s: s[0] - kap)[:3]
    return destek, direnc

def grafik_ciz(g, destek, direnc):
    g = g.copy()
    g.insert(0, "Tarih", g.index.tz_localize(None) if getattr(g.index, "tz", None) is not None else g.index)
    g = g.reset_index(drop=True)
    g["Renk"] = ["#26a69a" if c >= o else "#ef5350" for o, c in zip(g["Open"], g["Close"])]
    taban = alt.Chart(g).encode(x=alt.X("Tarih:T", title=None))
    olcek = alt.Scale(zero=False)
    fitil = taban.mark_rule().encode(y=alt.Y("Low:Q", scale=olcek, title="Fiyat"), y2="High:Q", color=alt.Color("Renk:N", scale=None))
    govde = taban.mark_bar(size=3).encode(y=alt.Y("Open:Q", scale=olcek), y2="Close:Q", color=alt.Color("Renk:N", scale=None),
                                          tooltip=["Tarih:T", "Open:Q", "High:Q", "Low:Q", "Close:Q"])
    ema = taban.mark_line(color="#ff7f0e", strokeDash=[4, 3]).encode(y=alt.Y("EMA_200:Q", scale=olcek))
    katmanlar = [fitil, govde, ema]
    sev = pd.DataFrame([{"Fiyat": f, "Etiket": f"Destek {f:.2f} ({t} temas)", "Renk": "#26a69a"} for f, t in destek] +
                       [{"Fiyat": f, "Etiket": f"Direnç {f:.2f} ({t} temas)", "Renk": "#ef5350"} for f, t in direnc])
    if len(sev):
        katmanlar.append(alt.Chart(sev).mark_rule(strokeDash=[6, 4], opacity=0.8).encode(y=alt.Y("Fiyat:Q", scale=olcek), color=alt.Color("Renk:N", scale=None)))
        katmanlar.append(alt.Chart(sev).mark_text(align="left", dx=4, dy=-6, fontSize=11).encode(x=alt.value(6), y=alt.Y("Fiyat:Q", scale=olcek), text="Etiket:N", color=alt.Color("Renk:N", scale=None)))
    st.altair_chart(alt.layer(*katmanlar).properties(height=380).interactive(), use_container_width=True)
    st.caption("Mum grafiği (yeşil: yükseliş, kırmızı: düşüş), turuncu kesikli çizgi: EMA200. Destek/direnç çizgileri son 1 yıldaki tepe/dip kümelerinden otomatik bulunur; kesin değil, yaklaşık seviyelerdir.")

def hisse_karnesi(df, temel, sembol):
    son = df.iloc[-1]
    kap = float(son['Close']); rsi = float(son.get('RSI_14', 50)); mfi = float(son.get('MFI_14', 50)); adx = float(son.get('ADX_14', 0))
    ema = float(son.get('EMA_200', kap))
    para = temel.get('para', '')
    y = []

    # 1) Ana trend
    fark = (kap / ema - 1) * 100
    egim = (ema / float(df['EMA_200'].iloc[-21]) - 1) * 100 if len(df) > 221 else 0.0
    if fark > 0:
        y.append(("🟢", f"Fiyat EMA200'ün %{fark:.1f} üzerinde; ana trend {'yükseliyor' if egim > 0 else 'yataylaşıyor/zayıflıyor'} (EMA200 son 20 günde %{egim:+.1f})."))
    else:
        y.append(("🔴", f"Fiyat EMA200'ün %{abs(fark):.1f} altında; ana trend zayıf. EMA200'e dönmek için %{(ema / kap - 1) * 100:.1f} yükseliş gerekir."))

    # 2) Momentum (RSI)
    if rsi < 30: y.append(("🟡", f"RSI {rsi:.0f}: aşırı satım. Tepki alımı gelebilir ama trend aşağıysa 'düşen bıçak' riski sürer."))
    elif rsi < 45: y.append(("🟠", f"RSI {rsi:.0f}: momentum zayıf, henüz toparlanma sinyali yok."))
    elif rsi < 55: y.append(("⚪", f"RSI {rsi:.0f}: momentum nötr."))
    elif rsi < 70: y.append(("🟢", f"RSI {rsi:.0f}: momentum güçlü ve henüz aşırı ısınmamış."))
    else: y.append(("🟡", f"RSI {rsi:.0f}: aşırı alım. Düzeltme riski artmış durumda."))

    # 3) Para akışı (fiyat - MFI uyumsuzluğu)
    f10 = (kap / float(df['Close'].iloc[-11]) - 1) * 100
    m10 = mfi - float(df['MFI_14'].iloc[-11])
    if f10 > 2 and m10 < -5: y.append(("⚠️", f"Negatif uyumsuzluk: fiyat 10 günde %{f10:+.1f} yükselirken MFI {m10:+.0f} puan düştü; yükseliş hacimle desteklenmiyor."))
    elif f10 < -2 and m10 > 5: y.append(("🟢", f"Pozitif uyumsuzluk: fiyat 10 günde %{f10:+.1f} düşerken MFI {m10:+.0f} puan arttı; satış baskısı azalıyor olabilir."))
    elif mfi < 20: y.append(("🟡", f"MFI {mfi:.0f}: para çıkışı aşırı, dip bölgesine yakın."))
    elif mfi > 80: y.append(("🟡", f"MFI {mfi:.0f}: aşırı para girişi, zirve bölgesine yakın."))
    else: y.append(("⚪", f"MFI {mfi:.0f}: para akışı dengeli."))

    # 4) Trend gücü (ADX)
    if adx >= 25: y.append(("🟢" if fark > 0 else "🔴", f"ADX {adx:.0f}: trend güçlü ({'yukarı' if fark > 0 else 'aşağı'} yönlü)."))
    elif adx < 20: y.append(("⚪", f"ADX {adx:.0f}: yatay/testere piyasası, trend sinyalleri güvenilmez."))
    else: y.append(("⚪", f"ADX {adx:.0f}: trend oluşum aşamasında."))

    # 5) 52 haftalık konum
    yil = df.tail(252)
    ust, alt_ = float(yil['High'].max()), float(yil['Low'].min())
    if ust > alt_ > 0:
        y.append(("📏", f"52 haftalık aralıkta konum: %{(kap - alt_) / (ust - alt_) * 100:.0f} (0=dip, 100=zirve). Zirveye uzaklık %{(kap / ust - 1) * 100:.1f}, dipten uzaklık %{(kap / alt_ - 1) * 100:+.1f}."))

    # 5b) Destek / direnç
    destek, direnc = destek_direnc(df)
    if direnc: y.append(("🔼", f"En yakın direnç: {direnc[0][0]:.2f} {para} (%{(direnc[0][0] / kap - 1) * 100:+.1f}, {direnc[0][1]} temas)."))
    if destek: y.append(("🔽", f"En yakın destek: {destek[0][0]:.2f} {para} (%{(destek[0][0] / kap - 1) * 100:+.1f}, {destek[0][1]} temas)."))

    # 6) Hacim ilgisi
    v5, v25 = float(df['Volume'].tail(5).mean()), float(df['Volume'].tail(25).mean())
    if v25 > 0:
        if v5 / v25 >= 1.5: y.append(("📈", f"Son 5 günlük hacim, 25 günlük ortalamanın {v5 / v25:.1f} katı: ilgi artıyor."))
        elif v5 / v25 <= 0.6: y.append(("📉", f"Son 5 günlük hacim, 25 günlük ortalamanın {v5 / v25:.1f} katı: ilgi azalıyor."))

    # 7) Oynaklık (ATR)
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.tail(14).mean()) / kap * 100
    y.append(("🌊", f"Günlük ortalama hareket aralığı (ATR) ≈ %{atr:.1f}: oynaklık {'yüksek' if atr > 4 else ('orta' if atr > 2.5 else 'düşük')}."))

    # 8) Endekse göre güç
    kod, ad = endeks_kodu(sembol)
    if kod:
        e = endeks_getir(kod)
        if e is not None and len(e) > 64 and len(df) > 64:
            h3 = (kap / float(df['Close'].iloc[-64]) - 1) * 100
            e3 = (float(e['Close'].iloc[-1]) / float(e['Close'].iloc[-64]) - 1) * 100
            y.append(("🏁", f"Son ~3 ayda hisse %{h3:+.1f}, {ad} %{e3:+.1f}: endeksin {'önünde' if h3 > e3 else 'gerisinde'} ({h3 - e3:+.1f} puan)."))

    # 9) Değerleme (eşikler piyasaya göre ölçeklenir)
    k = temel.get('pddd_k', 1.0)
    try:
        p = float(temel.get('PD_DD', 'Bilinmiyor'))
        if p <= 0: y.append(("💰", "PD/DD negatif: özsermaye negatif olabilir, bilançoyu kontrol et."))
        elif p < 1 * k: y.append(("💰", f"PD/DD {p:.2f}: defter değerine göre ucuz görünüm (nedenini araştır)."))
        elif p < 2 * k: y.append(("💰", f"PD/DD {p:.2f}: makul seviyede."))
        elif p < 4 * k: y.append(("💰", f"PD/DD {p:.2f}: defter değerine göre pahalılaşmış."))
        else: y.append(("💰", f"PD/DD {p:.2f}: defter değerine göre pahalı."))
    except (TypeError, ValueError):
        pass

    # 10) Senaryo uyumları + geçmiş sinyal testi
    uyum, baslik = {}, {}
    for h in "abcde":
        uyum[h], baslik[h] = senaryo_yuzde_tespit(df, temel, h)
    aktifler = [f"{baslik[h]} %{uyum[h]:.0f}" for h in "abcde" if uyum[h] >= 50]
    y.insert(0, ("🎯", ("Senaryo uyumu: " + ", ".join(aktifler) + ".") if aktifler else "Şu an hiçbir senaryoya belirgin (≥%50) uyum yok."))

    tablo = []
    for h, ad in {"a": "Yay Gevşemesi", "b": "Roket Kalkışı", "c": "Yorgunluk Sinyali"}.items():
        t = gecmis_sinyal_testi(df, h)
        tablo.append({"Senaryo": ad, "Şu an": (f"✅ %{uyum[h]:.0f}" if uyum[h] >= 50 else "—"), "Geçmişte (adet)": t[10]["n"],
                      "5g ort.": _yz(t[5]["ort"]), "10g ort.": _yz(t[10]["ort"]), "20g ort.": _yz(t[20]["ort"]),
                      "10g yükseliş oranı": ("—" if t[10]["n"] < 3 else f"%{t[10]['pozitif']:.0f}"), "Hisse genel 10g ort.": _yz(t[10]["genel"])})
        if uyum[h] >= 50:
            if t[10]["n"] >= 5:
                y.append(("🧪", f"Geçmiş test: bu hissede {ad} senaryosu 3 yılda {t[10]['n']} kez tetiklendi; 10 işlem günü sonra ortalama {_yz(t[10]['ort'])}, yükselişle kapanma oranı %{t[10]['pozitif']:.0f} (hissenin genel 10 günlük ortalaması {_yz(t[10]['genel'])})."))
            else:
                y.append(("🧪", f"Geçmiş test: {ad} senaryosu bu hissede 3 yılda yalnızca {t[10]['n']} kez tetiklendi; örneklem yetersiz."))

    # Genel teknik görünüm skoru (-5 ... +5)
    skor = (1 if kap > ema else -1) + (1 if egim > 0 else -1) + (1 if rsi >= 50 else -1) + (1 if mfi >= 50 else -1)
    if adx >= 25: skor += 1 if kap > ema else -1
    genel, ikon = ("Olumlu", "🟢") if skor >= 3 else (("Zayıf", "🔴") if skor <= -3 else ("Kararsız", "🟡"))
    return {"genel": genel, "ikon": ikon, "skor": skor, "yorumlar": y, "tablo": tablo, "destek": destek, "direnc": direnc}

def ek_satirlar(sembol, temel, grafik):
    s = []
    ham = temel.get('ham') or {}
    para = temel.get('para', '')
    kap = float(grafik['Close'].iloc[-1])
    if ham.get('sector'):
        s.append(("🏭", f"Sektör: {ham.get('sector')}" + (f" / {ham.get('industry')}" if ham.get('industry') else "")))
    b = temel.get('Borc_FAVOK')
    if isinstance(b, (int, float)):
        s.append(("🏦", f"Net borç/FAVÖK {b:.2f}: " + ("net nakit pozisyonu." if b < 0 else ("borç yükü güvenli bölgede." if b < 3 else ("borç yükü dikkat çekiyor." if b < 5 else "borç yükü yüksek.")))))
    elif isinstance(b, str) and 'geçersiz' in b:
        s.append(("🏦", "Net borç/FAVÖK finans şirketlerinde (banka, sigorta vb.) anlamlı bir ölçüt değildir."))
    try:
        hedef = ham.get('targetMeanPrice')
        if hedef:
            s.append(("🎯", f"Analist ortalama hedef fiyatı {float(hedef):.2f} {para} (güncel fiyata göre %{(float(hedef) / kap - 1) * 100:+.1f}); öneri: {ham.get('recommendationKey', '-')} ({ham.get('numberOfAnalystOpinions', '?')} analist)."))
    except (TypeError, ValueError):
        pass
    t = bilanco_tarihi(sembol)
    if t:
        gun = (t - datetime.date.today()).days
        if gun <= 90:
            s.append(("⚠️" if gun <= 7 else "📅", f"Sonraki bilanço: {t:%d.%m.%Y} ({gun} gün sonra)." + (" Bilanço öncesinde teknik sinyaller güvenilmez olabilir." if gun <= 7 else "")))
    if sembol.endswith(".IS"):
        fx = usdtry_getir()
        if fx is not None:
            try:
                g = grafik['Close'].copy(); g.index = g.index.tz_localize(None).normalize()
                f = fx['Close'].copy(); f.index = f.index.tz_localize(None).normalize()
                usd = (g / f.reindex(g.index, method='ffill')).dropna()
                if len(usd) > 64:
                    s.append(("💵", f"Dolar bazında son ~3 ay: %{(usd.iloc[-1] / usd.iloc[-64] - 1) * 100:+.1f} (TL bazında %{(g.iloc[-1] / g.iloc[-64] - 1) * 100:+.1f})."))
            except Exception:
                pass
    return s

def karne_goster(k, grafik, sembol, temel):
    st.markdown(f"#### {k['ikon']} Genel Teknik Görünüm: **{k['genel']}** (skor {k['skor']:+d} / ±5)")
    for ikon, metin in k['yorumlar'] + ek_satirlar(sembol, temel, grafik):
        st.markdown(f"{ikon} {metin}")
    st.markdown("**🧪 Bu hissede senaryolar geçmişte nasıl çalıştı? (son 3 yıl)**")
    st.dataframe(pd.DataFrame(k['tablo']), use_container_width=True, hide_index=True)
    st.caption("Aynı olayı tekrar saymamak için sinyaller arasında en az 10 işlem günü bırakılır. Örneklem küçükse (5'ten az) sonuçlara güvenmeyin. Geçmiş performans gelecek için garanti değildir; yatırım tavsiyesi değildir.")
    grafik_ciz(grafik, k.get('destek', []), k.get('direnc', []))
    with st.expander("🔎 Yahoo'dan gelen ham veri (veri kalitesi kontrolü)"):
        ham = temel.get('ham') or {}
        st.dataframe(pd.DataFrame({"Alan": list(HAM_ANAHTARLAR), "Değer": [("— (gelmedi)" if ham.get(a) is None else str(ham.get(a))) for a in HAM_ANAHTARLAR]}), hide_index=True, use_container_width=True)

def karsilastir_goster(kodlar):
    if len(kodlar) < 2:
        st.warning("⚠️ Karşılaştırma için en az 2 hisse kodu girin (örn. THYAO.IS, PGSUS.IS).")
        return
    havuz = veri_havuzu()
    veriler, hatali = {}, []
    for s in kodlar:
        df, temel = hisse_verileri_getir(s, havuz)
        if df is None: hatali.append(s)
        else: veriler[s] = (df, temel)
    if hatali:
        st.warning(f"⚠️ Veri alınamayan hisseler: {', '.join(hatali)}")
    if len(veriler) < 2:
        return
    st.subheader("⚖️ Hisse Karşılaştırması")
    seriler = {}
    for s, (df, _) in veriler.items():
        c = df['Close'].tail(252).copy()
        c.index = c.index.tz_localize(None).normalize()
        seriler[s] = c
    birlesik = pd.concat(seriler, axis=1).sort_index().ffill().dropna()
    if len(birlesik) > 1:
        st.markdown("**Son 1 yıl, başlangıç = 100** (farklı piyasalarda yalnızca yüzde değişim karşılaştırılır)")
        st.line_chart(birlesik / birlesik.iloc[0] * 100)
    satirlar = []
    for s, (df, temel) in veriler.items():
        k = hisse_karnesi(df, temel, s)
        son = df.iloc[-1]; kap = float(son['Close']); ema = float(son.get('EMA_200', kap))
        satirlar.append({"Hisse": s, "Kapanış": round(kap, 2), "3 ay %": round((kap / float(df['Close'].iloc[-64]) - 1) * 100, 1),
                         "1 yıl %": round((kap / float(df['Close'].iloc[-253]) - 1) * 100, 1) if len(df) > 253 else float('nan'),
                         "RSI": round(float(son.get('RSI_14', 0)), 1), "MFI": round(float(son.get('MFI_14', 0)), 1), "ADX": round(float(son.get('ADX_14', 0)), 1),
                         "EMA200 farkı %": round((kap / ema - 1) * 100, 1), "PD/DD": round(float(pd.to_numeric(temel.get('PD_DD'), errors='coerce')), 2),
                         "Görünüm": f"{k['ikon']} {k['genel']}"})
    st.dataframe(pd.DataFrame(satirlar), use_container_width=True, hide_index=True)
    if len(birlesik) > 30:
        st.markdown("**Günlük getiri korelasyonu** (1'e yakın: birlikte hareket ediyorlar, 0'a yakın: bağımsız)")
        st.dataframe(birlesik.pct_change().dropna().corr().round(2), use_container_width=True)

def pdf_bellege_uret(df, sembol, temel, son, puan, ema_etiket, vwap_deger, rsi_val, mfi_val, adx_val, pddd, senaryo_adi, senaryo_metni, tepki_potansiyeli=0, karne=None):
    pdf_buffer = io.BytesIO()
    PB = pdf_para(sembol)
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
        v_str = f"{float(vwap_deger):.2f} {PB}"
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
    ax_metin.text(c1_v, y1, f"{son['Close']:.2f} {PB}", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_k, y1, "RSI:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c2_v, y1, f"{rsi_val:.1f}", fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_k, y1, "PD/DD:", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c3_v, y1, pddd_str, fontsize=11, transform=ax_metin.transAxes)

    # 3. Satır
    y2 = 0.52
    ax_metin.text(c1_k, y2, "EMA(200):", fontweight='bold', color='navy', fontsize=11, transform=ax_metin.transAxes)
    ax_metin.text(c1_v, y2, f"{son.get('EMA_200', 0):.2f} {PB}", fontsize=11, transform=ax_metin.transAxes)
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
    ax1.set_ylabel(f"Fiyat ({PB})", fontweight='bold')

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
    ax3.set_ylabel(f"Fiyat ({PB})", fontweight='bold')

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
    ax5.set_ylabel(f"Fiyat ({PB})", fontweight='bold')

    ax6 = plt.subplot(gs2[3], sharex=ax5)
    ax6.bar(df_3y.index, df_3y['Volume'], color='#7f7f7f', alpha=0.7, label='İşlem Hacmi')
    ax6.legend(loc='upper left', frameon=True, fontsize=9)
    ax6.set_ylabel("Hacim", fontweight='bold')

    pdf.savefig(fig2, bbox_inches='tight')

    if karne:
        fig3 = plt.figure(figsize=(15, 12))
        fig3.suptitle(f"{sembol} - AKILLI YORUM VE GEÇMİŞ SİNYAL TESTİ", fontsize=18, fontweight='bold', color='darkgreen')
        ax_y = fig3.add_subplot(111)
        ax_y.axis('off')
        satirlar = [f"GENEL TEKNİK GÖRÜNÜM: {karne['genel'].upper()} (skor {karne['skor']:+d} / ±5)", ""]
        for _, metin in karne['yorumlar']:
            satirlar += textwrap.wrap("- " + metin, width=115, subsequent_indent="  ")
        satirlar += ["", "GEÇMİŞ SENARYO TESTİ (son 3 yıl):"]
        for s in karne['tablo']:
            satirlar += textwrap.wrap(" | ".join(f"{a}: {b}" for a, b in s.items()).replace("✅", "[AKTİF]"), width=115, subsequent_indent="    ")
        ax_y.text(0.0, 0.97, "\n".join(satirlar).replace("$", r"\$"), va='top', ha='left', fontsize=11, transform=ax_y.transAxes)
        pdf.savefig(fig3, bbox_inches='tight')
    
    pdf.close()
    plt.close('all')
    return pdf_buffer.getvalue()

# ==============================================================================
# BÖLÜM 2: YAN MENÜ (KUMANDA PANELİ)
# ==============================================================================
st.sidebar.title("⚙️ Kumanda Paneli")
piyasa = st.sidebar.radio("Piyasa", ["🇹🇷 BIST", "🇺🇸 ABD"], horizontal=True)
abd_modu = piyasa.endswith("ABD")
sektor_haritasi = {}
aktif_liste = bist_listesi
if abd_modu:
    abd_kaynak = st.sidebar.selectbox("ABD endeksi", list(ABD_KAYNAKLAR.keys()))
    try:
        sektor_haritasi = abd_evreni_getir(abd_kaynak)
        aktif_liste = list(sektor_haritasi.keys())
    except Exception:
        aktif_liste = ABD_YEDEK_LISTE
        st.sidebar.warning("⚠️ ABD hisse listesi çekilemedi, 30 hisselik yedek liste kullanılıyor.")
mod_secimi = st.sidebar.radio("Tarama Modu", ["Çoklu Hisse Tarama", "Tekli Hisse Tarama", "İzleme Listesi", "Karşılaştırma"])

tekli_sembol = ""
uyum_esigi = 75
if mod_secimi == "Çoklu Hisse Tarama":
    toplam_sayi = len(aktif_liste)
    _b = min(max(st.session_state['baslangic_degeri'], 1), toplam_sayi)
    _e = min(max(st.session_state['bitis_degeri'], _b), toplam_sayi)
    if (_b, _e) != (st.session_state['baslangic_degeri'], st.session_state['bitis_degeri']):
        st.session_state['baslangic_degeri'], st.session_state['bitis_degeri'], st.session_state['aralik_slider'] = _b, _e, (_b, _e)
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"📏 Arama Aralığı (1-{toplam_sayi})")
    
    st.sidebar.markdown("<div style='color: #666; font-size: 13px; margin-bottom: 10px; line-height: 1.4;'>ℹ️ Seçili piyasanın (BIST veya ABD endeksleri) sisteme kayıtlı hisseleri arasından taramak istediğiniz aralığı aşağıdaki çubuktan veya kutucuklardan belirleyebilirsiniz.</div>", unsafe_allow_html=True)
    
    st.sidebar.slider("Kaydırma Çubuğu", min_value=1, max_value=toplam_sayi, key='aralik_slider', on_change=slider_guncelle)
    # Mobilde sıkışmayı önlemek için sütunları kaldırdık, alt alta koyduk
    baslangic = st.sidebar.number_input("Başlangıç Hisse No:", min_value=1, max_value=toplam_sayi, key='baslangic_degeri', on_change=kutu_guncelle)
    bitis = st.sidebar.number_input("Bitiş Hisse No:", min_value=1, max_value=toplam_sayi, key='bitis_degeri', on_change=kutu_guncelle)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Strateji Seçimi")
    strateji = st.sidebar.radio("Yöntem:", ["Lütfen Seçiniz...", "Senaryo Algoritması", "Risk Profili", "Manuel Kriterler"])
    
    alt_secim = None
    rsi_aralik = mfi_aralik = adx_aralik = (0.0, 100.0)
    pddd_min, pddd_max = 0.0, (5.0 if abd_modu else 2.0)
    if strateji == "Senaryo Algoritması":
        alt_secim = st.sidebar.radio("📌 Alt Kategori:", ["a. Yay Gevşemesi", "b. Roket Kalkışı", "c. Yorgunluk Sinyali", "d. Ucuzluk Tuzağı", "e. Güvenli Liman"])
    elif strateji == "Risk Profili":
        alt_secim = st.sidebar.slider("Risk İştahınız (0: Güvenli, 100: Agresif)", 0, 100, 50)
    elif strateji == "Manuel Kriterler":
        st.sidebar.info("👉 Sağ taraftan tavsiye edilen Filtre Stratejilerini görebilirsiniz.")
        st.sidebar.markdown("**Manuel Aralıklar (Min - Max)**")
        rsi_aralik = st.sidebar.slider("RSI Aralığı", 0.0, 100.0, (0.0, 45.0), step=1.0)
        mfi_aralik = st.sidebar.slider("MFI Aralığı", 0.0, 100.0, (0.0, 45.0), step=1.0)
        adx_aralik = st.sidebar.slider("ADX Aralığı", 0.0, 100.0, (20.0, 100.0), step=1.0)
        p_col1, p_col2 = st.sidebar.columns(2)
        pddd_min = p_col1.number_input("PD/DD Min", value=0.0, step=0.1, key=f"pddd_min_{abd_modu}")
        pddd_max = p_col2.number_input("PD/DD Max", value=5.0 if abd_modu else 2.0, step=0.1, key=f"pddd_max_{abd_modu}")
        if pddd_min > pddd_max:
            st.sidebar.warning("⚠️ PD/DD Min değeri Max değerinden büyük olamaz.")

    uyum_esigi = st.sidebar.slider("🎚️ Minimum Uyum Eşiği (%)", 50, 100, 75, step=5, help="Düşürürsen daha fazla hisse eşleşir, yükseltirsen daha seçici olur.")

elif mod_secimi == "Tekli Hisse Tarama":
    tekli_sembol = st.sidebar.text_input("Hisse Kodu Girin (Örn: THYAO.IS):", value="AAPL" if abd_modu else "THYAO.IS").upper()
    
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

elif mod_secimi == "İzleme Listesi":
    if 'izleme_metni' not in st.session_state:
        st.session_state['izleme_metni'] = st.query_params.get("izleme", "THYAO.IS,ASELS.IS,KCHOL.IS").replace(",", ", ")
    st.sidebar.text_area("⭐ Hisse kodları (virgülle ayırın):", key='izleme_metni', height=110)
    izleme_listesi = list(dict.fromkeys(s.strip().upper() for s in st.session_state['izleme_metni'].replace("\n", ",").split(",") if s.strip()))
    st.query_params["izleme"] = ",".join(izleme_listesi)
    st.sidebar.caption("🔖 Tarayıcı adresi listenle birlikte güncellenir: sayfayı yer imine ekle, listen hep hazır olsun. Kodlara uzantıyı unutma (örn. THYAO.IS).")

elif mod_secimi == "Karşılaştırma":
    kars_metni = st.sidebar.text_input("2-3 hisse kodu (virgülle ayırın):", value="AAPL, MSFT" if abd_modu else "THYAO.IS, PGSUS.IS")
    kars_kodlar = list(dict.fromkeys(x.strip().upper() for x in kars_metni.split(",") if x.strip()))[:3]

st.sidebar.markdown("---")
buton_sutun1, buton_sutun2 = st.sidebar.columns(2)
baslat = buton_sutun1.button("▶️ BAŞLAT", use_container_width=True)
durdur = buton_sutun2.button("🛑 DURDUR", use_container_width=True)

if baslat and mod_secimi == "Çoklu Hisse Tarama" and strateji == "Lütfen Seçiniz...":
    st.sidebar.warning("⚠️ Önce bir strateji seçiniz.")
    baslat = False

if baslat and mod_secimi == "Çoklu Hisse Tarama" and strateji == "Manuel Kriterler" and pddd_min > pddd_max:
    st.sidebar.warning("⚠️ PD/DD Min değeri Max değerinden büyük olamaz.")
    baslat = False
    
if baslat and mod_secimi == "Karşılaştırma":
    st.session_state['kars_kodlar'] = kars_kodlar

if durdur:
    # 1. Hafızadaki tüm eski tarama verilerini sil
    if 'eslesenler_hafiza' in st.session_state:
        del st.session_state['eslesenler_hafiza']
    if 'bronz_hafiza' in st.session_state:
        del st.session_state['bronz_hafiza']
    if 'hatali_hafiza' in st.session_state:
        del st.session_state['hatali_hafiza']
        
    st.session_state.pop('kars_kodlar', None)
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
if mod_secimi == "Karşılaştırma" and 'kars_kodlar' in st.session_state:
    karsilastir_goster(st.session_state['kars_kodlar'])
elif not baslat and not arama_gecmisi_var:
    
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
                "*(RSI: 0–35 | MFI: 0–30 | PD/DD: 0–2 | ADX: 25–100)*<br><br>"
                "**2. Dengeli Trend (Orta Risk):**<br>"
                "Arkasına güçlü trend almış istikrarlı hisseler.<br>"
                "*(RSI: 40–60 | MFI: 35–60 | PD/DD: 0–4 | ADX: 20–50)*<br><br>"
                "**3. Değer Yatırımcısı (Düşük Risk):**<br>"
                "Teknik coşkudan ziyade ucuzluğa odaklanır.<br>"
                "*(RSI: 25–50 | MFI: 25–50 | PD/DD: 0–1.5 | ADX: 15–40)*",
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
        if mod_secimi == "Çoklu Hisse Tarama": taranacak_liste = aktif_liste[baslangic-1:bitis]
        elif mod_secimi == "İzleme Listesi": taranacak_liste = izleme_listesi
        else: taranacak_liste = [tekli_sembol]
        toplam_hisse = len(taranacak_liste)
        
        ilerleme_cubugu = st.progress(0.0)
        durum_metni = st.empty()
        gecici_eslesenler = []
        gecici_bronz_liste = []
        gecici_hatali = []
        nabiz_listesi = []
        strateji_acc = strateji_acc_olustur()

        import time # Çubuğun mobilde donmasını engellemek için
        
        havuz = veri_havuzu()
        for _k in [k for k, v in havuz.items() if time.time() - v[0] > 900]:
            havuz.pop(_k, None)
        indirilenler = {}
        yurutucu = ThreadPoolExecutor(max_workers=MAKS_ISCI)
        try:
            gorevler = {yurutucu.submit(hisse_verileri_getir, s_, havuz): s_ for s_ in taranacak_liste}
            for j, g_ in enumerate(as_completed(gorevler)):
                try: indirilenler[gorevler[g_]] = g_.result()
                except Exception: indirilenler[gorevler[g_]] = (None, None)
                durum_metni.text(f"⬇️ Veriler indiriliyor: {j+1}/{toplam_hisse}")
                ilerleme_cubugu.progress((j + 1) / toplam_hisse)
        finally:
            yurutucu.shutdown(wait=False, cancel_futures=True)

        for i, sembol in enumerate(taranacak_liste):
            durum_metni.text(f"🔍 [{i+1}/{toplam_hisse}] Analiz ediliyor: {sembol} ...")
            ilerleme_cubugu.progress((i + 1) / toplam_hisse)
            time.sleep(0.01) # Arayüze nefes aldırır
            
            df, temel = indirilenler.get(sembol, (None, None))
            if df is None:
                gecici_hatali.append(sembol)
                continue
            _s = df.iloc[-1]
            _v25 = df['Volume'].tail(25).mean()
            nabiz_listesi.append({"Hisse": sembol, "Sektör": sektor_haritasi.get(sembol, ""),
                                  "Günlük %": round(float((_s['Close'] / df['Close'].iloc[-2] - 1) * 100), 2),
                                  "Hacim x": round(float(_s['Volume'] / _v25), 1) if _v25 > 0 else 0.0,
                                  "RSI": round(float(_s.get('RSI_14', 50)), 1),
                                  "EMA200 üstü": bool(_s['Close'] > _s.get('EMA_200', _s['Close']))})
            strateji_topla(df, strateji_acc)
            
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
                    p_p = 10 if (isinstance(pddd, (int, float)) and pddd < 1.5 * temel.get('pddd_k', 1.0)) else (5 if (isinstance(pddd, (int, float)) and pddd < 3 * temel.get('pddd_k', 1.0)) else 0)
                    
                    puan = (r_p * rsi_w) + (m_p * mfi_w) + (a_p * adx_w) + (p_p * pddd_w)
                    if temel.get('mevsimsel_pozitif'): puan += 1
                    uyum_puani = (puan / 11.0) * 100 
                    senaryo_adi = f"{senaryo_adi} (Puan: {puan:.1f}/11)"

                elif strateji == "Manuel Kriterler":
                    son = df.iloc[-1]
                    rsi_val = son.get('RSI_14', 50); mfi_val = son.get('MFI_14', 50); adx_val = son.get('ADX_14', 0); pddd = temel.get('PD_DD', 'Bilinmiyor')
                    puan = 0
                    if rsi_aralik[0] <= rsi_val <= rsi_aralik[1]: puan += 1
                    if mfi_aralik[0] <= mfi_val <= mfi_aralik[1]: puan += 1
                    if adx_aralik[0] <= adx_val <= adx_aralik[1]: puan += 1
                    if isinstance(pddd, (int, float)) and pddd_min <= pddd <= pddd_max: puan += 1
                    uyum_puani = (puan / 4.0) * 100
                    senaryo_adi = f"Manuel Kriter Eşleşmesi (Puan: {puan}/4)"
            else:
                uyum_puani = 100
                senaryo_adi = "Tekli İnceleme"

            if uyum_puani >= uyum_esigi:
                son = df.iloc[-1]
                kapanis = son['Close']
                ema200 = son.get('EMA_200', kapanis)
                ema_etiket = "POZİTİF (Fiyat > EMA200)" if kapanis > ema200 else "NEGATİF (Fiyat < EMA200)"
                
                # VWAP Değerini yakalama düzeltmesi
                vwap_sutun = temel.get('VWAP_Col')
                vwap_degeri = son.get(vwap_sutun, 'Bilinmiyor') if vwap_sutun else 'Bilinmiyor'
                
                karne = hisse_karnesi(df, temel, sembol)
                pdf_bytes = pdf_bellege_uret(
                    df, sembol, temel, son, uyum_puani, ema_etiket, 
                    vwap_degeri, son.get('RSI_14', 50), 
                    son.get('MFI_14', 50), son.get('ADX_14', 0), 
                    temel.get('PD_DD', 'Bilinmiyor'), senaryo_adi, "", karne=karne
                )
                gecici_eslesenler.append({"sembol": sembol, "uyum": uyum_puani, "pdf": pdf_bytes,
                                          "kapanis": round(float(kapanis), 2), "rsi": round(float(son.get('RSI_14', 0)), 1),
                                          "mfi": round(float(son.get('MFI_14', 0)), 1), "adx": round(float(son.get('ADX_14', 0)), 1),
                                          "pddd": round(float(pd.to_numeric(temel.get('PD_DD'), errors='coerce')), 2),
                                          "trend": "↑" if kapanis > ema200 else "↓"})
                gecici_eslesenler[-1].update({"gorunum": f"{karne['ikon']} {karne['genel']}", "karne": karne, "grafik": df[['Open', 'High', 'Low', 'Close', 'EMA_200']].tail(252), "temel": temel})

            elif mod_secimi == "Çoklu Hisse Tarama" and uyum_puani >= 50:
                gecici_bronz_liste.append({"sembol": sembol, "uyum": uyum_puani})

        # Tarama bitti, sonuçları HAFIZAYA kaydet (İndirme butonuna basınca silinmesin diye)
        gecici_eslesenler.sort(key=lambda x: x['uyum'], reverse=True)
        st.session_state['eslesenler_hafiza'] = gecici_eslesenler
        st.session_state['bronz_hafiza'] = gecici_bronz_liste
        st.session_state['hatali_hafiza'] = gecici_hatali
        st.session_state['nabiz_hafiza'] = nabiz_listesi
        st.session_state['strateji_hafiza'] = strateji_tablosu(strateji_acc)
        durum_metni.empty()
        ilerleme_cubugu.empty()

    # --- EKRANA YAZDIRMA BÖLÜMÜ (HAFIZADAN OKUR) ---
    eslesenler = st.session_state.get('eslesenler_hafiza', [])
    bronz_liste = st.session_state.get('bronz_hafiza', [])

# Eğer hafızada tarama sonucu varsa ekrana bas (Butona basılmasa da hep ekranda kalır)
    if 'eslesenler_hafiza' in st.session_state:
        
        if st.button("📚 Başucu Rehberini Görüntüle / Gizle", use_container_width=True):
            st.session_state['rehber_goster'] = not st.session_state.get('rehber_goster', False)
        
        if st.session_state.get('rehber_goster', False):
            st.info("💡 Rehberi kapatmak için yukarıdaki butona tekrar basabilirsiniz. Raporlarınız aşağıda yer almaktadır.")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                with st.expander("📈 İndikatörler ve Temel Metrikler", expanded=True):
                    st.markdown("""
                    - **RSI (Göreceli Güç Endeksi):** 0-100 arası hız ölçer. 30 altı aşırı satım (tepki gelebilir), 70 üstü aşırı alımdır (düzeltme gelebilir).
                    - **MFI (Para Akışı Endeksi):** RSI'ın hacimli versiyonudur. Fiyat artarken MFI artmıyorsa asıl para çıkıyordur. 20 altı aşırı satım, 80 üstü aşırı alımdır.
                    - **ADX (Ortalama Yönsel Endeks):** Trendin gücünü ölçer. 25 üstü güçlü trend, 20 altı yatay/testere piyasasıdır.
                    - **VWAP (Ağırlıklı Ortalama):** Gün içi adil fiyattır. Fiyat VWAP üstündeyse alıcılar baskındır.
                    - **PD/DD:** Şirketin defter değerine göre pahalılığını gösterir. 1-2 makul, 5+ genelde pahalıdır.
                    - **EMA 200:** Uzun vadeli ana trend yönüdür. Fiyat üstündeyse hisse sağlıklıdır.
                    - **Net Borç / FAVÖK:** Borç ödeme kapasitesidir. 3'ün altı güvenli kabul edilir.
                    """)
                    
                with st.expander("📊 Grafikler ve Formasyonlar (Görsel Rehber)", expanded=False):
                    st.markdown("**1. Boğa Piyasası [Bull Market]:** \n Fiyatların merdiven çıkar gibi sürekli yeni zirveler yaptığı, alıcıların iştahlı olduğu bereketli dönem. \"Malda kalma\" zamanıdır.")
                    st.markdown("---")
                    st.markdown("**2. Ayı Piyasası [Bear Market]:** \n Fiyatların asansörle iner gibi sürekli yeni dipler yaptığı, korkunun hakim olduğu dönem. Nakitte bekleme veya açığa satış zamanıdır.")
                    st.markdown("---")
                    st.markdown("**3. İkili Tepe / M Formasyonu [Double Top]:** \n Fiyatın aynı tavanı iki kez yoklayıp kıramamasıdır. \"Buradan ötesi yok, malı boşaltıyorlar\" diyen güçlü bir düşüş sinyalidir.")
                    try: st.image("Görseller/ikili_tepe.jpg")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'ikili_tepe.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**4. İkili Dip / W Formasyonu [Double Bottom]:** \n Fiyatın aynı tabandan iki kez destek bulup sekmesidir. \"Dibi gördük, artık yön yukarı\" diyen güçlü bir yükseliş sinyalidir.")
                    try: st.image("Görseller/ikili_dip.jpg")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'ikili_dip.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**5. Omuz Baş Omuz (OBO) Formasyonu [Head and Shoulders]:** \n Ortada büyük bir zirve (baş), yanlarda daha küçük iki zirve (omuzlar). Yükseliş partisinin bittiğini gösterir, boyun çizgisi aşağı kırılırsa kaçılır.")
                    try: st.image("Görseller/obo.jpg")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'obo.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**6. Ters OBO Formasyonu [Inverse Head and Shoulders]:** \n OBO'nun tepetaklak halidir. Ortada derin bir kuyu, yanlarda sığ iki kuyu. Düşüşün bittiğini ve sağlam bir yükseliş trendinin başlayacağını müjdeler.")
                    try: st.image("Görseller/tobo.jpg")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'tobo.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**7. Kulplu Fincan Formasyonu [Cup and Handle]:** \n Fiyat önce büyük bir çanak (fincan) çizer, sonra küçük bir düzeltme (kulp) yapar. Kulp yukarı kırıldığında, hisse fincanın derinliği kadar yukarı fırlamaya hazırlanır.")
                    try: st.image("Görseller/fincan_kulp.jpg")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'fincan_kulp.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**8. Takoz Formasyonu [Wedge Pattern]:** \n Fiyatın gittikçe daralan bir huniye sıkışmasıdır. Yükselen takoz (Ayı) genelde aşağı doğru patlar, düşen takoz (Boğa) ise yay gibi gerilip yukarı doğru patlar.")
                    try: st.image("Görseller/takoz.png")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'takoz.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**9. Bayrak Formasyonu [Flag Pattern]:** \n Sert bir hareket sonrası dikdörtgen şeklinde kısa bir mola. Direk yukarıysa (Boğa Bayrağı) moladan sonra yükseliş devam eder, direk aşağıysa (Ayı Bayrağı) düşüş devam eder.")
                    try: st.image("Görseller/bayrak.png")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'bayrak.jpg' ekleyin]")
                    st.markdown("---")
                    st.markdown("**10. Flama Formasyonu [Pennant Pattern]:** \n Bayrağın dikdörtgen değil, küçük bir simetrik üçgen halidir. Mantık aynıdır: Sert hareket (direk) -> kısa üçgen mola -> aynı yönde sert kopuş.")
                    try: st.image("Görseller/flama.png")
                    except: st.caption("⚠️ [Görsel Bulunamadı: Lütfen uygulamanın klasörüne 'flama.jpg' ekleyin]")

            with col_r2:
                with st.expander("🎯 Senaryo Sözlüğü", expanded=True):
                    st.markdown("""
                    - **Yay Gevşemesi:** Hisse o kadar çok satıldı ki satacak kimse kalmadı. 'Bedava' diyen alıcılar gelirse yay gibi fırlayabilir.
                    - **Roket Kalkışı:** Hisse rüzgarı arkasına aldı. Güçlü şekilde yükseliyor, trene binmek için son çağrı olabilir.
                    - **Yorgunluk Sinyali:** Zirveye çıktı ama nefesi kesiliyor. Fiyat yükselse de para çıkışı var, iniş başlayabilir.
                    - **Ucuzluk Tuzağı:** Şirket kağıt üzerinde ucuz ama düşüş henüz bitmemiş olabilir. *Düşen bıçak tutulmaz.*
                    - **Güvenli Liman:** Fırtınalı havada sığınılacak yer. Hızlı kazandırmaz ama kolay kolay da kaybettirmez.
                    """)
                    
                with st.expander("💡 Tavsiye Edilen Filtre Stratejileri", expanded=False):
                    st.markdown(
                        "**1. Dip Avcısı (Yüksek Risk):**<br>"
                        "Panikle satılan ucuz hisseler.<br>"
                        "*(RSI: 0–35 | MFI: 0–30 | PD/DD: 0–2 | ADX: 25–100)*<br><br>"
                        "**2. Dengeli Trend (Orta Risk):**<br>"
                        "Arkasına güçlü trend almış istikrarlı hisseler.<br>"
                        "*(RSI: 40–60 | MFI: 35–60 | PD/DD: 0–4 | ADX: 20–50)*<br><br>"
                        "**3. Değer Yatırımcısı (Düşük Risk):**<br>"
                        "Teknik coşkudan ziyade ucuzluğa odaklanır.<br>"
                        "*(RSI: 25–50 | MFI: 25–50 | PD/DD: 0–1.5 | ADX: 15–40)*",
                        unsafe_allow_html=True
                    )
            st.markdown("---")

        nabiz = st.session_state.get('nabiz_hafiza', [])
        if len(nabiz) >= 10:
            ndf = pd.DataFrame(nabiz)
            st.subheader("📡 Piyasa Nabzı")
            n1, n2, n3, n4 = st.columns(4)
            oran = ndf['EMA200 üstü'].mean() * 100
            n1.metric("Taranan hisse", len(ndf))
            n2.metric("EMA200 üstünde", f"%{oran:.0f}")
            n3.metric("Aşırı satım (RSI<30)", f"%{(ndf['RSI'] < 30).mean() * 100:.0f}")
            n4.metric("Aşırı alım (RSI>70)", f"%{(ndf['RSI'] > 70).mean() * 100:.0f}")
            st.caption(f"Piyasa genişliği: {'zayıf' if oran < 30 else ('güçlü' if oran > 70 else 'karışık')} | Yükselen: {(ndf['Günlük %'] > 0).sum()} | Düşen: {(ndf['Günlük %'] < 0).sum()} | Ortalama günlük değişim: %{ndf['Günlük %'].mean():+.2f}")
            t1, t2, t3 = st.columns(3)
            with t1:
                st.markdown("**🚀 En çok yükselen**")
                st.dataframe(ndf.nlargest(5, 'Günlük %')[['Hisse', 'Günlük %']], hide_index=True, use_container_width=True)
            with t2:
                st.markdown("**🔻 En çok düşen**")
                st.dataframe(ndf.nsmallest(5, 'Günlük %')[['Hisse', 'Günlük %']], hide_index=True, use_container_width=True)
            with t3:
                st.markdown("**🔊 Hacim patlaması (son gün / 25 gün ort.)**")
                st.dataframe(ndf.nlargest(5, 'Hacim x')[['Hisse', 'Hacim x']], hide_index=True, use_container_width=True)
            if (ndf['Sektör'] != '').any():
                st.markdown("**🏭 Sektör görünümü**")
                sk = ndf[ndf['Sektör'] != ''].groupby('Sektör').agg(Hisse=('Hisse', 'count'), Gunluk=('Günlük %', 'mean'), Ema=('EMA200 üstü', 'mean'), Rsi=('RSI', 'mean')).reset_index()
                sk['Gunluk'] = sk['Gunluk'].round(2); sk['Ema'] = (sk['Ema'] * 100).round(0); sk['Rsi'] = sk['Rsi'].round(1)
                sk = sk.rename(columns={'Hisse': 'Hisse sayısı', 'Gunluk': 'Ort. günlük %', 'Ema': 'EMA200 üstü %', 'Rsi': 'Ort. RSI'}).sort_values('Ort. günlük %', ascending=False)
                st.dataframe(sk, hide_index=True, use_container_width=True)
            strat = st.session_state.get('strateji_hafiza', [])
            if strat:
                with st.expander("🧪 Strateji Karnesi: bu senaryolar taranan hisselerde son 3 yılda nasıl çalıştı?"):
                    st.dataframe(pd.DataFrame(strat), hide_index=True, use_container_width=True)
                    st.caption("Taranan tüm hisselerin son 3 yıllık verisinde senaryo koşulunun oluştuğu günler (aynı hissede sinyaller arası en az 10 gün) toplanır. 'Piyasa 10g ort.' tüm günlerin ortalamasıdır; 'Fark' sinyalin piyasaya göre avantajıdır. Dikkat: yalnızca bugün listede olan hisseler taranır (batan/çıkan hisseler yok), bu yüzden sonuçlar olduğundan iyi görünebilir. Gelecek için garanti değildir.")
            st.markdown("---")

        hatalilar = st.session_state.get('hatali_hafiza', [])
        if hatalilar:
            with st.expander(f"⚠️ Veri alınamayan hisseler ({len(hatalilar)})", expanded=(len(eslesenler) == 0 and len(hatalilar) <= 5)):
                st.caption("Yahoo Finance veri vermedi, hisse kodu/uzantısı hatalı veya 200 günden kısa işlem geçmişi var.")
                st.write(", ".join(hatalilar))

        if len(eslesenler) == 0:
            st.warning("⚠️ Eşleşme bulunamadı. Çoklu taramada kriterleri esnetmeyi; tekli/izleme modunda hisse kodunu ve uzantısını (örn. THYAO.IS) kontrol etmeyi deneyin.")
        else:
            st.success(f"🎉 Tarama Tamamlandı! {len(eslesenler)} adet eşleşme bulundu.")

            tablo_df = pd.DataFrame([{k: v for k, v in h.items() if k not in ("pdf", "karne", "grafik", "temel")} for h in eslesenler]).rename(columns={"sembol": "Hisse", "uyum": "Uyum %", "kapanis": "Kapanış", "rsi": "RSI", "mfi": "MFI", "adx": "ADX", "pddd": "PD/DD", "trend": "Trend", "gorunum": "Görünüm"})
            tablo_df["Uyum %"] = tablo_df["Uyum %"].round(1)
            st.dataframe(tablo_df, use_container_width=True, hide_index=True)
            st.download_button("📊 Özet Tabloyu CSV İndir", tablo_df.to_csv(index=False).encode("utf-8-sig"), "Borsa_Ozet.csv", "text/csv")

            karneli = [h for h in eslesenler if h.get('karne')]
            if karneli:
                secili_kod = karneli[0]['sembol'] if len(karneli) == 1 else st.selectbox("🧠 Akıllı karne için hisse seç:", [h['sembol'] for h in karneli])
                secili = next(h for h in karneli if h['sembol'] == secili_kod)
                st.markdown(f"### 🧠 {secili_kod} - Akıllı Karne")
                karne_goster(secili['karne'], secili['grafik'], secili_kod, secili['temel'])
                st.markdown("---")
            
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
                with st.expander("🔍 Kısmi Uyum Sağlayan Diğer Hisseler (%50 ve üzeri, eşiğin altında)"):
                    st.info("Bu hisseler senaryoya yaklaşmış ancak henüz tam olgunlaşmamıştır.")
                    bronz_liste.sort(key=lambda x: x['uyum'], reverse=True)
                    for br in bronz_liste:
                        st.markdown(f"- **{br['sembol']}** (Uyum: %{br['uyum']:.1f})")
            if st.button("🏠 Ana Ekrana Dön", use_container_width=True):
                if 'eslesenler_hafiza' in st.session_state: del st.session_state['eslesenler_hafiza']
                if 'bronz_hafiza' in st.session_state: del st.session_state['bronz_hafiza']
                if 'hatali_hafiza' in st.session_state: del st.session_state['hatali_hafiza']
                st.rerun()
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
