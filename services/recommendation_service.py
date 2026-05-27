from services.wardrobe_service import WardrobeService


class RecommendationService:

    # ── ATURAN KOMPATIBILITAS WARNA ──
    NEUTRAL_COLORS = {"black", "white", "grey", "beige", "navy"}
    COLOR_HARMONY = {
        ("blue", "white"), ("blue", "grey"), ("blue", "beige"),
        ("red", "black"), ("red", "white"), ("red", "grey"),
        ("green", "beige"), ("green", "brown"), ("green", "white"),
        ("yellow", "white"), ("yellow", "black"), ("yellow", "grey"),
        ("brown", "beige"), ("brown", "white"), ("brown", "navy"),
        ("pink", "white"), ("pink", "grey"), ("pink", "black"),
        ("purple", "white"), ("purple", "grey"), ("purple", "black"),
    }

    # ── ATURAN KOMPATIBILITAS POLA ──
    PATTERN_SCORES = {
        ("solid", "solid"): 25,
        ("solid", "stripe"): 20,
        ("solid", "floral"): 20,
        ("solid", "plaid"): 18,
        ("solid", "graphic"): 15,
        ("stripe", "solid"): 20,
        ("floral", "solid"): 20,
        ("plaid", "solid"): 18,
        ("graphic", "solid"): 15,
        ("stripe", "stripe"): 5,
        ("floral", "floral"): 5,
    }

    # ── ATURAN KOMPATIBILITAS STYLE ──
    STYLE_COMPAT = {
        ("casual", "casual"): 15,
        ("formal", "formal"): 15,
        ("sporty", "sporty"): 15,
        ("streetwear", "streetwear"): 15,
        ("casual", "streetwear"): 10,
        ("streetwear", "casual"): 10,
        ("formal", "casual"): 5,
        ("casual", "formal"): 5,
    }

    def __init__(self):
        self.wardrobe_service = WardrobeService()

    def calculate_color_score(self, color1: str, color2: str) -> float:
        """
        Menghitung skor kompatibilitas warna (maks 45 poin)
        - 30 poin jika salah satu warna adalah netral
        - 45 poin jika kombinasi warna ada di COLOR_HARMONY
        - 15 poin jika warna sama
        """
        c1, c2 = color1.lower(), color2.lower()
        if (c1, c2) in self.COLOR_HARMONY or (c2, c1) in self.COLOR_HARMONY:
            return 45.0
        if c1 in self.NEUTRAL_COLORS or c2 in self.NEUTRAL_COLORS:
            return 30.0
        if c1 == c2:
            return 15.0
        return 10.0

    def calculate_pattern_score(self, pattern1: str, pattern2: str) -> float:
        """
        Menghitung skor kompatibilitas pola (maks 25 poin)
        berdasarkan PATTERN_SCORES lookup table
        """
        key = (pattern1.lower(), pattern2.lower())
        return float(self.PATTERN_SCORES.get(key, 8))

    def calculate_occasion_score(self, activities1: str, activities2: str) -> float:
        """
        Menghitung skor kesesuaian kesempatan pemakaian (maks 30 poin)
        berdasarkan jumlah kesamaan aktivitas antara dua item
        """
        acts1 = set(activities1.lower().split(","))
        acts2 = set(activities2.lower().split(","))
        common = acts1.intersection(acts2)
        if not common:
            return 5.0
        ratio = len(common) / max(len(acts1), len(acts2))
        return round(ratio * 30, 2)

    def calculate_style_score(self, style1: str, style2: str) -> float:
        """
        Menghitung skor keselarasan gaya berpakaian (maks 15 poin)
        berdasarkan STYLE_COMPAT lookup table
        """
        key = (style1.lower(), style2.lower())
        return float(self.STYLE_COMPAT.get(key, 3))

    def calculate_score(self, item: dict, candidate: dict) -> dict:
        """
        Menghitung total skor kompatibilitas menggunakan
        fungsi calculate_score() dengan empat aturan:
        - color_score   maks 45 poin
        - pattern_score maks 25 poin
        - occasion_score maks 30 poin
        - style_score   maks 15 poin
        Total maksimal = 115 poin
        """
        color_score = self.calculate_color_score(
            item.get("color", ""), candidate.get("color", "")
        )
        pattern_score = self.calculate_pattern_score(
            item.get("pattern", ""), candidate.get("pattern", "")
        )
        occasion_score = self.calculate_occasion_score(
            item.get("activities", ""), candidate.get("activities", "")
        )
        style_score = self.calculate_style_score(
            item.get("style", ""), candidate.get("style", "")
        )
        total = color_score + pattern_score + occasion_score + style_score

        # Normalisasi skor ke skala 0-100
        normalized = round((total / 115) * 100, 2)

        return {
            "color_score": color_score,
            "pattern_score": pattern_score,
            "occasion_score": occasion_score,
            "style_score": style_score,
            "total_score": total,
            "normalized_score": normalized
        }

    def generate_reason(self, item: dict, candidate: dict, score_detail: dict) -> str:
        """
        Menyusun alasan pencocokan outfit berdasarkan
        aturan scoring yang terpenuhi menggunakan generate_reason()
        """
        reasons = []
        if score_detail["color_score"] >= 40:
            reasons.append(
                f"Kombinasi warna {item['color']} dan {candidate['color']} sangat serasi"
            )
        elif score_detail["color_score"] >= 25:
            reasons.append(
                f"Warna {item['color']} atau {candidate['color']} bersifat netral sehingga mudah dipadukan"
            )
        if score_detail["pattern_score"] >= 20:
            reasons.append(
                f"Kombinasi pola {item['pattern']} dengan {candidate['pattern']} terlihat harmonis"
            )
        if score_detail["occasion_score"] >= 20:
            reasons.append(
                f"Kedua item cocok digunakan untuk {item['activities']}"
            )
        if score_detail["style_score"] >= 12:
            reasons.append(
                f"Gaya {item['style']} dan {candidate['style']} saling melengkapi"
            )
        return ". ".join(reasons) if reasons else "Kombinasi outfit yang dapat dipadukan"

    def get_recommendations(self, user_id: str, item_id: str) -> dict:
        """
        SKPL-F-011, F-012, F-013:
        Menjalankan seluruh proses rekomendasi rule-based:
        1. Mengambil item yang dipilih dari Firebase
        2. Menentukan kategori lawan (tops → bottoms, bottoms → tops)
        3. Mengambil semua kandidat menggunakan get_items_by_category()
        4. Menghitung skor setiap pasangan menggunakan calculate_score()
        5. Mengurutkan menggunakan sorted(scores, key=lambda x: x["score"], reverse=True)
        6. Mengambil top_3 = sorted_scores[:3]
        7. Menyusun alasan menggunakan generate_reason()
        """
        # Ambil item yang dipilih
        selected_item = self.wardrobe_service.get_item_by_id(user_id, item_id)
        if not selected_item:
            return None

        # Tentukan kategori lawan
        selected_category = selected_item.get("category", "").lower()
        opposite_category = "Bottoms" if selected_category == "tops" else "Tops"

        # Ambil semua kandidat dari kategori lawan
        candidates = self.wardrobe_service.get_items_by_category(
            user_id, opposite_category
        )
        if not candidates:
            return None

        # Hitung skor setiap pasangan
        scores = []
        for candidate in candidates:
            score_detail = self.calculate_score(selected_item, candidate)
            reason = self.generate_reason(selected_item, candidate, score_detail)
            scores.append({
                "item": candidate,
                "score_detail": score_detail,
                "reason": reason
            })

        # Urutkan secara descending berdasarkan normalized_score
        sorted_scores = sorted(
            scores,
            key=lambda x: x["score_detail"]["normalized_score"],
            reverse=True
        )

        # Ambil top 3
        top_3 = sorted_scores[:3]

        return {
            "selected_item": selected_item,
            "recommendations": top_3,
            "total_candidates": len(candidates)
        }
