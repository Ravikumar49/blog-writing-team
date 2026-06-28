import streamlit as st
from blog_team import app

st.set_page_config(page_title="Multi-Agent Blog Writer", page_icon="✍️", layout="centered")

st.title("✍️ Multi-Agent Blog Writing Team")
st.caption("Supervisor → Researcher → Fact-Checker → Writer, all working together")

# ---- Session state setup ----
if "stage" not in st.session_state:
    st.session_state.stage = "input"   # input -> researched -> done
if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": "blog-session-1"}}

# ---- Stage 1: Topic input ----
if st.session_state.stage == "input":
    topic = st.text_input("Enter a blog topic", placeholder="e.g. The Future of Renewable Energy")

    if st.button("Start Research", use_container_width=True):
        if topic:
            with st.spinner("Researcher and Fact-Checker are working..."):
                result = app.invoke(
                    {"topic": topic, "research": "", "fact_check": "", "draft": "", "next_step": ""},
                    st.session_state.config
                )
            st.session_state.result = result
            st.session_state.stage = "review"
            st.rerun()
        else:
            st.warning("Please enter a topic first.")

# ---- Stage 2: Review research + fact-check, allow editing ----
elif st.session_state.stage == "review":
    result = st.session_state.result

    st.markdown("### 📋 Research Notes")
    st.markdown(result["research"])

    st.markdown("### ✅ Fact-Check Report")
    st.markdown(result.get("fact_check", "No fact-check available."))

    st.markdown("---")
    st.markdown("### Want to edit the research before writing?")
    edited_research = st.text_area(
        "Edit research notes (optional)",
        value=result["research"],
        height=200
    )

    if st.button("Approve & Write Blog Post", use_container_width=True):
        if edited_research != result["research"]:
            app.update_state(st.session_state.config, {"research": edited_research})

        with st.spinner("Writer is drafting the blog post..."):
            final_result = app.invoke(None, st.session_state.config)

        st.session_state.final_result = final_result
        st.session_state.stage = "done"
        st.rerun()

# ---- Stage 3: Final blog post ----
elif st.session_state.stage == "done":
    st.markdown("### 📝 Final Blog Post")
    st.markdown(st.session_state.final_result["draft"])

    if st.button("Write Another Post", use_container_width=True):
        st.session_state.stage = "input"
        st.rerun()