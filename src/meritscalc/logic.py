class MeritsCalculator:
    def __init__(
        self,
        merits_to_seconds_rate: float = 1.0,
        merits_to_auec_rate: float = 0.618,
    ):
        self.merits_to_seconds_rate = merits_to_seconds_rate
        self.merits_to_auec_rate = merits_to_auec_rate

    def merits_to_time(self, merits: float):
        total_seconds = merits * self.merits_to_seconds_rate
        return self._format_time(total_seconds)

    def time_to_merits(self, hours: float, minutes: float, seconds: float) -> float:
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        if self.merits_to_seconds_rate == 0:
            return 0
        return total_seconds / self.merits_to_seconds_rate

    def merits_to_auec(self, merits: float) -> float:
        return merits * self.merits_to_auec_rate

    def auec_to_merits(self, auec: float) -> float:
        if self.merits_to_auec_rate == 0:
            return 0
        return auec / self.merits_to_auec_rate

    def apply_fee(self, base_amount: float, fee_percent: float) -> float:
        if base_amount < 0:
            return 0
        fee = base_amount * (fee_percent / 100.0)
        return base_amount + fee

    def total_with_fee(
        self,
        base_amount: float,
        fee_percent: float,
        additional_charges: float,
        discount_percent: float,
    ) -> float:
        subtotal = self.apply_fee(base_amount, fee_percent) + additional_charges
        discount = subtotal * (max(0.0, discount_percent) / 100.0)
        return max(0.0, round(subtotal - discount, 2))

    def _format_time(self, seconds: float):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return int(h), int(m), int(s)
