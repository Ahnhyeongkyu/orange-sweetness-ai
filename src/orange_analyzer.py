"""
Orange Sweetness Analysis Module
- Visual analysis using Vision API
- Sweetness grade and Brix range estimation
- Multi-image relative comparison
"""

import json
import re
from dataclasses import dataclass
from typing import Optional
from src.vision_api import VisionAPIBase


@dataclass
class OrangeAnalysisResult:
    """Orange analysis result"""
    is_orange: bool
    sweetness_grade: Optional[str] = None  # High, Medium, Low
    brix_range: Optional[str] = None  # e.g., "12~14"
    brix_min: Optional[float] = None
    brix_max: Optional[float] = None
    sweetness_score: Optional[int] = None  # 0-100 detailed score
    confidence_score: Optional[int] = None  # 1-100
    rank: Optional[int] = None  # Rank (for multi-comparison)
    analysis_reason: Optional[str] = None  # Analysis rationale
    color_analysis: Optional[str] = None
    surface_analysis: Optional[str] = None
    ripeness_analysis: Optional[str] = None
    error_message: Optional[str] = None


# Single image analysis prompt (strict criteria)
SINGLE_ANALYSIS_PROMPT = """You are an expert orange quality evaluator. Please evaluate with strict criteria.

## Evaluation Criteria (0-100 points each)

### 1. Color Score (40% weight)
- 90-100: Very deep orange, perfectly uniform, no green at all
- 70-89: Deep orange, mostly uniform, almost no green
- 50-69: Average orange, slightly uneven, some green present
- 30-49: Light orange, uneven, green areas present
- 0-29: Very light, very uneven, lots of green

### 2. Surface Score (30% weight)
- 90-100: Strong natural shine, smooth texture, small uniform pores
- 70-89: Moderate shine, good texture, decent pores
- 50-69: Average shine, average texture, average pores
- 30-49: Lack of shine, rough texture, large or uneven pores
- 0-29: No shine, very rough, problematic pores

### 3. Ripeness Score (30% weight)
- 90-100: Perfect ripeness, optimal firmness, peak freshness
- 70-89: Well ripened, good firmness, fresh
- 50-69: Moderately ripened, average firmness
- 30-49: Under-ripe or over-ripe, lacking firmness
- 0-29: Very unripe or severely over-ripe

## Sweetness Grade Criteria (based on total score) - Use only 3 grades
- **High** (12-14 Brix): Total score 75 or above
- **Medium** (10-12 Brix): Total score 50-74
- **Low** (8-10 Brix): Total score below 50

## Response Format (output JSON only)
```json
{
  "is_orange": true,
  "color_score": 0-100,
  "surface_score": 0-100,
  "ripeness_score": 0-100,
  "sweetness_score": 0-100,
  "sweetness_grade": "High" or "Medium" or "Low",
  "brix_min": number,
  "brix_max": number,
  "confidence_score": 0-100,
  "color_analysis": "Color analysis (specific evidence)",
  "surface_analysis": "Surface analysis (specific evidence)",
  "ripeness_analysis": "Ripeness analysis (specific evidence)",
  "analysis_reason": "Overall assessment (why this grade)"
}
```

**Important**:
- sweetness_grade must be exactly "High", "Medium", or "Low".
- Do NOT use other expressions like "Very High", "Average", etc.!
- Most regular supermarket oranges are "Medium" grade.
- "High" is only for premium quality oranges.
- If not an orange, respond with is_orange: false

Please analyze the image."""


