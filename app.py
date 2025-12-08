"""
오렌지 당도 추정 AI - Streamlit 앱
"""

import streamlit as st
from PIL import Image
import io

from src.vision_api import get_vision_api
from src.orange_analyzer import OrangeAnalyzer, OrangeAnalysisResult


# 페이지 설정
st.set_page_config(
    page_title="오렌지 당도 추정 AI",
    page_icon="🍊",
    layout="centered"
)

# 커스텀 CSS
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
    """순위에 따른 이모지 반환"""
    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
    return rank_emojis.get(rank, f"{rank}위")


def get_grade_class(grade: str) -> str:
    """등급에 따른 CSS 클래스 반환"""
    grade_map = {"높음": "grade-high", "중간": "grade-medium", "낮음": "grade-low"}
    return grade_map.get(grade, "grade-medium")


def display_single_result(result: OrangeAnalysisResult, image=None, rank: int = None, total: int = 1):
    """단일 분석 결과 표시"""

    if not result.is_orange:
        st.error(result.error_message or "오렌지가 아닌 이미지입니다.")
        return

    grade_class = get_grade_class(result.sweetness_grade)

    # 순위 표시 (다중 이미지일 때만)
    if rank and total > 1:
        if rank == 1:
            st.markdown('<div class="winner-banner">🏆 가장 달 것으로 예상! 🏆</div>', unsafe_allow_html=True)

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
            <div style="font-size: 14px; margin-bottom: 5px;">당도 등급</div>
            <div style="font-size: 32px; font-weight: bold;">{result.sweetness_grade}</div>
            <div style="font-size: 24px; margin-top: 10px;">예상 Brix: {result.brix_range}</div>
        </div>
        """, unsafe_allow_html=True)

        # 점수 표시
        if result.sweetness_score:
            st.markdown(f"""
            <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                <span style="font-size: 14px;">당도 점수:</span>
                <span style="font-size: 28px; font-weight: bold; color: #FF6B35;"> {result.sweetness_score}점</span>
                <span style="font-size: 12px; color: #888;"> / 100</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**신뢰도:** {result.confidence_score}%")

    # 상세 분석
    with st.expander("📊 상세 분석 보기", expanded=(rank == 1 if rank else True)):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**🎨 색상**")
            st.caption(result.color_analysis)
        with col_b:
            st.markdown("**✨ 표면**")
            st.caption(result.surface_analysis)
        with col_c:
            st.markdown("**🍊 숙성도**")
            st.caption(result.ripeness_analysis)

        st.markdown("---")
        st.markdown(f"**💡 종합 판단:** {result.analysis_reason}")


