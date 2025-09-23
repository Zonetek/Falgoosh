from .strategies import ScanQuotaStrategy, QueryQuotaStrategy


class QuotaService:
    STRATEGIES = {
        "scan": ScanQuotaStrategy(),
        "query": QueryQuotaStrategy(),
    }

    @classmethod
    def consume(cls, user, resource: str, count=1) -> bool:
        strategy = cls.STRATEGIES.get(resource)
        if not strategy:
            raise ValueError(f"No quota strategy for resource: {resource}")
        return strategy.consume(user, count)