# Multi-image relative comparison prompt
MULTI_COMPARISON_PROMPT = """You are an expert orange quality evaluator.
Compare {count} orange images and rank them by expected sweetness level.

## Comparison Criteria
1. **Color**: Deeper orange and more uniform color indicates higher sweetness
2. **Shine**: More natural shine indicates higher sweetness
3. **Surface**: Smoother surface with moderate pores indicates higher sweetness
4. **Ripeness**: Properly ripened state indicates higher sweetness

## Cut Orange (cross-section visible) Evaluation
- For cut oranges, judge by **flesh color**
- Deep orange flesh with abundant juice → higher sweetness
- Light colored or dry-looking flesh → lower sweetness
- Compare fairly with whole oranges using same criteria

## Important Instructions
- You MUST distinguish **relative differences** between images
- Even if they look similar, find subtle differences and rank clearly
- No ties - assign different ranks from 1 to {count}
- Each image's sweetness_score should differ by at least 5 points
- Maintain consistency in ranking decisions

## Sweetness Grade Criteria - Use only 3 grades
- **High** (12-14 Brix): Total score 75 or above
- **Medium** (10-12 Brix): Total score 50-74
- **Low** (8-10 Brix): Total score below 50

## Response Format (output as JSON array)
```json
[
  {{
    "image_index": 1,
    "rank": 1,
    "sweetness_score": 85,
    "sweetness_grade": "High",
    "brix_min": 12,
    "brix_max": 14,
    "confidence_score": 85,
    "color_analysis": "Color analysis",
    "surface_analysis": "Surface analysis",
    "ripeness_analysis": "Ripeness analysis",
    "analysis_reason": "Why this rank - explain compared to other images",
    "comparison_note": "What makes it better/worse than other images"
  }},
  ...
]
```

**Important**: sweetness_grade must be exactly "High", "Medium", or "Low"!

Analyze the {count} images in order and rank them by sweetness level.
First image is image_index: 1, second is image_index: 2, etc."""


class OrangeAnalyzer:
    """Orange sweetness analyzer"""

    def __init__(self, vision_api: VisionAPIBase):
        self.vision_api = vision_api

    def analyze(self, image_data: bytes) -> OrangeAnalysisResult:
        """Analyze single orange image"""
        try:
            response = self.vision_api.analyze_image(
                image_data=image_data,
                prompt=SINGLE_ANALYSIS_PROMPT
            )
            return self._parse_single_response(response)

        except Exception as e:
            return OrangeAnalysisResult(
                is_orange=False,
                error_message=f"Error during analysis: {str(e)}"
            )

    def _parse_single_response(self, response: str) -> OrangeAnalysisResult:
        """Parse single analysis API response"""
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
                    error_message="This is not an orange image. Please upload an orange photo."
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
                error_message="Could not parse analysis result. Please try again."
            )

    def analyze_multiple(self, images: list[tuple[str, bytes]]) -> list[tuple[str, OrangeAnalysisResult]]:
        """
        Relative comparison analysis for multiple orange images
        - Send all images to Vision API at once
        - AI directly compares and determines rankings
        """
        if len(images) == 1:
            # Single image uses existing method
            filename, image_data = images[0]
            result = self.analyze(image_data)
            result.rank = 1
            return [(filename, result)]

        try:
            # Multi-image comparison analysis
            prompt = MULTI_COMPARISON_PROMPT.format(count=len(images))
            response = self.vision_api.analyze_multiple_images(
                images_data=[img_data for _, img_data in images],
                prompt=prompt
            )

            results = self._parse_multi_response(response, images)
            return results

        except Exception as e:
            # Fallback to individual analysis if multi-analysis fails
            return self._fallback_individual_analysis(images, str(e))

    def _parse_multi_response(self, response: str, images: list[tuple[str, bytes]]) -> list[tuple[str, OrangeAnalysisResult]]:
        """Parse multi-comparison response"""
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

            # Sort by rank
            results.sort(key=lambda x: x[1].rank if x[1].rank else 999)
            return results

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Fallback to individual analysis if parsing fails
            return self._fallback_individual_analysis(images, str(e))

    def _fallback_individual_analysis(self, images: list[tuple[str, bytes]], error_msg: str = "") -> list[tuple[str, OrangeAnalysisResult]]:
        """Individual analysis fallback (when multi-comparison fails)"""
        results = []

        for filename, image_data in images:
            result = self.analyze(image_data)
            results.append((filename, result))

        # Sort by sweetness_score
        def sort_key(item):
            _, result = item
            if not result.is_orange:
                return -1
            return result.sweetness_score or result.brix_max or 0

        results.sort(key=sort_key, reverse=True)

        # Assign ranks
        for rank, (filename, result) in enumerate(results, 1):
            result.rank = rank

        return results
