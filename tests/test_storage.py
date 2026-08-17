import pandas as pd

from vnstocklab.analysis.alerts import AlertEvent, AlertRule, AlertSnapshot
from vnstocklab.analysis.portfolio import PortfolioTransaction
from vnstocklab.storage import SQLiteRepository


def test_repository_persists_portfolio_and_alert_data(tmp_path) -> None:
    path = tmp_path / "vnstocklab.db"
    repository = SQLiteRepository(path)
    transaction = PortfolioTransaction(pd.Timestamp("2026-01-05"), "FPT", "Mua", 100, 100.0, 15.0)
    repository.add_portfolio_transaction(transaction)
    repository.upsert_alert_rule(AlertRule("FPT", 90, 120, 65))
    repository.upsert_alert_snapshots({"FPT": AlertSnapshot("NẮM GIỮ", "Tăng", score=70)})
    event = AlertEvent(
        "event-1",
        pd.Timestamp("2026-01-06"),
        "FPT",
        "Mục tiêu",
        "Cao",
        "Đã chạm mục tiêu",
        120,
        70,
    )
    repository.add_alert_events(iter([event, event]))
    repository.set_metadata("breadth_state", "Tích cực")

    reopened = SQLiteRepository(path)
    assert reopened.list_portfolio_transactions() == [transaction]
    assert reopened.list_alert_rules() == [AlertRule("FPT", 90, 120, 65)]
    assert reopened.list_alert_snapshots()["FPT"].trend == "Tăng"
    assert reopened.list_alert_snapshots()["FPT"].score == 70
    assert reopened.list_alert_events() == [event]
    assert reopened.get_metadata("breadth_state") == "Tích cực"

    reopened.delete_last_portfolio_transaction()
    reopened.delete_alert_rule("FPT")
    reopened.clear_alert_events()
    assert reopened.list_portfolio_transactions() == []
    assert reopened.list_alert_rules() == []
    assert reopened.list_alert_events() == []
