"""
Orange Sweetness Estimation AI - Streamlit App
"""

import streamlit as st
from PIL import Image
import io

from src.vision_api import get_vision_api
from src.orange_analyzer import OrangeAnalyzer, OrangeAnalysisResult


# Page config
st.set_page_config(
    page_title="Orange Sweetness AI",
    page_icon="🍊",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #FF6B35;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 16px;
        margin-bottom: 30px;
    }
    .rank-badge {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
        padding: 10px;
    }
    .rank-1 { color: #FFD700; }
    .rank-2 { color: #C0C0C0; }
    .rank-3 { color: #CD7F32; }
    .rank-other { color: #888; }
    .score-display {
        font-size: 36px;
        font-weight: bold;
        text-align: center;
    }
    .grade-high {
        color: #FF6B35;
        background: linear-gradient(135deg, #FFE4C4 0%, #FFDAB9 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF6B35;
    }
    .grade-medium {
        color: #DAA520;
        background: linear-gradient(135deg, #FFF8DC 0%, #FFFACD 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #DAA520;
    }
    .grade-low {
        color: #808080;
        background: linear-gradient(135deg, #F5F5F5 0%, #E8E8E8 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #808080;
    }
    .comparison-highlight {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-style: italic;
    }
    .disclaimer {
        font-size: 12px;
        color: #888;
        text-align: center;
        margin-top: 20px;
    }
    .winner-banner {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


def get_rank_emoji(rank: int) -> str:
    """Return emoji based on rank"""
    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
    return rank_emojis.get(rank, f"#{rank}")


def get_grade_class(grade: str) -> str:
    """Return CSS class based on grade"""
    grade_map = {"높음": "grade-high", "중간": "grade-medium", "낮음": "grade-low",
                 "High": "grade-high", "Medium": "grade-medium", "Low": "grade-low"}
    return grade_map.get(grade, "grade-medium")


def translate_grade(grade: str) -> str:
    """Translate Korean grade to English"""
    translations = {"높음": "High", "중간": "Medium", "낮음": "Low"}
    return translations.get(grade, grade)


def display_single_result(result: OrangeAnalysisResult, image=None, rank: int = None, total: int = 1):
    """Display single analysis result"""

    if not result.is_orange:
        st.error(result.error_message or "This image does not appear to be an orange.")
        return

    grade_class = get_grade_class(result.sweetness_grade)
    display_grade = translate_grade(result.sweetness_grade)

    # Rank display (only for multiple images)
    if rank and total > 1:
        if rank == 1:
            st.markdown('<div class="winner-banner">🏆 Expected Sweetest! 🏆</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        if image:
            st.image(image, use_container_width=True)
        if rank and total > 1:
            rank_class = f"rank-{rank}" if rank <= 3 else "rank-other"
            st.markdown(f'<div class="rank-badge {rank_class}">{get_rank_emoji(rank)}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="{grade_class}">
            <div style="font-size: 14px; margin-bottom: 5px;">Sweetness Grade</div>
            <div style="font-size: 32px; font-weight: bold;">{display_grade}</div>
            <div style="font-size: 24px; margin-top: 10px;">Est. Brix: {result.brix_range}</div>
        </div>
        """, unsafe_allow_html=True)

        # Score display
        if result.sweetness_score:
            st.markdown(f"""
            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                <span style="font-size: 14px;">Sweetness Score:</span>
                <span style="font-size: 28px; font-weight: bold; color: #FF6B35;"> {result.sweetness_score}</span>
                <span style="font-size: 12px; color: #888;"> / 100</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**Confidence:** {result.confidence_score}%")

    # Detailed analysis
    with st.expander("📊 View Detailed Analysis", expanded=(rank == 1 if rank else True)):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**🎨 Color**")
            st.caption(result.color_analysis)
        with col_b:
            st.markdown("**✨ Surface**")
            st.caption(result.surface_analysis)
        with col_c:
            st.markdown("**🍊 Ripeness**")
            st.caption(result.ripeness_analysis)

        st.markdown("---")
        st.markdown(f"**💡 Summary:** {result.analysis_reason}")


def main():
    # Header
    st.markdown("<h1 class='main-title'>🍊 Orange Sweetness AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Upload orange photos and AI will analyze appearance to estimate sweetness</p>", unsafe_allow_html=True)

    # Sidebar - API settings
    with st.sidebar:
        st.header("⚙️ API Settings")

        api_provider = st.selectbox(
            "Select AI Model",
            options=["openai", "claude"],
            format_func=lambda x: "GPT-4o (OpenAI) - Recommended" if x == "openai" else "Claude (Anthropic)"
        )

        api_key = st.text_input(
            "Enter API Key",
            type="password",
            help="Enter your API key for the selected AI service."
        )

        # API key guide
        with st.expander("🔑 How to Get API Key"):
            if api_provider == "claude":
                st.markdown("""
                **Anthropic (Claude)**
                1. Visit [console.anthropic.com](https://console.anthropic.com/)
                2. Sign up or log in
                3. Go to API Keys → Create new key
                4. Add credits (minimum $5)
                """)
            else:
                st.markdown("""
                **OpenAI (GPT-4)**
                1. Visit [platform.openai.com](https://platform.openai.com/)
                2. Sign up or log in
                3. Go to API Keys → Create new key
                4. Add credits
                """)

        st.divider()

        # Usage guide
        st.header("📖 How to Use")
        st.markdown("""
        1. Enter API key
        2. Upload orange photos (up to 5)
        3. Click 'Analyze'
        4. View results!

        **Multiple Images**
        AI will compare all images and rank them by expected sweetness.
        """)

        st.divider()
        st.caption("""
        ⚠️ **Note**
        - This is a visual estimation
        - Actual sweetness may vary
        - Results depend on lighting/angle
        """)

    # Main area - Image upload
    st.subheader("📤 Upload Orange Photos")

    uploaded_files = st.file_uploader(
        "Select images (up to 5)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Supports JPG, PNG, WEBP. Under 10MB recommended."
    )

    # Limit uploaded files
    if uploaded_files and len(uploaded_files) > 5:
        st.warning("⚠️ Maximum 5 images allowed. Only first 5 will be analyzed.")
        uploaded_files = uploaded_files[:5]

    # Preview uploaded images
    if uploaded_files:
        st.markdown(f"**Uploaded: {len(uploaded_files)} image(s)**")
        cols = st.columns(min(len(uploaded_files), 5))
        for idx, (col, file) in enumerate(zip(cols, uploaded_files)):
            with col:
                img = Image.open(file)
                st.image(img, caption=f"#{idx+1}", use_container_width=True)

    # Analyze button
    st.divider()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analyze_btn = st.button(
            "🔍 Analyze",
            type="primary",
            use_container_width=True,
            disabled=not (api_key and uploaded_files)
        )

    if not api_key:
        st.info("👈 Please enter your API key in the sidebar.")
    elif not uploaded_files:
        st.info("📤 Please upload orange photos.")

    # Run analysis
    if analyze_btn and api_key and uploaded_files:
        try:
            # Initialize Vision API
            vision_api = get_vision_api(api_provider, api_key)
            analyzer = OrangeAnalyzer(vision_api)

            with st.spinner("🍊 AI is analyzing the oranges..."):
                if len(uploaded_files) == 1:
                    # Single image analysis
                    file = uploaded_files[0]
                    file.seek(0)
                    image_data = file.read()
                    result = analyzer.analyze(image_data)

                    st.subheader("📋 Analysis Result")
                    file.seek(0)
                    img = Image.open(file)
                    display_single_result(result, image=img)

                else:
                    # Multiple image comparison
                    images = []
                    image_objects = {}

                    for file in uploaded_files:
                        file.seek(0)
                        image_data = file.read()
                        images.append((file.name, image_data))

                        file.seek(0)
                        image_objects[file.name] = Image.open(file)

                    results = analyzer.analyze_multiple(images)

                    st.subheader("🏆 Results (Ranked by Sweetness)")
                    st.markdown("AI compared all images and ranked them.")

                    for filename, result in results:
                        st.markdown("---")
                        display_single_result(
                            result,
                            image=image_objects.get(filename),
                            rank=result.rank,
                            total=len(results)
                        )

        except Exception as e:
            error_msg = str(e)
            if "credit" in error_msg.lower() or "balance" in error_msg.lower():
                st.error("❌ Insufficient API credits. Please add credits on your API provider's website.")
            elif "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
                st.error("❌ Invalid API key. Please check and try again.")
            else:
                st.error(f"❌ An error occurred: {error_msg}")

    # Footer
    st.divider()
    st.markdown("""
    <div class='disclaimer'>
    This service uses AI to <b>estimate</b> orange sweetness based on appearance.<br>
    Actual sweetness may differ. For <b>reference only</b>.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
