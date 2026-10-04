
import os
import io
import hashlib
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Rodaserv | Control de Referencias", page_icon="📦", layout="wide")

# -----------------------------
# CONFIG / STORAGE
# -----------------------------
USERS_DEFAULT = {
    "admin": {"password": "admin123", "role": "Administrador", "name": "Administrador"},
    "bodega": {"password": "bodega123", "role": "Bodega", "name": "Bodega"},
    "vendedor1": {"password": "vendor1", "role": "Vendedor", "name": "Vendedor 1"},
    "vendedor2": {"password": "vendor2", "role": "Vendedor", "name": "Vendedor 2"},
    "vendedor3": {"password": "vendor3", "role": "Vendedor", "name": "Vendedor 3"},
}

COLS = [
    "ID","Fecha reporte","Hora reporte","Usuario","Tipo","Referencia","Marca",
    "Aplicación","Cantidad sugerida","Cliente","Observaciones",
    "Estado","Fecha actualización","Usuario actualización","Comentario validación"
]

STATUSES = ["Reportado","En revisión","Validado","Gestión de compra","Solucionado","Descartado"]

def hash_pw(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def load_users():
    # Optional Streamlit secrets format:
    # [users.admin]
    # password = "..."
    # role = "Administrador"
    # name = "..."
    users = {}
    try:
        if "users" in st.secrets:
            for u, data in st.secrets["users"].items():
                users[u] = {
                    "password": str(data["password"]),
                    "role": str(data.get("role","Vendedor")),
                    "name": str(data.get("name",u))
                }
    except Exception:
        pass
    return users or USERS_DEFAULT

def google_sheet_enabled():
    try:
        return "gcp_service_account" in st.secrets and "spreadsheet_id" in st.secrets
    except Exception:
        return False

@st.cache_resource
def get_gspread_client():
    import gspread
    from google.oauth2.service_account import Credentials
    info = dict(st.secrets["gcp_service_account"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

def get_worksheet():
    gc = get_gspread_client()
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    try:
        ws = sh.worksheet(st.secrets.get("worksheet_name","REPORTES"))
    except Exception:
        ws = sh.add_worksheet(title=st.secrets.get("worksheet_name","REPORTES"), rows=2000, cols=len(COLS))
        ws.append_row(COLS)
    values = ws.get_all_values()
    if not values:
        ws.append_row(COLS)
        values=[COLS]
    if values[0] != COLS:
        # Keep existing sheet readable; do not overwrite data automatically.
        pass
    return ws

def local_path():
    return "reportes_roda.csv"

def load_data():
    if google_sheet_enabled():
        ws=get_worksheet()
        values=ws.get_all_values()
        if len(values)<=1:
            return pd.DataFrame(columns=COLS)
        df=pd.DataFrame(values[1:], columns=values[0])
        for c in COLS:
            if c not in df.columns: df[c]=""
        return df[COLS]
    if os.path.exists(local_path()):
        df=pd.read_csv(local_path(), dtype=str).fillna("")
        for c in COLS:
            if c not in df.columns: df[c]=""
        return df[COLS]
    return pd.DataFrame(columns=COLS)

def save_row(row):
    if google_sheet_enabled():
        get_worksheet().append_row([str(row.get(c,"")) for c in COLS], value_input_option="USER_ENTERED")
    else:
        df=load_data()
        df=pd.concat([df,pd.DataFrame([[row.get(c,"") for c in COLS]], columns=COLS)], ignore_index=True)
        df.to_csv(local_path(), index=False, encoding="utf-8-sig")

def update_row(row_id, changes):
    if google_sheet_enabled():
        ws=get_worksheet()
        vals=ws.get_all_values()
        if not vals: return False
        headers=vals[0]
        if "ID" not in headers: return False
        id_col=headers.index("ID")+1
        for r in range(2,len(vals)+1):
            if str(vals[r-1][id_col-1]) == str(row_id):
                for k,v in changes.items():
                    if k in headers:
                        ws.update_cell(r, headers.index(k)+1, str(v))
                return True
        return False
    df=load_data()
    idx=df.index[df["ID"].astype(str)==str(row_id)].tolist()
    if not idx: return False
    i=idx[0]
    for k,v in changes.items():
        if k in df.columns: df.loc[i,k]=v
    df.to_csv(local_path(), index=False, encoding="utf-8-sig")
    return True

def new_id():
    return datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

# -----------------------------
# LOGIN
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user=None

if not st.session_state.user:
    st.markdown("# 📦 RODASERV")
    st.markdown("### Control de agotados y referencias nuevas")
    st.caption("Versión móvil para equipo comercial, bodega y administración.")
    with st.form("login"):
        u=st.text_input("Usuario")
        p=st.text_input("Contraseña", type="password")
        ok=st.form_submit_button("Ingresar", use_container_width=True)
    if ok:
        users=load_users()
        if u in users and (p==users[u]["password"] or hash_pw(p)==users[u]["password"]):
            st.session_state.user={"username":u, **users[u]}
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.info("Usuarios demo: admin/admin123 · bodega/bodega123 · vendedor1/vendor1 · vendedor2/vendor2 · vendedor3/vendor3")
    st.stop()

user=st.session_state.user

# -----------------------------
# HEADER
# -----------------------------
st.sidebar.markdown("## 📦 RODASERV")
st.sidebar.write(f"**{user['name']}**")
st.sidebar.caption(user["role"])
if st.sidebar.button("Cerrar sesión", use_container_width=True):
    st.session_state.user=None
    st.rerun()

page=st.sidebar.radio("Menú", ["📊 Dashboard","➕ Nuevo reporte","🔎 Buscar / gestionar","📋 Seguimiento","📥 Exportar"])

df=load_data()
if not df.empty:
    df["Fecha reporte"]=df["Fecha reporte"].astype(str)
    df["Estado"]=df["Estado"].astype(str)

# -----------------------------
# DASHBOARD
# -----------------------------
if page=="📊 Dashboard":
    st.title("📊 Dashboard de avance")
    if df.empty:
        st.warning("Aún no hay reportes.")
        st.stop()

    total=len(df)
    agot=(df["Tipo"]=="Agotado").sum()
    nuevas=(df["Tipo"]=="Referencia nueva").sum()
    solved=(df["Estado"]=="Solucionado").sum()
    pending=total-solved-(df["Estado"]=="Descartado").sum()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Total reportes",total)
    c2.metric("Agotados",agot)
    c3.metric("Referencias nuevas",nuevas)
    c4.metric("Pendientes",pending)

    st.subheader("Estado general")
    status_counts=df["Estado"].value_counts().reindex(STATUSES, fill_value=0)
    st.bar_chart(status_counts)

    st.subheader("Avance por tipo")
    t=df.groupby(["Tipo","Estado"]).size().reset_index(name="Cantidad")
    st.dataframe(t, use_container_width=True, hide_index=True)

    if user["role"] in ["Administrador","Bodega"]:
        st.subheader("Carga por usuario")
        by_user=df.groupby("Usuario").size().sort_values(ascending=False)
        st.bar_chart(by_user)

# -----------------------------
# NEW REPORT
# -----------------------------
elif page=="➕ Nuevo reporte":
    st.title("➕ Registrar reporte")
    st.caption("Diseñado para diligenciar rápidamente desde celular.")
    with st.form("new_report", clear_on_submit=True):
        tipo=st.radio("Tipo de reporte",["Agotado","Referencia nueva"], horizontal=True)
        ref=st.text_input("Referencia *", placeholder="Ej.: 6205-2RS-C3")
        marca=st.text_input("Marca", placeholder="PFI / NSK / KOYO / SKF...")
        aplic=st.text_input("Aplicación", placeholder="Vehículo, máquina, modelo o uso")
        qty=st.number_input("Cantidad sugerida", min_value=0, value=1, step=1)
        cliente=st.text_input("Cliente / oportunidad", placeholder="Opcional")
        obs=st.text_area("Observaciones", placeholder="¿Por qué se reporta? ¿Qué necesita el cliente?")
        enviar=st.form_submit_button("🚀 ENVIAR REPORTE", use_container_width=True)
    if enviar:
        if not ref.strip():
            st.error("La referencia es obligatoria.")
        else:
            now=datetime.now()
            row={
                "ID":new_id(),"Fecha reporte":now.strftime("%Y-%m-%d"),
                "Hora reporte":now.strftime("%H:%M:%S"),"Usuario":user["name"],
                "Tipo":tipo,"Referencia":ref.strip().upper(),"Marca":marca.strip().upper(),
                "Aplicación":aplic.strip(),"Cantidad sugerida":qty,"Cliente":cliente.strip(),
                "Observaciones":obs.strip(),"Estado":"Reportado",
                "Fecha actualización":now.strftime("%Y-%m-%d %H:%M:%S"),
                "Usuario actualización":user["name"],"Comentario validación":""
            }
            save_row(row)
            st.success(f"Reporte guardado: {row['Referencia']}")
            st.balloons()

# -----------------------------
# SEARCH / MANAGE
# -----------------------------
elif page=="🔎 Buscar / gestionar":
    st.title("🔎 Buscar y gestionar referencias")
    if df.empty:
        st.info("No hay reportes.")
        st.stop()

    q=st.text_input("Buscar referencia, marca, cliente o aplicación", "")
    f_tipo=st.multiselect("Tipo",["Agotado","Referencia nueva"], default=[])
    f_estado=st.multiselect("Estado",STATUSES, default=[])
    f_user=st.multiselect("Usuario",sorted(df["Usuario"].unique().tolist()), default=[])

    view=df.copy()
    if q:
        mask=view.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)
        view=view[mask]
    if f_tipo: view=view[view["Tipo"].isin(f_tipo)]
    if f_estado: view=view[view["Estado"].isin(f_estado)]
    if f_user: view=view[view["Usuario"].isin(f_user)]

    st.caption(f"{len(view)} resultado(s)")
    st.dataframe(view[["ID","Fecha reporte","Usuario","Tipo","Referencia","Marca","Aplicación","Estado","Cliente"]], use_container_width=True, hide_index=True)

    if user["role"] in ["Administrador","Bodega"] and len(view):
        st.subheader("Actualizar estado")
        ids=view["ID"].astype(str).tolist()
        selected=st.selectbox("Seleccione reporte",ids)
        rec=view[view["ID"].astype(str)==selected].iloc[0]
        st.write(f"**{rec['Referencia']}** · {rec['Tipo']} · reportado por {rec['Usuario']}")
        new_status=st.selectbox("Nuevo estado",STATUSES, index=STATUSES.index(rec["Estado"]) if rec["Estado"] in STATUSES else 0)
        comment=st.text_area("Comentario de validación / avance", value=str(rec["Comentario validación"]))
        if st.button("💾 Guardar avance", use_container_width=True):
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_row(selected,{
                "Estado":new_status,
                "Fecha actualización":now,
                "Usuario actualización":user["name"],
                "Comentario validación":comment
            })
            st.success("Estado actualizado.")
            st.rerun()

# -----------------------------
# TRACKING
# -----------------------------
elif page=="📋 Seguimiento":
    st.title("📋 Seguimiento de avance")
    if df.empty:
        st.info("No hay información.")
        st.stop()

    refq=st.text_input("Escriba una referencia para ver su estado")
    if refq:
        r=df[df["Referencia"].astype(str).str.contains(refq,case=False,na=False)]
        if r.empty: st.warning("No encontrada.")
        else:
            for _,x in r.iterrows():
                st.markdown(f"### {x['Referencia']} · {x['Tipo']}")
                st.progress((STATUSES.index(x["Estado"])+1)/len(STATUSES) if x["Estado"] in STATUSES else 0)
                a,b,c=st.columns(3)
                a.metric("Estado",x["Estado"])
                b.metric("Reportado por",x["Usuario"])
                c.metric("Última actualización",x["Fecha actualización"])
                st.write(f"**Marca:** {x['Marca']}  \n**Aplicación:** {x['Aplicación']}  \n**Cliente:** {x['Cliente']}  \n**Observaciones:** {x['Observaciones']}  \n**Validación:** {x['Comentario validación']}")
    else:
        resumen=df.groupby(["Referencia","Tipo","Estado"]).size().reset_index(name="Reportes")
        st.dataframe(resumen.sort_values("Estado"), use_container_width=True, hide_index=True)

# -----------------------------
# EXPORT
# -----------------------------
elif page=="📥 Exportar":
    st.title("📥 Reportes")
    if df.empty:
        st.info("No hay datos para exportar.")
        st.stop()

    st.dataframe(df, use_container_width=True, hide_index=True)
    xls=io.BytesIO()
    with pd.ExcelWriter(xls, engine="openpyxl") as writer:
        df.to_excel(writer,index=False,sheet_name="REPORTES")
        df[df["Estado"]!="Solucionado"].to_excel(writer,index=False,sheet_name="PENDIENTES")
        df[df["Tipo"]=="Agotado"].to_excel(writer,index=False,sheet_name="AGOTADOS")
        df[df["Tipo"]=="Referencia nueva"].to_excel(writer,index=False,sheet_name="NUEVAS")
    st.download_button("⬇️ Descargar Excel completo", xls.getvalue(), "Rodaserv_Control_Referencias.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    csv=df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Descargar CSV",csv,"Rodaserv_Control_Referencias.csv","text/csv",use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("RODASERV · Control de agotados y referencias nuevas")
st.sidebar.caption("Backend: Google Sheets (equipo) o CSV local (pruebas).")
