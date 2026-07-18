import streamlit as st

st.set_page_config(page_title="Research OS", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg, #07111f 0%, #0b1728 55%, #0d1e32 100%);}
    [data-testid="stSidebar"] {background: #081321; border-right: 1px solid #1d344d;}
    .hero {padding: 1.8rem 2rem; border: 1px solid #23415f; border-radius: 18px;
           background: linear-gradient(120deg, rgba(20,54,82,.9), rgba(9,29,48,.92)); margin-bottom: 1.2rem;}
    .eyebrow {color:#5eead4; font-size:.78rem; font-weight:700; letter-spacing:.16em;
              text-transform:uppercase;}
    .hero h1 {font-size:2.55rem; margin:.3rem 0; color:#f4f8fc;}
    .hero p {font-size:1.08rem; color:#b7c9da; max-width:780px; margin:0;}
    .status {display:inline-block; margin-top:1rem; padding:.32rem .72rem; border-radius:99px;
             color:#8ff4df; background:#123c3b; border:1px solid #236b64; font-size:.82rem;}
    div[data-testid="stMetric"] {background:#0d2033; border:1px solid #203c57; padding:1rem;
                                 border-radius:14px; min-height:118px;}
    div[data-testid="stMetricValue"] {color:#f7fbff;}
    .stage {padding:1rem; background:#0c1c2c; border:1px solid #203a53; border-radius:12px; min-height:122px;}
    .stage-num {color:#5eead4; font-weight:800; font-size:.75rem; letter-spacing:.12em;}
    .stage-title {color:#f1f7fb; font-weight:700; margin:.25rem 0;}
    .stage-copy {color:#9fb4c6; font-size:.86rem;}
    .receipt {font-family:monospace; color:#b8cce0; background:#07101c; border:1px solid #29435d;
              border-radius:12px; padding:1rem 1.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("## ◈ Research OS")
st.sidebar.caption("Constitutional research engine")
page = st.sidebar.radio(
    "Workspace",
    ["Command Center", "Evidence", "Analysis", "Verification", "Publication"],
)
st.sidebar.divider()
st.sidebar.caption("AI PROVIDER")
st.sidebar.markdown("**OpenAI · GPT-5.6**")
st.sidebar.caption("Provider-neutral runtime")
st.sidebar.divider()
st.sidebar.success("API healthy · lineage verified")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Evidence-first AI research</div>
      <h1>Research OS</h1>
      <p>Turn approved sources into inspectable evidence, claims, verification, and publication—without
      losing the chain of reasoning that makes research trustworthy.</p>
      <div class="status">● VERIFIED SAMPLE WORKSPACE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Command Center":
    st.caption("AI Tutor Adoption Review · sample lineage generated from the verified backend test scenario")
    a, b, c, d = st.columns(4)
    a.metric("Approved sources", "4", "GitHub + studies")
    b.metric("Evidence records", "12", "100% sourced")
    c.metric("Verified claims", "5 / 6", "1 inconclusive")
    d.metric("Receipt integrity", "SHA-256", "Matched")

    st.markdown("### Governed research workflow")
    stages = [
        ("01", "Question", "Intent and scope captured"),
        ("02", "Sources", "Project allow-list enforced"),
        ("03", "Evidence", "Typed excerpts extracted"),
        ("04", "Claims", "Support mapped explicitly"),
        ("05", "Verify", "Verdicts and limits recorded"),
        ("06", "Publish", "Report + receipt committed"),
    ]
    columns = st.columns(6)
    for column, (number, title, copy) in zip(columns, stages, strict=True):
        column.markdown(
            f'<div class="stage"><div class="stage-num">{number}</div><div class="stage-title">{title}</div>'
            f'<div class="stage-copy">{copy}</div></div>',
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.6, 1])
    with left:
        st.markdown("### Evidence coverage")
        st.progress(0.92, text="92% of claims have direct multi-source support")
        st.progress(0.83, text="83% of claims passed verification")
        st.info("One claim remains inconclusive because the approved sources do not establish causality.")
    with right:
        st.markdown("### Constitutional controls")
        st.write("✓ Provider and model allow-list")
        st.write("✓ Source ownership boundary")
        st.write("✓ Atomic transaction rollback")
        st.write("✓ Required limitations")

elif page == "Evidence":
    st.markdown("## Evidence organization")
    st.caption("Each record retains its project, source, extraction type, and relevance metadata.")
    st.dataframe(
        [
            {"ID": "E-104", "Source": "Study A", "Kind": "finding", "Relevance": 0.96, "Status": "Grounded"},
            {
                "ID": "E-105",
                "Source": "GitHub README",
                "Kind": "implementation",
                "Relevance": 0.93,
                "Status": "Grounded",
            },
            {
                "ID": "E-106",
                "Source": "Issue #18",
                "Kind": "limitation",
                "Relevance": 0.88,
                "Status": "Grounded",
            },
            {"ID": "E-107", "Source": "Study B", "Kind": "finding", "Relevance": 0.85, "Status": "Grounded"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.warning(
        "Research OS rejects model output that cites a source outside the approved project source set."
    )

elif page == "Analysis":
    st.markdown("## Claim analysis")
    st.caption("Findings stay connected to the evidence records that support them.")
    with st.container(border=True):
        st.markdown("**Claim C-204 · AI tutoring may improve targeted practice outcomes.**")
        st.write("Evidence: E-104, E-107 · Method: provider-structured-synthesis · Confidence: 0.91")
        st.success("Supported by two approved sources")
    with st.container(border=True):
        st.markdown("**Claim C-205 · Results generalize to every classroom environment.**")
        st.write("Evidence: E-106 · Method: provider-structured-synthesis · Confidence: 0.48")
        st.warning("Inconclusive · available evidence does not establish generalizability")

elif page == "Verification":
    st.markdown("## Verification and lineage")
    st.caption(
        "The event timeline reconstructs what happened, in order, without overstating deterministic replay."
    )
    events = [
        ("09:41:02", "CONSTITUTIONAL_EXECUTION_STARTED", "Provider, model, and source set authorized"),
        ("09:41:03", "EVIDENCE_EXTRACTED", "12 evidence records persisted"),
        ("09:41:03", "CLAIM_GENERATED", "6 claims mapped to evidence"),
        ("09:41:04", "CLAIM_VERIFIED", "5 pass · 1 inconclusive"),
        ("09:41:04", "REPORT_PUBLISHED", "Publication P-031 created"),
        ("09:41:04", "RESEARCH_RECEIPT_ISSUED", "Report hash recorded"),
    ]
    for timestamp, event, detail in events:
        st.markdown(f"`{timestamp}` **{event}**  \n{detail}")

else:
    st.markdown("## Final generated research output")
    st.caption("Publication P-031 · AI Tutor Adoption Review")
    st.markdown(
        """
        ### Executive finding
        The approved evidence supports targeted use of AI tutoring for structured practice, with meaningful
        limitations around classroom context, accessibility, and long-term outcomes.

        ### Recommendation
        Proceed with a measured pilot that includes educator oversight, outcome monitoring, and an explicit
        review checkpoint before broader adoption.

        ### Limitations
        The supplied sources do not establish universal generalizability or long-term causal impact.
        """
    )
    st.markdown(
        """
        <div class="receipt">EXECUTION  94d2…8f31<br>PROVIDER   openai<br>MODEL      gpt-5.6<br>
        WORKFLOW   1.0.0<br>REPORT     sha256: 6fa1c0d8…a55e<br>INTEGRITY  MATCHED</div>
        """,
        unsafe_allow_html=True,
    )
