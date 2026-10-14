from django.db import models

# Create your models here.

class CoreUsers(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Core_users'


class Usermodule(models.Model):
    moduleid = models.AutoField(db_column='ModuleID', primary_key=True)  # Field name made lowercase.
    userid = models.IntegerField(db_column='UserID', blank=True, null=True)  # Field name made lowercase.
    modulename = models.CharField(db_column='ModuleName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    module_url = models.CharField(db_column='Module_url', max_length=50, blank=True, null=True)  # Field name made lowercase.
    showmodule = models.BooleanField(db_column='ShowModule', blank=True, null=True)  # Field name made lowercase.
    can_module_add = models.BooleanField(blank=True, null=True)
    can_module_edit = models.BooleanField(blank=True, null=True)
    can_module_delete = models.BooleanField(blank=True, null=True)
    is_admin = models.BooleanField(blank=True, null=True)
    displayorder = models.IntegerField(db_column='DisplayOrder')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'UserModule'


class Userpage(models.Model):
    moduleid = models.ForeignKey('Usermodule', models.DO_NOTHING, db_column='ModuleID', blank=True, null=True)  # Field name made lowercase.
    userid = models.IntegerField(db_column='UserID', blank=True, null=True)  # Field name made lowercase.
    modulename = models.CharField(db_column='ModuleName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    pageid = models.AutoField(db_column='PageId', primary_key=True)  # Field name made lowercase.
    pagename = models.CharField(db_column='PageName', max_length=50, blank=True, null=True)  # Field name made lowercase.
    pageurl = models.CharField(db_column='Pageurl', max_length=50, blank=True, null=True)  # Field name made lowercase.
    showpage = models.BooleanField(db_column='ShowPage', blank=True, null=True)  # Field name made lowercase.
    can_page_add = models.BooleanField(db_column='can_Page_add', blank=True, null=True)  # Field name made lowercase.
    can_page_edit = models.BooleanField(db_column='can_Page_edit', blank=True, null=True)  # Field name made lowercase.
    can_page_delete = models.BooleanField(db_column='can_Page_delete', blank=True, null=True)  # Field name made lowercase.
    is_admin = models.BooleanField(blank=True, null=True)
    displayorder = models.IntegerField(db_column='DisplayOrder')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'UserPage'

class Parties(models.Model):
    code = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=50, blank=True, null=True)
    owner_name = models.CharField(max_length=50, blank=True, null=True)
    number = models.CharField(max_length=50, blank=True, null=True)
    party_type = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    entry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'parties'



class ExpenseHead(models.Model):
    code = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    entry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'expense_head'


class BroilerRate(models.Model):
    date = models.DateField(blank=True, null=True)
    rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'broiler_rate'


class FatRate(models.Model):
    month = models.CharField(max_length=50, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    rate = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'fat_rate'


class WasteRate(models.Model):
    month = models.CharField(max_length=50, blank=True, null=True)
    year = models.CharField(max_length=50, blank=True, null=True)
    rate = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True 
        db_table = 'waste_rate'


class PurchaseReceiving(models.Model):
    id = models.BigAutoField(primary_key=True)
    purchase_number = models.CharField(db_column='Purchase_number', max_length=50, blank=True, null=True)  # Field name made lowercase.
    vendor_code = models.CharField(max_length=45, blank=True, null=True)
    vendor_name = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    vendor_rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    market_rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    weight = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    remaining_weight = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    payed_amount = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    remaining_amount = models.GeneratedField(
        expression=models.F('amount') - models.F('payed_amount'),
        output_field=models.DecimalField(max_digits=18, decimal_places=0),
        db_persist=True,
    )
    discription = models.CharField(max_length=450, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_receiving'




class SellsInvoice(models.Model):
    id = models.BigAutoField(primary_key=True)
    purchase_number = models.CharField(max_length=50, blank=True, null=True)
    sells_no = models.CharField(max_length=50, blank=True, null=True)
    customer_code = models.CharField(max_length=45, blank=True, null=True)
    customer_name = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    rate = models.CharField(max_length=50, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    received_amount = models.CharField(max_length=50, blank=True, null=True)
    remaining_amount = models.CharField(max_length=50, blank=True, null=True)
    vehicle_no = models.CharField(max_length=50, blank=True, null=True)
    entry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sells_invoice'


        
class Sellspayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    sell_no = models.CharField(max_length=50, blank=True, null=True)
    customer_code = models.CharField(max_length=45, blank=True, null=True)
    customer_name = models.CharField(max_length=50, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    rate = models.CharField(max_length=50, blank=True, null=True)
    vehicle_no = models.CharField(max_length=50, blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    received_amount = models.CharField(max_length=50, blank=True, null=True)
    description = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    entry_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sellspayment'


class Mortality(models.Model):
    purchase_no = models.CharField(max_length=50, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    weight = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    entry_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Mortality'



class PurchasePayments(models.Model):
    # id = models.BigAutoField(primary_key=True)
    purchase_number = models.CharField(max_length=50, blank=True, null=True)
    party_code = models.CharField(max_length=45, blank=True, null=True)
    part_name = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    payment_mood = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_payments'


class Expensedetail(models.Model):
    head_code = models.CharField(max_length=50, blank=True, null=True)
    head_name = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    amount = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'expensedetail'



class PurchaseReceivingView(models.Model):
    # id = models.AutoField()
    purchase_number = models.CharField(db_column='Purchase_number', max_length=50, blank=True, null=True)  # Field name made lowercase.
    vendor_name = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    vendor_rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    market_rate = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    weight = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    remaining_weight = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    payed_amount = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    remaining_amount = models.DecimalField(max_digits=19, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Purchase_receiving_view'


class PurchasePaymentHistory(models.Model):
    party_code = models.CharField(max_length=45, blank=True, null=True)
    party_name = models.CharField(max_length=50)
    date = models.DateTimeField(blank=True, null=True)
    totall_amount = models.IntegerField(blank=True, null=True)
    payed_amount = models.IntegerField(blank=True, null=True)
    due = models.IntegerField(blank=True, null=True)
    advanced = models.IntegerField(blank=True, null=True)
    remarks = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_payment_history'





class ReceiptHistory(models.Model):
    party_name = models.CharField(max_length=45, blank=True, null=True)
    part_code = models.CharField(max_length=45, blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)
    received_amount = models.CharField(max_length=45, blank=True, null=True)
    payment_method = models.CharField(max_length=45, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    due = models.IntegerField(blank=True, null=True)
    advance = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'receipt_history'


class CashRecord(models.Model):
    # id = models.IntegerField(primary_key=True)
    cash_in_hand = models.IntegerField(blank=True, null=True)
    cash_in_bank = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    discription = models.CharField(max_length=450, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cash_record'


class ChartOfAccount(models.Model):
    LEVEL_CHOICES = (
        (1, 'Level 1 - Main Class'),
        (2, 'Level 2 - Control Head'),
        (3, 'Level 3 - Sub Control'),
        (4, 'Level 4 - Transactional Account'),
    )
    ACCOUNT_TYPE_CHOICES = (
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Revenue', 'Revenue'),
        ('Expense', 'Expense'),
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPE_CHOICES)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'chart_of_accounts'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} (L{self.level})"


class Voucher(models.Model):
    VOUCHER_TYPES = (
        ('Payment Voucher', 'Payment Voucher (Cash/Bank Out)'),
        ('Receipt Voucher', 'Receipt Voucher (Cash/Bank In)'),
        ('Transfer Voucher', 'Transfer / Journal Voucher (Head to Head)'),
    )

    voucher_no = models.CharField(max_length=50, unique=True)
    voucher_type = models.CharField(max_length=50, choices=VOUCHER_TYPES)
    date = models.DateField()
    reference_no = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'vouchers'
        ordering = ['-id']

    def __str__(self):
        return f"{self.voucher_no} ({self.voucher_type}) - Rs. {self.total_amount}"


class VoucherDetail(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='details')
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='voucher_lines')
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    narration = models.CharField(max_length=255, blank=True, null=True)
    party = models.ForeignKey(Parties, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'voucher_details'

    def __str__(self):
        return f"{self.voucher.voucher_no} - {self.account.name} (Dr:{self.debit}, Cr:{self.credit})"