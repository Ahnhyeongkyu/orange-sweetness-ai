"""
오렌지 당도 분석 모듈
- Vision API를 활용한 외관 분석
- 당도 등급 및 Brix 범위 추정
- 다중 이미지 상대 비교
"""

import json
import re
from dataclasses import dataclass
from typing import Optional
from src.vision_api import VisionAPIBase


@dataclass
class OrangeAnalysisResult:
    """오렌지 분석 결과"""
    is_orange: bool
    sweetness_grade: Optional[str] = None  # 높음, 중간, 낮음
    brix_range: Optional[str] = None  # 예: "12~14"
    brix_min: Optional[float] = None
    brix_max: Optional[float] = None
    sweetness_score: Optional[int] = None  # 0-100 세밀한 점수
    confidence_score: Optional[int] = None  # 1-100
    rank: Optional[int] = None  # 순위 (다중 비교 시)
    analysis_reason: Optional[str] = None  # 분석 근거
    color_analysis: Optional[str] = None
    surface_analysis: Optional[str] = None
    ripeness_analysis: Optional[str] = None
    error_message: Optional[str] = None


# 단일 이미지 분석용 프롬프트 (더 엄격한 기준)
SINGLE_ANALYSIS_PROMPT = """당신은 오렌지 품질 감별 전문가입니다. 엄격한 기준으로 평가해주세요.

## 평가 기준 (각 항목 0-100점)

### 1. 색상 점수 (40% 비중)
- 90-100: 매우 진한 주황색, 완벽히 균일, 녹색 전혀 없음
- 70-89: 진한 주황색, 대체로 균일, 녹색 거의 없음
- 50-69: 보통 주황색, 약간 불균일, 녹색 약간 있음
- 30-49: 연한 주황색, 불균일, 녹색 부분 있음
- 0-29: 매우 연함, 많이 불균일, 녹색 많음

### 2. 표면 점수 (30% 비중)
- 90-100: 강한 자연광택, 매끈한 질감, 기공 작고 균일
- 70-89: 적당한 광택, 좋은 질감, 기공 적당
- 50-69: 보통 광택, 보통 질감, 기공 보통
- 30-49: 광택 부족, 거친 질감, 기공 크거나 불균일
- 0-29: 광택 없음, 매우 거침, 기공 문제 있음

### 3. 숙성도 점수 (30% 비중)
- 90-100: 완벽한 숙성, 탄력 최적, 신선함 최고
- 70-89: 잘 익음, 탄력 좋음, 신선함
- 50-69: 적당히 익음, 탄력 보통
- 30-49: 덜 익었거나 과숙, 탄력 부족
- 0-29: 미숙 또는 과숙 심함

## 당도 등급 기준 (총점 기준) - 반드시 3단계만 사용
- **높음** (12-14 Brix): 총점 75점 이상
- **중간** (10-12 Brix): 총점 50-74점
- **낮음** (8-10 Brix): 총점 50점 미만

## 응답 형식 (JSON만 출력)
```json
{
  "is_orange": true,
  "color_score": 0-100,
  "surface_score": 0-100,
  "ripeness_score": 0-100,
  "sweetness_score": 0-100,
  "sweetness_grade": "높음" 또는 "중간" 또는 "낮음",
  "brix_min": 숫자,
  "brix_max": 숫자,
  "confidence_score": 0-100,
  "color_analysis": "색상 분석 (구체적 근거)",
  "surface_analysis": "표면 분석 (구체적 근거)",
  "ripeness_analysis": "숙성도 분석 (구체적 근거)",
  "analysis_reason": "종합 판단 (왜 이 등급인지)"
}
```

**중요**:
- sweetness_grade는 반드시 "높음", "중간", "낮음" 중 하나만 사용하세요.
- "매우 높음", "보통" 등 다른 표현 절대 금지!
- 일반 마트 오렌지는 대부분 "중간" 등급입니다.
- "높음"은 프리미엄 고품질만 해당합니다.
- 오렌지가 아니면 is_orange: false로 응답

이미지를 분석해주세요."""


