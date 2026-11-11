"""Session currency and owned materials."""


MATERIAL_PRICES = {"mat_01": 8, "mat_02": 12, "mat_03": 4}


class GameState:
    def __init__(self):
        self.coins = 100
        self.materials = {name: 0 for name in MATERIAL_PRICES}

    def purchase_status(self, material, quantity):
        if material not in MATERIAL_PRICES:
            return False, "구매할 수 없는 재료입니다."
        if type(quantity) is not int or quantity < 1:
            return False, "구매 수량은 1개 이상이어야 합니다."
        cost = MATERIAL_PRICES[material] * quantity
        if self.coins < cost:
            return False, "코인이 부족합니다."
        return True, ""

    def purchase(self, material, quantity):
        available, reason = self.purchase_status(material, quantity)
        if not available:
            return False, reason
        self.coins -= MATERIAL_PRICES[material] * quantity
        self.materials[material] += quantity
        return True, f"재료 {quantity}개를 구매했습니다."
