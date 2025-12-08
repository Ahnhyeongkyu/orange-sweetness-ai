# 오렌지 당도 추정 AI

오렌지 사진을 업로드하면 외관을 AI로 분석하여 당도를 추정하는 웹 서비스입니다.

## 상태
- [x] 개발 완료
- [ ] 배포 완료

## 기능
- 오렌지 사진 업로드 → 당도 등급(높음/중간/낮음) + Brix 범위 출력
- 최대 5장까지 동시 업로드 → 당도 높은 순 순위 비교
- 분석 근거 표시 (색상, 표면, 숙성도)

## 폴더 구조
```
├── app.py              # Streamlit 앱 (메인)
├── src/
│   ├── vision_api.py   # Vision API 연동 (Claude/OpenAI)
│   └── orange_analyzer.py  # 오렌지 분석 로직
├── requirements.txt    # 의존성
└── .streamlit/
    └── config.toml     # Streamlit 설정
```

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud 배포
1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://share.streamlit.io/) 접속
3. "New app" → GitHub 저장소 연결
4. Main file: `app.py` 선택
5. Deploy 클릭

## 사용법
1. 사이드바에서 API 선택 (Claude 또는 OpenAI)
2. API Key 입력
3. 오렌지 사진 업로드 (최대 5장)
4. '분석하기' 클릭
5. 결과 확인

## API 키 발급
### Claude (Anthropic)
1. https://console.anthropic.com/ 접속
2. 회원가입/로그인
3. API Keys → 새 키 생성

### OpenAI
1. https://platform.openai.com/ 접속
2. 회원가입/로그인
3. API Keys → 새 키 생성

## 주의사항
- 외관 기반 상대적 추정이므로 실제 당도와 차이가 있을 수 있습니다
- 조명/각도에 따라 결과가 달라질 수 있습니다
- 참고용으로만 사용해주세요
