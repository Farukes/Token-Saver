from __future__ import annotations

from token_saver.tools.symbol_index import SymbolIndexer, find_symbol_global


def test_symbol_extraction():
    python_code = """
class UserService:
    def authenticate(self, user, token):
        pass

def global_helper():
    pass
"""
    symbols = SymbolIndexer.extract_symbols_from_code(python_code, "python", "src/user.py")
    names = [s.name for s in symbols]
    assert "UserService" in names
    assert "authenticate" in names
    assert "global_helper" in names


def test_symbol_extraction_multi_lang():
    ruby_code = """
class BillingManager
  def process_invoice(id)
    puts id
  end
end
"""
    symbols_rb = SymbolIndexer.extract_symbols_from_code(ruby_code, "ruby", "lib/billing.rb")
    names_rb = [s.name for s in symbols_rb]
    assert "BillingManager" in names_rb
    assert "process_invoice" in names_rb

    kotlin_code = """
class PushNotifier {
    fun sendAlert(msg: String) {
        println(msg)
    }
}
"""
    symbols_kt = SymbolIndexer.extract_symbols_from_code(kotlin_code, "kotlin", "app/Notifier.kt")
    names_kt = [s.name for s in symbols_kt]
    assert "PushNotifier" in names_kt
    assert "sendAlert" in names_kt


def test_find_symbol_global(tmp_path):
    src_file = tmp_path / "app.py"
    src_file.write_text(
        """
class OrderProcessor:
    def process_order(self, order_id):
        pass

def calculate_tax(amount):
    return amount * 0.20
""",
        encoding="utf-8",
    )

    out1 = find_symbol_global("OrderProcessor", str(tmp_path))
    assert "OrderProcessor" in out1
    assert "CLASS" in out1
    assert "app.py" in out1

    out2 = find_symbol_global("calculate_tax", str(tmp_path), exact=True)
    assert "calculate_tax" in out2
    assert "FUNCTION" in out2

    out3 = find_symbol_global("NonExistentSymbol", str(tmp_path))
    assert "No symbols found" in out3