# 다중 이미지 상대 비교용 프롬프트
MULTI_COMPARISON_PROMPT = """당신은 오렌지 품질 감별 전문가입니다.
{count}장의 오렌지 이미지를 비교하여 당도가 높을 것으로 예상되는 순서대로 순위를 매겨주세요.

## 비교 기준
1. **색상**: 더 진한 주황색, 더 균일한 색상이 높은 당도
2. **광택**: 자연스러운 광택이 있을수록 높은 당도
3. **표면**: 매끈하고 기공이 적당할수록 높은 당도
4. **숙성도**: 적절히 익은 상태일수록 높은 당도

## 자른 오렌지(단면이 보이는 경우) 평가 기준
- 자른 오렌지는 **과육 색상**으로 판단
- 과육이 진한 주황색이고 과즙이 풍부해 보이면 → 높은 당도
- 과육이 연한 색이거나 건조해 보이면 → 낮은 당도
- 원형 오렌지와 동일한 기준으로 공정하게 비교

## 중요 지침
- 이미지 간 **상대적 차이**를 반드시 구분하세요
- 아무리 비슷해 보여도 미세한 차이를 찾아 순위를 명확히 매기세요
- 동점 없이 1위부터 {count}위까지 모두 다른 순위를 부여하세요
- 각 이미지의 sweetness_score는 최소 5점 이상 차이나게 해주세요
- 순위 결정에 일관성을 유지하세요

## 당도 등급 기준 - 반드시 3단계만 사용
- **높음** (12-14 Brix): 총점 75점 이상
- **중간** (10-12 Brix): 총점 50-74점
- **낮음** (8-10 Brix): 총점 50점 미만

## 응답 형식 (JSON 배열로 출력)
```json
[
  {{
    "image_index": 1,
    "rank": 1,
    "sweetness_score": 85,
    "sweetness_grade": "높음",
    "brix_min": 12,
    "brix_max": 14,
    "confidence_score": 85,
    "color_analysis": "색상 분석",
    "surface_analysis": "표면 분석",
    "ripeness_analysis": "숙성도 분석",
    "analysis_reason": "왜 이 순위인지 다른 이미지와 비교하여 설명",
    "comparison_note": "다른 이미지 대비 어떤 점이 더 좋은지/나쁜지"
  }},
  ...
]
```

**중요**: sweetness_grade는 반드시 "높음", "중간", "낮음" 중 하나만 사용!

{count}장의 이미지를 순서대로 분석하고, 당도 높은 순으로 순위를 매겨주세요.
첫 번째 이미지가 image_index: 1, 두 번째가 image_index: 2 입니다."""


