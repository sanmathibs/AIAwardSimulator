"""
AI Award Interpreter - Streamlit App
"""

import streamlit as st
import json
from pathlib import Path
import sys
import traceback


# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.orchestrator import Orchestrator


# Page config
st.set_page_config(
    page_title=config.APP_TITLE, page_icon=config.APP_ICON, layout="wide"
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-header {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .cost-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .success-badge {
        background-color: #00cc00;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state"""
    print("Initializing session state...")
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "award_data" not in st.session_state:
        st.session_state.award_data = None
    if "award_spec" not in st.session_state:
        st.session_state.award_spec = None
    if "gap_report" not in st.session_state:
        st.session_state.gap_report = None
    if "outputs" not in st.session_state:
        st.session_state.outputs = None
    if "step" not in st.session_state:
        st.session_state.step = 1


def main():
    init_session_state()

    # Header
    st.markdown(
        f"<h1 class='main-header'>{config.APP_ICON} {config.APP_TITLE}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #666;'>From Fair Work Awards to system-ready configurations in minutes!</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Step 1: Award Input
    st.markdown(
        "<div class='step-header'><h2>📝 Step 1: Award Input</h2></div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([4, 1])

    with col1:
        award_url = st.text_input(
            "Award URL",
            placeholder="https://awards.fairwork.gov.au/MA000028.html",
            help="Enter the full URL to the Fair Work award page",
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_button = st.button(
            "🚀 Start Analysis", type="primary", use_container_width=True
        )

    if start_button and award_url:
        if not award_url.startswith("http"):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            print("Starting new analysis session...")
            # Initialize orchestrator with selected generator
            st.session_state.orchestrator = Orchestrator(use_llm_generator=True)
            st.session_state.session_id = st.session_state.orchestrator.start_session(
                award_url
            )
            st.session_state.step = 2
            st.rerun()

    # Step 2: Processing
    if st.session_state.step >= 2:
        st.markdown(
            "<div class='step-header'><h2>⚙️ Step 2: Processing</h2></div>",
            unsafe_allow_html=True,
        )
        print("Processing step started...")
        orchestrator: Orchestrator = st.session_state.orchestrator

        with st.status("Processing award...", expanded=True) as status:
            # Fetch and parse
            if st.session_state.award_data is None:
                st.write("🔍 Fetching award document...")
                try:
                    award_data = orchestrator.fetch_and_parse()
                    st.session_state.award_data = award_data
                    st.write(f"✅ Fetched: {award_data['award_name']}")
                    st.write(f"✅ Parsed {award_data['clauses_count']} clauses")
                except Exception as e:
                    st.error(f"Error fetching award: {str(e)}")
                    status.update(label="❌ Processing failed", state="error")
                    return

            # Create vector store
            st.write("📦 Creating vector store...")
            try:
                print("Creating vector store for wards...")
                vector_result = orchestrator.create_vector_store(
                    st.session_state.award_data["clauses"]
                )
                st.write(
                    f"✅ Embedded {vector_result['count']} clauses (${vector_result['cost']:.4f})"
                )
            except Exception as e:
                st.error(f"Error creating vector store: {str(e)}")
                status.update(label="❌ Processing failed", state="error")
                return

            # Extract rules
            if st.session_state.award_spec is None:
                st.write("🔬 Extracting rules...")
                try:
                    print("Extracting rules...")
                    award_spec = orchestrator.extract_rules(
                        st.session_state.award_data["award_name"],
                    )
                    st.session_state.award_spec = award_spec
                    st.write("✅ Extracted ordinary hours")
                    st.write("✅ Extracted overtime rules")
                    st.write("✅ Extracted weekend penalties")
                    st.write("✅ Extracted public holiday rules")
                    st.write("✅ Extracted break rules")
                    st.write("✅ Extracted allowances")
                except Exception as e:
                    # print traceback
                    traceback.print_exc()
                    st.error(f"Error extracting rules: {str(e)}")
                    status.update(label="❌ Processing failed", state="error")
                    return

            status.update(label="✅ Processing complete", state="complete")

        # Only advance to step 3 if we're still on step 2
        if st.session_state.step == 2:
            st.session_state.step = 3

    # Step 3: Gap Analysis
    if st.session_state.step >= 3:
        st.markdown(
            "<div class='step-header'><h2>📊 Step 3: Gap Analysis</h2></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.gap_report is None:
            with st.spinner("Analyzing gaps..."):
                try:
                    print("Analyzing gaps...")
                    orchestrator: Orchestrator = st.session_state.orchestrator
                    gap_report = orchestrator.analyze_gaps(st.session_state.award_spec)
                    st.session_state.gap_report = gap_report
                except Exception as e:
                    st.error(f"Error analyzing gaps: {str(e)}")
                    return

        gap_report = st.session_state.gap_report

        # Display summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Gaps", gap_report.summary["total_gaps"])
        with col2:
            st.metric("Config Only", gap_report.summary["config_only"])
        with col3:
            st.metric("Code Required", gap_report.summary["code_required"])
        with col4:
            st.metric("Ambiguous", gap_report.summary["ambiguous"])

        # Show gaps details
        if gap_report.summary["total_gaps"] > 0:
            tab1, tab2, tab3 = st.tabs(
                ["Config-Only Gaps", "Code-Required Gaps", "Ambiguous Items"]
            )

            with tab1:
                if gap_report.gaps["config_only"]:
                    for gap in gap_report.gaps["config_only"]:
                        with st.expander(f"[{gap.severity.upper()}] {gap.description}"):
                            st.write(f"**Category**: {gap.category}")
                            st.write(f"**Current Value**: {gap.current_value}")
                            st.write(f"**Required Value**: {gap.required_value}")
                            if gap.json_path:
                                st.write(f"**JSON Path**: `{gap.json_path}`")
                            if gap.clause_reference:
                                st.write(
                                    f"**Clause Reference**: {gap.clause_reference}"
                                )
                else:
                    st.info("No config-only gaps found.")

            with tab2:
                if gap_report.gaps["code_required"]:
                    for gap in gap_report.gaps["code_required"]:
                        with st.expander(f"[{gap.severity.upper()}] {gap.description}"):
                            st.write(f"**Category**: {gap.category}")
                            if gap.affected_functions:
                                st.write(
                                    f"**Affected Functions**: {', '.join(gap.affected_functions)}"
                                )
                            if gap.clause_reference:
                                st.write(
                                    f"**Clause Reference**: {gap.clause_reference}"
                                )
                else:
                    st.success("✅ No code changes required!")

            with tab3:
                if gap_report.gaps["ambiguous"]:
                    st.warning("The following items need clarification:")
                    for idx, gap in enumerate(gap_report.gaps["ambiguous"]):
                        st.write(f"### Ambiguity #{idx + 1}: {gap.description}")
                        if gap.clause_text:
                            st.info(gap.clause_text)
                        if gap.possible_interpretations:
                            selected = st.radio(
                                "Select interpretation:",
                                gap.possible_interpretations,
                                key=f"ambiguity_{gap.gap_id}",
                            )
                            if st.session_state.orchestrator.session:
                                st.session_state.orchestrator.session.ambiguities_resolved[
                                    gap.gap_id
                                ] = selected
                        st.markdown("---")
                else:
                    st.success("No ambiguous items found.")

        if st.button("📦 Generate Outputs", type="primary"):
            print("Generating outputs...")
            st.session_state.step = 4
            st.rerun()

    # Step 4: Outputs
    if st.session_state.step >= 4:
        st.markdown(
            "<div class='step-header'><h2>📄 Step 4: Review & Download</h2></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.outputs is None:
            with st.spinner("Generating outputs..."):
                try:
                    print("Generating final outputs...")
                    orchestrator: Orchestrator = st.session_state.orchestrator
                    outputs = orchestrator.generate_outputs(
                        st.session_state.award_spec, st.session_state.gap_report
                    )
                    st.session_state.outputs = outputs
                except Exception as e:
                    # print traceback
                    traceback.print_exc()
                    st.error(f"Error generating outputs: {str(e)}")
                    return

        st.success("✅ All artifacts generated successfully!")

        # Display cost
        total_cost = st.session_state.orchestrator.get_session_cost()
        st.markdown(
            f"<p style='text-align: center;'>💰 Total Cost: <span class='cost-badge'>${total_cost:.4f}</span></p>",
            unsafe_allow_html=True,
        )

        # Preview tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📄 JSON Config", "🔧 Patch Plan", "📊 Gap Report", "📚 Award Spec"]
        )

        with tab1:
            config_path = Path(st.session_state.outputs["config_path"])
            config_data = json.loads(config_path.read_text())
            st.json(config_data)

            st.download_button(
                label="⬇️ Download JSON Config",
                data=json.dumps(config_data, indent=2),
                file_name=f"{st.session_state.award_data['award_id']}_config.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab2:
            patch_path = Path(st.session_state.outputs["patch_plan_path"])
            patch_content = patch_path.read_text(encoding="utf-8")
            st.markdown(patch_content)

            st.download_button(
                label="⬇️ Download Patch Plan",
                data=patch_content,
                file_name=f"{st.session_state.award_data['award_id']}_patch_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with tab3:
            gap_path = Path(
                st.session_state.orchestrator.session.artifacts["gap_report_path"]
            )
            gap_data = json.loads(gap_path.read_text())
            st.json(gap_data)

            st.download_button(
                label="⬇️ Download Gap Report",
                data=json.dumps(gap_data, indent=2),
                file_name=f"{st.session_state.award_data['award_id']}_gap_report.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab4:
            spec_path = Path(
                st.session_state.orchestrator.session.artifacts["award_spec_path"]
            )
            spec_data = json.loads(spec_path.read_text())
            st.json(spec_data)

            st.download_button(
                label="⬇️ Download Award Spec",
                data=json.dumps(spec_data, indent=2),
                file_name=f"{st.session_state.award_data['award_id']}_award_spec.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Process Another Award", use_container_width=True):
                # Reset session
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


if __name__ == "__main__":
    main()
