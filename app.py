import streamlit as st
import time
import sys
from scraper import scrape_problem
from agent import get_ai_solution, extract_code, get_second_opinion
from sandbox import run_in_docker

# --- Page Configuration ---
st.set_page_config(
    page_title="GrandmasterAi Solver",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stStatus { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("🏆 GrandmasterAi: Agentic CP Solver")
    st.markdown("Automating the path from problem statement to verified solution.")
    st.divider()

    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("⚙️ Agent Settings")
        max_retries = st.slider("Retries per Sample", 1, 5, 3, help="How many times the Critic can send code back to the Architect.")
        st.info("The Docker sandbox provides a secure layer to compile and execute generated C++ code.")
        
        if st.button("Clear Cache & Logs", key="clear_cache"):
            st.session_state.clear()
            st.rerun()

    # --- Input Section ---
    url = st.text_input("Codeforces Problem URL", placeholder="https://codeforces.com/problemset/problem/4/A", key="problem_url")

    # Use a persistent container for logs so they don't jump around
    log_container = st.container()

    if st.button("Start Solving 🚀", key="main_solve_btn"):
        if not url:
            st.warning("Please enter a valid Codeforces URL.")
            return

        # 1. THE EYES: Scraping Stage
        with st.status("🔍 Scraping Problem Data...", expanded=True) as status:
            data = scrape_problem(url)
            if not data:
                st.error("Failed to fetch problem. Check your internet or the URL.")
                status.update(label="Scraping Failed ❌", state="error")
                return
            st.write(f"**Problem:** {data['title']}")
            st.write(f"**Time Limit:** {data['time_limit']}s")
            status.update(label="Problem Scraped ✅", state="complete", expanded=False)

        # 2. THE BRAIN: Initial Generation
        with st.status("🧠 Architect is Thinking...", expanded=True) as status:
            raw_response = get_ai_solution(data)
            active_code = extract_code(raw_response)
            st.code(active_code, language="cpp")
            status.update(label="Initial Code Generated ✅", state="complete", expanded=False)

        # 3. THE WARDEN: Verification & Refinement Loop
        st.subheader("🛠️ Verification & Refinement")
        
        samples = data['samples']
        current_sample_idx = 0
        
        # Main refinement state machine
        while current_sample_idx < len(samples):
            sample = samples[current_sample_idx]
            sample_name = f"Sample {current_sample_idx + 1}"
            
            with st.expander(f"📋 {sample_name}", expanded=True):
                # Run the initial test
                actual = run_in_docker(active_code, sample['input'], data['time_limit'])
                
                if actual.strip() == sample['output'].strip():
                    st.success(f"{sample_name} Passed!")
                    current_sample_idx += 1
                else:
                    st.error(f"{sample_name} Failed.")
                    
                    # Nested Refinement Tries
                    solved_current = False
                    for attempt in range(1, max_retries + 1):
                        st.markdown(f"**Refinement Attempt {attempt}/{max_retries}**")
                        
                        # A. Get Critic's Audit
                        error_report = f"Input: {sample['input']}\nExpected: {sample['output']}\nGot: {actual}"
                        with st.spinner("Critic is auditing logic..."):
                            analysis = get_second_opinion(data, active_code, error_report)
                        st.info(f"**Critic's Insight:** {analysis}")

                        # B. Architect Fixes
                        feedback = f"CODE FAILED SAMPLE:\n{active_code}\n\nERROR:\n{error_report}\n\nCRITIC ADVICE:\n{analysis}"
                        with st.spinner("Architect is rewriting..."):
                            new_response = get_ai_solution(data, feedback=feedback)
                            active_code = extract_code(new_response)
                        
                        # C. Re-test
                        actual = run_in_docker(active_code, sample['input'], data['time_limit'])
                        if actual.strip() == sample['output'].strip():
                            st.success(f"Success! {sample_name} now passes.")
                            solved_current = True
                            break
                        else:
                            st.warning(f"Attempt {attempt} still failing.")

                    if solved_current:
                        current_sample_idx += 1
                    else:
                        st.error(f"Could not solve {sample_name} after {max_retries} attempts.")
                        st.stop()

        # 4. FINAL VERDICT
        st.divider()
        st.balloons()
        st.success("### 🏆 ALL SAMPLES PASSED!")
        st.markdown("Final Optimized C++ Code:")
        st.code(active_code, language="cpp")
        
        st.download_button(
            label="Download Solution (.cpp)",
            data=active_code,
            file_name=f"solution_{data['title'].replace(' ', '_')}.cpp",
            mime="text/x-c++src",
            key="download_final"
        )

if __name__ == "__main__":
    main()