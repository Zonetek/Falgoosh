from .strategies import ScanQuotaStrategy, QueryQuotaStrategy, ReportQuotaStrategy


class QuotaService:
    STRATEGIES = {
        "scan": ScanQuotaStrategy(),
        "query": QueryQuotaStrategy(),
        "report": ReportQuotaStrategy(),
    }

    @classmethod
    def consume(cls, user, resource: str, count=1) -> bool:
        strategy = cls.STRATEGIES.get(resource)
        if not strategy:
            raise ValueError(f"No quota strategy for resource: {resource}")
        return strategy.consume(user, count)
