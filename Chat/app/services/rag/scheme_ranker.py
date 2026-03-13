from typing import List, Dict, Any


class SchemeRanker:
    """
    Applies business-level ranking logic on top of vector similarity score.
    Works with a farm_context dict containing: crop, soil_type, area_acres, state, district.
    """

    REGION_WEIGHT = 0.10
    CROP_WEIGHT = 0.10
    SOIL_WEIGHT = 0.05
    LAND_SIZE_WEIGHT = 0.05
    PAN_INDIA_WEIGHT = 0.03

    def rank(self, results: List[Dict], farm_context: Dict[str, Any]) -> List[Dict]:
        """
        Enhance similarity score using domain logic based on farm context.
        """
        user_crop = (farm_context.get("crop") or "").lower()
        user_soil = (farm_context.get("soil_type") or "").lower()
        user_state = (farm_context.get("state") or "").lower()
        user_district = (farm_context.get("district") or "").lower()
        user_area = farm_context.get("area_acres", 0)

        for item in results:
            base_score = item.get("similarity", 0.0)
            boost = 0.0

            # Region boost — check if scheme region matches state or is pan-india
            scheme_region = (item.get("region") or "").lower().strip()
            if scheme_region:
                if user_state and user_state in scheme_region:
                    boost += self.REGION_WEIGHT
                elif "pan-india" in scheme_region or "pan india" in scheme_region:
                    boost += self.PAN_INDIA_WEIGHT
                elif user_district and user_district in scheme_region:
                    boost += self.REGION_WEIGHT

            # Crop boost — fuzzy match: check if user's crop appears in scheme's applicable crops
            scheme_crops = (item.get("crop_type") or "").lower()
            if user_crop and scheme_crops:
                if user_crop in scheme_crops or "all" in scheme_crops:
                    boost += self.CROP_WEIGHT

            # Soil type boost — for schemes related to soil health
            if user_soil:
                scheme_desc = (item.get("description") or "").lower()
                if user_soil in scheme_desc or "soil" in scheme_desc:
                    boost += self.SOIL_WEIGHT

            # Land-size eligibility boost
            eligibility_text = (item.get("eligibility") or "").lower()
            if user_area > 0:
                # Small/marginal farmer boost (typically ≤2 ha ≈ 5 acres)
                if user_area <= 5 and ("small" in eligibility_text or "marginal" in eligibility_text):
                    boost += self.LAND_SIZE_WEIGHT
                # Broader "all farmers" eligibility
                elif "all farmer" in eligibility_text:
                    boost += self.LAND_SIZE_WEIGHT * 0.5

            final_score = round(base_score + boost, 4)

            item["base_score"] = round(base_score, 4)
            item["boost"] = round(boost, 4)
            item["final_score"] = final_score

        return sorted(results, key=lambda x: x["final_score"], reverse=True)