class OrangeAnalyzer:
    """오렌지 당도 분석기"""

    def __init__(self, vision_api: VisionAPIBase):
        self.vision_api = vision_api

    def analyze(self, image_data: bytes) -> OrangeAnalysisResult:
        """단일 오렌지 이미지 분석"""
        try:
            response = self.vision_api.analyze_image(
                image_data=image_data,
                prompt=SINGLE_ANALYSIS_PROMPT
            )
            return self._parse_single_response(response)

        except Exception as e:
            return OrangeAnalysisResult(
                is_orange=False,
                error_message=f"분석 중 오류 발생: {str(e)}"
            )

    def _parse_single_response(self, response: str) -> OrangeAnalysisResult:
        """단일 분석 API 응답 파싱"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            if not data.get("is_orange", False):
                return OrangeAnalysisResult(
                    is_orange=False,
                    error_message="오렌지가 아닌 이미지입니다. 오렌지 사진을 업로드해주세요."
                )

            brix_min = data.get("brix_min")
            brix_max = data.get("brix_max")
            brix_range = f"{brix_min}~{brix_max}" if brix_min and brix_max else None

            return OrangeAnalysisResult(
                is_orange=True,
                sweetness_grade=data.get("sweetness_grade"),
                brix_range=brix_range,
                brix_min=brix_min,
                brix_max=brix_max,
                sweetness_score=data.get("sweetness_score"),
                confidence_score=data.get("confidence_score"),
                analysis_reason=data.get("analysis_reason"),
                color_analysis=data.get("color_analysis"),
                surface_analysis=data.get("surface_analysis"),
                ripeness_analysis=data.get("ripeness_analysis"),
            )

        except json.JSONDecodeError:
            return OrangeAnalysisResult(
                is_orange=False,
                error_message="분석 결과를 파싱할 수 없습니다. 다시 시도해주세요."
            )

    def analyze_multiple(self, images: list[tuple[str, bytes]]) -> list[tuple[str, OrangeAnalysisResult]]:
        """
        여러 오렌지 이미지 상대 비교 분석
        - 모든 이미지를 한 번에 Vision API로 전송
        - AI가 직접 상대 비교하여 순위 결정
        """
        if len(images) == 1:
            # 단일 이미지는 기존 방식
            filename, image_data = images[0]
            result = self.analyze(image_data)
            result.rank = 1
            return [(filename, result)]

        try:
            # 다중 이미지 비교 분석
            prompt = MULTI_COMPARISON_PROMPT.format(count=len(images))
            response = self.vision_api.analyze_multiple_images(
                images_data=[img_data for _, img_data in images],
                prompt=prompt
            )

            results = self._parse_multi_response(response, images)
            return results

        except Exception as e:
            # 다중 분석 실패 시 개별 분석으로 폴백
            return self._fallback_individual_analysis(images, str(e))

    def _parse_multi_response(self, response: str, images: list[tuple[str, bytes]]) -> list[tuple[str, OrangeAnalysisResult]]:
        """다중 비교 응답 파싱"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()

            data_list = json.loads(json_str)

            results = []
            for data in data_list:
                img_idx = data.get("image_index", 1) - 1
                if 0 <= img_idx < len(images):
                    filename = images[img_idx][0]

                    brix_min = data.get("brix_min")
                    brix_max = data.get("brix_max")
                    brix_range = f"{brix_min}~{brix_max}" if brix_min and brix_max else None

                    comparison_note = data.get("comparison_note", "")
                    analysis_reason = data.get("analysis_reason", "")
                    if comparison_note:
                        analysis_reason = f"{analysis_reason} ({comparison_note})"

                    result = OrangeAnalysisResult(
                        is_orange=True,
                        sweetness_grade=data.get("sweetness_grade"),
                        brix_range=brix_range,
                        brix_min=brix_min,
                        brix_max=brix_max,
                        sweetness_score=data.get("sweetness_score"),
                        confidence_score=data.get("confidence_score"),
                        rank=data.get("rank"),
                        analysis_reason=analysis_reason,
                        color_analysis=data.get("color_analysis"),
                        surface_analysis=data.get("surface_analysis"),
                        ripeness_analysis=data.get("ripeness_analysis"),
                    )
                    results.append((filename, result))

            # 순위 기준 정렬
            results.sort(key=lambda x: x[1].rank if x[1].rank else 999)
            return results

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # 파싱 실패 시 개별 분석으로 폴백
            return self._fallback_individual_analysis(images, str(e))

    def _fallback_individual_analysis(self, images: list[tuple[str, bytes]], error_msg: str = "") -> list[tuple[str, OrangeAnalysisResult]]:
        """개별 분석 폴백 (다중 비교 실패 시)"""
        results = []

        for filename, image_data in images:
            result = self.analyze(image_data)
            results.append((filename, result))

        # sweetness_score 기준 정렬
        def sort_key(item):
            _, result = item
            if not result.is_orange:
                return -1
            return result.sweetness_score or result.brix_max or 0

        results.sort(key=sort_key, reverse=True)

        # 순위 부여
        for rank, (filename, result) in enumerate(results, 1):
            result.rank = rank

        return results
