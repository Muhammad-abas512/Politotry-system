import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'politory.settings')
django.setup()

from django.db import connection, transaction
from core.models import (
    VoucherDetail,
    Voucher,
    SellsInvoice,
    Sellspayment,
    PurchasePaymentHistory,
    PurchasePayments,
    PurchaseReceiving,
    ReceiptHistory,
    CashRecord,
    Expensedetail,
    Mortality,
    ChartOfAccount,
    Parties,
    CoreUsers,
    Usermodule,
    Userpage,
)

def clean_database():
    print("=" * 60)
    print("STARTING DATABASE TRANSACTIONAL CLEANUP")
    print("=" * 60)

    tables_to_clear = [
        ('voucher_details', VoucherDetail),
        ('vouchers', Voucher),
        ('sells_invoice', SellsInvoice),
        ('sellspayment', Sellspayment),
        ('purchase_payment_history', PurchasePaymentHistory),
        ('purchase_payments', PurchasePayments),
        ('purchase_receiving', PurchaseReceiving),
        ('receipt_history', ReceiptHistory),
        ('cash_record', CashRecord),
        ('expensedetail', Expensedetail),
        ('mortality', Mortality),
    ]

    print("\n--- PRE-CLEAN ROW COUNTS ---")
    for tbl_name, model_cls in tables_to_clear:
        count = model_cls.objects.count()
        print(f"  {tbl_name}: {count} records")

    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        with transaction.atomic():
            for tbl_name, model_cls in tables_to_clear:
                deleted_count, _ = model_cls.objects.all().delete()
                print(f"Deleted from {tbl_name}: {deleted_count}")

            # Reset AUTO_INCREMENT for each cleared table
            for tbl_name, _ in tables_to_clear:
                try:
                    cursor.execute(f"ALTER TABLE `{tbl_name}` AUTO_INCREMENT = 1;")
                except Exception as e:
                    print(f"Notice: Could not reset AUTO_INCREMENT for {tbl_name}: {e}")

            # Reset Chart of Accounts balances
            updated_coa = ChartOfAccount.objects.all().update(
                opening_balance=Decimal('0.00'),
                current_balance=Decimal('0.00')
            )
            print(f"Reset balances to 0.00 on {updated_coa} Chart of Account heads.")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    print("\n--- POST-CLEAN ROW COUNTS ---")
    for tbl_name, model_cls in tables_to_clear:
        count = model_cls.objects.count()
        print(f"  {tbl_name}: {count} records")

    print("\n--- PRESERVED MASTER & SYSTEM DATA ---")
    print(f"  Parties: {Parties.objects.count()} (Preserved)")
    print(f"  Chart of Accounts: {ChartOfAccount.objects.count()} (Preserved, all balances 0.00)")
    print(f"  Core Users: {CoreUsers.objects.count()} (Preserved: {[u.name for u in CoreUsers.objects.all()]})")
    print(f"  User Modules: {Usermodule.objects.count()} (Preserved)")
    print(f"  User Pages: {Userpage.objects.count()} (Preserved)")
    print("=" * 60)
    print("DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    clean_database()
