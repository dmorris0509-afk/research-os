import streamlit as st

from research_os.integrations.github.errors import GitHubIntegrationError
from research_os.integrations.github.factory import create_github_client
from research_os.integrations.github.importer import GitHubRepositoryImporter

st.set_page_config(page_title="GitHub · Research OS", page_icon="🔗", layout="wide")
st.title("Connect GitHub")
st.write("Import repository metadata, README content, Issues, and Pull Requests into Research OS.")

repository = st.text_input("Repository", placeholder="owner/repository")
if st.button("Import repository", type="primary", disabled=not repository.strip()):
    try:
        with st.spinner("Importing GitHub evidence…"):
            snapshot = GitHubRepositoryImporter(create_github_client()).import_repository(repository)
        st.success(f"Connected {snapshot.full_name}")
        left, middle, right = st.columns(3)
        left.metric("Stars", snapshot.repository.get("stargazers_count", 0))
        middle.metric("Issues", len(snapshot.issues))
        right.metric("Pull requests", len(snapshot.pull_requests))
        with st.expander("README", expanded=True):
            st.markdown(snapshot.readme or "No README found.")
        with st.expander("Issues"):
            for issue in snapshot.issues:
                st.markdown(f"- [#{issue['number']} {issue['title']}]({issue['html_url']})")
        with st.expander("Pull requests"):
            for pull in snapshot.pull_requests:
                st.markdown(f"- [#{pull['number']} {pull['title']}]({pull['html_url']})")
        st.info(
            "Persistence is delegated to GitHubImportSink so this page can bind to the existing "
            "Research OS service layer after it is pushed."
        )
    except (ValueError, GitHubIntegrationError) as exc:
        st.error(str(exc))
