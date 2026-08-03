from services.wardrobe_service import WardrobeService


class RecommendationService:

    # =====================================================
    # KNOWLEDGE BASE WARNA
    # Berdasarkan teori Color Harmony
    # =====================================================

    NEUTRAL_COLORS = {
        "black",
        "white",
        "grey",
        "beige",
        "navy"
    }

    COLOR_HARMONY = {

        # Monochromatic
        ("black", "black"),
        ("white", "white"),
        ("grey", "grey"),
        ("navy", "navy"),
        ("blue", "blue"),
        ("red", "red"),
        ("green", "green"),
        ("yellow", "yellow"),
        ("brown", "brown"),
        ("pink", "pink"),
        ("purple", "purple"),

        # Neutral Combination
        ("black", "white"),
        ("black", "grey"),
        ("black", "beige"),
        ("black", "navy"),

        ("white", "grey"),
        ("white", "beige"),
        ("white", "navy"),

        ("grey", "beige"),
        ("grey", "navy"),

        # Harmonious Combination
        ("blue", "white"),
        ("blue", "grey"),
        ("blue", "beige"),
        ("blue", "navy"),

        ("red", "black"),
        ("red", "white"),
        ("red", "grey"),
        ("red", "navy"),

        ("green", "white"),
        ("green", "beige"),
        ("green", "brown"),

        ("yellow", "black"),
        ("yellow", "white"),
        ("yellow", "grey"),
        ("yellow", "navy"),

        ("brown", "white"),
        ("brown", "beige"),
        ("brown", "navy"),

        ("pink", "white"),
        ("pink", "grey"),
        ("pink", "black"),

        ("purple", "white"),
        ("purple", "grey"),
        ("purple", "black")
    }

    
    # =====================================================
    # KNOWLEDGE BASE STYLE
    # =====================================================

    STYLE_COMPAT = {

        ("casual", "casual"): 20,
        ("formal", "formal"): 20,
        ("sporty", "sporty"): 20,
        ("streetwear", "streetwear"): 20,

        ("casual", "streetwear"): 15,
        ("streetwear", "casual"): 15,

        ("casual", "sporty"): 12,
        ("sporty", "casual"): 12,

        ("casual", "formal"): 9,
        ("formal", "casual"): 9
    }

    # =====================================================
    # KNOWLEDGE BASE OCCASION
    # =====================================================

    OCCASION_COMPAT = {

        "campus": {
            "campus",
            "hangout"
        },

        "work": {
            "work"
        },

        "hangout": {
            "hangout",
            "campus",
            "travel"
        },

        "sport": {
            "sport"
        },

        "travel": {
            "travel",
            "hangout"
        }
    }

    def __init__(self):
        self.wardrobe_service = WardrobeService()

    # =====================================================
    # COLOR SCORE
    # Bobot maksimum = 42.5
    # =====================================================

    def calculate_color_score(
        self,
        color1: str,
        color2: str
    ) -> float:

        c1 = color1.lower().strip()
        c2 = color2.lower().strip()

        # Monochromatic / Color Harmony
        if (
            c1 == c2 or
            (c1, c2) in self.COLOR_HARMONY or
            (c2, c1) in self.COLOR_HARMONY
        ):
            return 42.5

        # Salah satu warna netral
        if (
            c1 in self.NEUTRAL_COLORS or
            c2 in self.NEUTRAL_COLORS
        ):
            return 32.5

        # Kombinasi lainnya
        return 21.0
    

    # =====================================================
    # STYLE SCORE
    # Bobot maksimum = 20
    # =====================================================

    def calculate_style_score(
        self,
        style1: str,
        style2: str
    ) -> float:

        key = (
            style1.lower().strip(),
            style2.lower().strip()
        )

        if key in self.STYLE_COMPAT:
            return float(self.STYLE_COMPAT[key])

        # Style yang tidak memiliki hubungan
        return 6.0

    # =====================================================
    # OCCASION SCORE
    # Bobot maksimum = 37.5
    # =====================================================

    def calculate_occasion_score(
        self,
        activities1: str,
        activities2: str
    ) -> float:

        acts1 = {
            a.strip().lower()
            for a in activities1.split(",")
            if a.strip()
        }

        acts2 = {
            a.strip().lower()
            for a in activities2.split(",")
            if a.strip()
        }

        # Aktivitas sama
        if acts1 & acts2:
            return 37.5

        # Aktivitas masih berhubungan
        for act in acts1:

            related = self.OCCASION_COMPAT.get(
                act,
                set()
            )

            if related.intersection(acts2):
                return 25.5

        # Tidak memiliki hubungan
        return 12.0

    # =====================================================
    # TOTAL SCORE
    # Maksimum = 100
    # =====================================================

    def calculate_score(
        self,
        item: dict,
        candidate: dict
    ) -> dict:

        color_score = self.calculate_color_score(
            item.get("color", ""),
            candidate.get("color", "")
        )

        occasion_score = self.calculate_occasion_score(
            item.get("occasion"),
            candidate.get("occasion")
        )

        style_score = self.calculate_style_score(
            item.get("style", ""),
            candidate.get("style", "")
        )

        total_score = round(
            color_score +
            occasion_score +
            style_score,
            2
        )

        return {

            "color_score": color_score,

            "occasion_score": occasion_score,

            "style_score": style_score,

            "total_score": total_score

        }
        
    # =====================================================
    # GENERATE REASON
    # =====================================================

    def generate_reason(self, score_detail: dict):

        reasons = []

        if score_detail["color_score"] >= 40:
            reasons.append("Kombinasi warna sangat serasi.")

        elif score_detail["color_score"] >= 30:
            reasons.append("Warna masih cukup cocok.")

        if score_detail["style_score"] >= 18:
            reasons.append("Style pakaian saling melengkapi.")

        elif score_detail["style_score"] >= 10:
            reasons.append("Style pakaian masih sesuai.")

        if score_detail["occasion_score"] >= 35:
            reasons.append("Sesuai untuk aktivitas yang sama.")

        elif score_detail["occasion_score"] >= 20:
            reasons.append("Masih cocok digunakan pada aktivitas serupa.")

        return " ".join(reasons)
    
    
    # =====================================================
    # GET RECOMMENDATIONS
    # =====================================================

    def get_recommendations(
        self,
        user_id: str,
        item_id: str
    ):

        selected_item = self.wardrobe_service.get_item_by_id(
            user_id,
            item_id
        )

        if not selected_item:
            return None

        category = selected_item.get("category")

        if category == "Tops":
            candidate_category = "Bottoms"
        else:
            candidate_category = "Tops"

        candidates = self.wardrobe_service.get_items_by_category(
            user_id,
            candidate_category
        )

        results = []

        for candidate in candidates:

            score_detail = self.calculate_score(
                selected_item,
                candidate
            )

            score_detail["normalized_score"] = round(
                score_detail["total_score"],
                2
            )

            results.append({

                "item": candidate,

                "score_detail": score_detail,

                "reason": self.generate_reason(score_detail)

            })

        results.sort(
            key=lambda x: x["score_detail"]["total_score"],
            reverse=True
        )

        return {

            "selected_item": selected_item,

            "recommendations": results[:3],

            "total_candidates": len(results)

        }