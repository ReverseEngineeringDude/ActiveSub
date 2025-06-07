import streamlit as st
import asyncio
import httpx
import tempfile

# Page setup
st.set_page_config(page_title="Subdomain Scanner", layout="wide")
st.title("🌐 Ultra-Fast Subdomain Scanner")

# Init session state
if "stop_scan" not in st.session_state:
    st.session_state.stop_scan = False
if "results" not in st.session_state:
    st.session_state.results = {"active": [], "not_found": []}
if "completed" not in st.session_state:
    st.session_state.completed = 0

def reset_session():
    st.session_state.stop_scan = False
    st.session_state.results = {"active": [], "not_found": []}
    st.session_state.completed = 0

# Upload section
uploaded_file = st.file_uploader("📄 Upload subdomain list (.txt)", type=["txt"], on_change=reset_session)

# Async Scanner Logic
MAX_CONCURRENCY = 50
semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

async def fetch(client, subdomain, update_progress, results):
    if st.session_state.stop_scan:
        return
    url = f"https://{subdomain}/"
    try:
        async with semaphore:
            r = await client.get(url, timeout=5)
            if r.status_code == 200:
                results["active"].append(subdomain)
                update_progress(subdomain, 200)
            elif r.status_code == 404:
                results["not_found"].append(subdomain)
                update_progress(subdomain, 404)
            else:
                update_progress(subdomain, r.status_code)
    except Exception:
        update_progress(subdomain, "error")

async def scan_subdomains(subdomains, update_progress):
    results = {"active": [], "not_found": []}
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [fetch(client, sub, update_progress, results) for sub in subdomains]
        await asyncio.gather(*tasks)
    return results

# Main logic
if uploaded_file:
    subdomains = uploaded_file.read().decode("utf-8").splitlines()
    total = len(subdomains)
    progress_bar = st.progress(0, text="Ready to start...")
    status_area = st.empty()

    def update_progress(subdomain, status_code):
        st.session_state.completed += 1
        percent = st.session_state.completed / total
        progress_bar.progress(percent, text=f"{st.session_state.completed}/{total} scanned")

        status_message = f"[`{subdomain}`](https://{subdomain}) — **{status_code}**"
        if status_code == 200:
            status_area.markdown(f"✅ {status_message}", unsafe_allow_html=True)
        elif status_code == 404:
            status_area.markdown(f"⚠️ {status_message}", unsafe_allow_html=True)
        elif status_code == "error":
            status_area.markdown(f"❌ `{subdomain}` — Request Failed", unsafe_allow_html=True)
        else:
            status_area.markdown(f"🔵 {status_message}", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    if col1.button("🚀 Start Scan"):
        st.session_state.stop_scan = False
        st.session_state.results = asyncio.run(scan_subdomains(subdomains, update_progress))
        progress_bar.progress(1.0, text="✅ Scan Completed")
        st.success("Scan completed!")

    if col2.button("⛔ Stop Scan"):
        st.session_state.stop_scan = True
        st.warning("Scan stopped.")

# Display Results with Copy + Links
if st.session_state.results["active"] or st.session_state.results["not_found"]:
    st.subheader("📊 Scan Results")
    tabs = st.tabs(["✅ 200 OK", "⚠️ 404 Not Found"])

    def display_result(result_list, label):
        if result_list:
            # Copy All
            copy_all = "\n".join(result_list)
            st.code(copy_all, language="bash")

            st.download_button(f"📥 Download {label}.txt", copy_all, file_name=f"{label}.txt")

            for sub in result_list:
                col1, col2 = st.columns([0.9, 0.1])
                col1.markdown(f"<a href='https://{sub}' target='_blank'>{sub}</a>", unsafe_allow_html=True)
                col2.code(sub, language="text")
        else:
            st.info(f"No {label} subdomains found.")

    with tabs[0]:
        st.markdown("### ✅ Active Subdomains")
        display_result(st.session_state.results["active"], "200")

    with tabs[1]:
        st.markdown("### ⚠️ Not Found Subdomains")
        display_result(st.session_state.results["not_found"], "404")
