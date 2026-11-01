"""Tests for the amount_eur backfill migration."""

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

MIGRATION_PATH = (
    Path(__file__).parents[2]
    / "alembic/versions/b9d4e2a7c1f3_backfill_amount_eur_for_non_eur_transactions.py"
)


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("backfill_amount_eur", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revises_current_head() -> None:
    assert _load_migration().down_revision == "f82a429f3da9"


def test_upgrade_updates_only_broken_bgn_and_usd_rows() -> None:
    migration = _load_migration()
    with patch.object(migration, "op", MagicMock()) as mock_op:
        migration.upgrade()

    statements = [str(call.args[0]) for call in mock_op.execute.call_args_list]
    assert len(statements) == 2
    bgn = next(s for s in statements if "currency = 'BGN'" in s)
    usd = next(s for s in statements if "currency = 'USD'" in s)
    assert "amount / 1.95583" in bgn
    assert "amount * 0.92" in usd
    assert "amount_eur = amount" in bgn
    assert "amount_eur = amount" in usd
    assert not any("'EUR'" in s for s in statements)


def test_downgrade_is_noop() -> None:
    migration = _load_migration()
    with patch.object(migration, "op", MagicMock()) as mock_op:
        migration.downgrade()

    mock_op.execute.assert_not_called()
    assert mock_op.mock_calls == []