def main():
    # 헤더
    st.markdown("<h1 class='main-title'>🍊 오렌지 당도 추정 AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>오렌지 사진을 업로드하면 외관을 AI로 분석하여 당도를 추정합니다</p>", unsafe_allow_html=True)

    # 사이드바 - API 설정
    with st.sidebar:
        st.header("⚙️ API 설정")

        api_provider = st.selectbox(
            "AI 모델 선택",
            options=["openai", "claude"],
            format_func=lambda x: "GPT-4o (OpenAI) - 추천" if x == "openai" else "Claude (Anthropic)"
        )

        api_key = st.text_input(
            "API Key 입력",
            type="password",
            help="선택한 AI 서비스의 API 키를 입력하세요."
        )

        # API 키 발급 안내
        with st.expander("🔑 API 키 발급 방법"):
            if api_provider == "claude":
                st.markdown("""
                **Anthropic (Claude)**
                1. [console.anthropic.com](https://console.anthropic.com/) 접속
                2. 회원가입 또는 로그인
                3. API Keys 메뉴 → 새 키 생성
                4. 크레딧 충전 필요 (최소 $5)
                """)
            else:
                st.markdown("""
                **OpenAI (GPT-4)**
                1. [platform.openai.com](https://platform.openai.com/) 접속
                2. 회원가입 또는 로그인
                3. API Keys 메뉴 → 새 키 생성
                4. 크레딧 충전 필요
                """)

        st.divider()

        # 사용 안내
        st.header("📖 사용 방법")
        st.markdown("""
        1. API 키 입력
        2. 오렌지 사진 업로드 (최대 5장)
        3. '분석하기' 클릭
        4. 결과 확인!

        **여러 장 업로드 시**
        AI가 직접 비교하여 가장 달 것으로 예상되는 순서대로 순위를 매깁니다.
        """)

        st.divider()
        st.caption("""
        ⚠️ **주의사항**
        - 외관 기반 상대적 추정입니다
        - 실제 당도와 차이가 있을 수 있습니다
        - 조명/각도에 따라 결과가 달라질 수 있습니다
        """)

    # 메인 영역 - 이미지 업로드
    st.subheader("📤 오렌지 사진 업로드")

    uploaded_files = st.file_uploader(
        "이미지를 선택하세요 (최대 5장)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="JPG, PNG, WEBP 형식 지원. 10MB 이하 권장."
    )

    # 업로드된 파일 수 제한
    if uploaded_files and len(uploaded_files) > 5:
        st.warning("⚠️ 최대 5장까지 업로드 가능합니다. 처음 5장만 분석합니다.")
        uploaded_files = uploaded_files[:5]

    # 업로드된 이미지 미리보기
    if uploaded_files:
        st.markdown(f"**업로드된 이미지: {len(uploaded_files)}장**")
        cols = st.columns(min(len(uploaded_files), 5))
        for idx, (col, file) in enumerate(zip(cols, uploaded_files)):
            with col:
                img = Image.open(file)
                st.image(img, caption=f"#{idx+1}", use_container_width=True)

    # 분석 버튼
    st.divider()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analyze_btn = st.button(
            "🔍 분석하기",
            type="primary",
            use_container_width=True,
            disabled=not (api_key and uploaded_files)
        )

    if not api_key:
        st.info("👈 사이드바에서 API 키를 입력해주세요.")
    elif not uploaded_files:
        st.info("📤 오렌지 사진을 업로드해주세요.")

    # 분석 실행
    if analyze_btn and api_key and uploaded_files:
        try:
            # Vision API 초기화
            vision_api = get_vision_api(api_provider, api_key)
            analyzer = OrangeAnalyzer(vision_api)

            with st.spinner("🍊 AI가 오렌지를 분석하고 있습니다..."):
                if len(uploaded_files) == 1:
                    # 단일 이미지 분석
                    file = uploaded_files[0]
                    file.seek(0)
                    image_data = file.read()
                    result = analyzer.analyze(image_data)

                    st.subheader("📋 분석 결과")
                    file.seek(0)
                    img = Image.open(file)
                    display_single_result(result, image=img)

                else:
                    # 다중 이미지 비교 분석
                    images = []
                    image_objects = {}

                    for file in uploaded_files:
                        file.seek(0)
                        image_data = file.read()
                        images.append((file.name, image_data))

                        file.seek(0)
                        image_objects[file.name] = Image.open(file)

                    results = analyzer.analyze_multiple(images)

                    st.subheader("🏆 분석 결과 (당도 높은 순)")
                    st.markdown("AI가 모든 이미지를 직접 비교하여 순위를 매겼습니다.")

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
                st.error("❌ API 크레딧이 부족합니다. API 제공사 웹사이트에서 크레딧을 충전해주세요.")
            elif "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
                st.error("❌ API 키가 올바르지 않습니다. 다시 확인해주세요.")
            else:
                st.error(f"❌ 오류가 발생했습니다: {error_msg}")

    # 푸터
    st.divider()
    st.markdown("""
    <div class='disclaimer'>
    이 서비스는 오렌지의 외관을 AI로 분석하여 당도를 <b>추정</b>합니다.<br>
    실제 당도 측정과는 차이가 있을 수 있으며, <b>참고용</b>으로만 사용해주세요.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
