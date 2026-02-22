from typing import List, Dict
from app.db.models.user import User


class SchemeRanker:
    """
    Applies business-level ranking logic
    on top of vector similarity score.
    """

    REGION_WEIGHT = 0.08
    CROP_WEIGHT = 0.07
    LAND_SIZE_WEIGHT = 0.05

    def rank(self, results: List[Dict], user: User) -> List[Dict]:
        """
        Enhance similarity score using domain logic.
        """

        for item in results:
            base_score = item.get("similarity", 0.0)
            boost = 0.0

            # Region boost
            if item.get("region") and user.region:
                if item["region"].lower() == user.region.lower():
                    boost += self.REGION_WEIGHT

            # Crop boost
            if item.get("crop_type") and user.crop_type:
                if item["crop_type"].lower() == user.crop_type.lower():
                    boost += self.CROP_WEIGHT

            # Land-size eligibility boost
            eligibility_text = item.get("eligibility", "").lower()
            if user.land_size:
                if "small farmer" in eligibility_text and user.land_size < 5:
                    boost += self.LAND_SIZE_WEIGHT

            final_score = round(base_score + boost, 4)

            item["base_score"] = round(base_score, 4)
            item["boost"] = round(boost, 4)
            item["final_score"] = final_score

        return sorted(results, key=lambda x: x["final_score"], reverse=True)