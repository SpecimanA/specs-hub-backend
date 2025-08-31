# sales/models.py
from django.db import models
from django.conf import settings
from crm.models import Account, Currency, Incoterm, PaymentTerm
from products.models import Product
from smart_selects.db_fields import ChainedForeignKey
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Q # ייבוא Q עבור שאילתות מורכבות

class Pipeline(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="שם ה-Pipeline")
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "Pipeline", "Pipelines"

class Stage(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='stages', verbose_name="Pipeline")
    name = models.CharField(max_length=100, verbose_name="שם השלב")
    order = models.PositiveIntegerField(default=0)
    win_probability = models.FloatField(default=0.0)
    class Meta:
        ordering = ['pipeline', 'order']
        unique_together = ('pipeline', 'name')
        verbose_name, verbose_name_plural = "שלב", "שלבים"
    def __str__(self): return f"{self.pipeline.name} - {self.name}"

class LostReason(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="סיבת הפסד")
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "סיבת הפסד", "סיבות הפסד"

class Opportunity(models.Model):
    name = models.CharField(max_length=255, verbose_name="שם ה-Opportunity")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='opportunities', verbose_name="לקוח")
    opportunity_pipeline = models.ForeignKey(Pipeline, on_delete=models.SET_NULL, null=True, verbose_name="סוג Opportunity / Pipeline")
    stage = ChainedForeignKey(Stage, chained_field="opportunity_pipeline", chained_model_field="pipeline", show_all=False, auto_choose=True, sort=True, verbose_name="שלב", null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סכום (מתעדכן אוטומטית)")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, verbose_name="מטבע עסקה")
    total_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="עלויות (מתעדכן אוטומטית)")
    total_agent_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סה\"כ עמלת סוכן (מחושב)")
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="רווח כולל (מחושב)")
    profit_percentage = models.FloatField(default=0.0, verbose_name="% רווחיות (מחושב)")
    
    vat_percentage = models.FloatField(default=17.0, verbose_name="אחוז מע\"מ")
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סכום מע\"מ (מחושב)")
    total_with_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סה\"כ כולל מע\"מ (מחושב)")

    incoterm = models.ForeignKey(Incoterm, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="תנאי שילוח")
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="תנאי תשלום כלליים")
    
    close_date = models.DateField(verbose_name="תאריך סגירה צפוי")
    lost_reason = models.ForeignKey(LostReason, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="סיבת הפסד")
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")
    products = models.ManyToManyField(Product, through='OpportunityProduct', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='opportunities', verbose_name="אחראי")
    
    def save(self, *args, **kwargs):
        self.vat_amount = self.amount * (Decimal(self.vat_percentage) / Decimal(100))
        self.total_with_vat = self.amount + self.vat_amount
        super().save(*args, **kwargs)

    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "Opportunity", "Opportunities"

class OpportunityProduct(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="מוצר")
    item_description = models.TextField(blank=True, null=True, verbose_name="תיאור פריט")
    quantity = models.PositiveIntegerField(default=1, verbose_name="כמות")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="מחיר מכירה ליחידה")
    
    supplier_pn = models.CharField(max_length=100, blank=True, null=True, verbose_name="מק\"ט ספק")
    agent = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_vendor': True}, related_name='agent_deals', verbose_name="סוכן")
    agent_percentage = models.FloatField(default=0.0, verbose_name="% עמלת סוכן")

    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סך הכל שורה")
    line_profit_before_agent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="רווח לפני סוכן")
    line_profit_after_agent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="רווח אחרי סוכן")

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        purchase_cost = self.quantity * self.product.purchase_price
        self.line_profit_before_agent = self.line_total - purchase_cost
        agent_fee = self.line_total * (Decimal(self.agent_percentage) / Decimal(100))
        self.line_profit_after_agent = self.line_profit_before_agent - agent_fee
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.quantity} x {self.product.name}"
    class Meta: unique_together = ('opportunity', 'product')

class PaymentMilestone(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="payment_milestones")
    name = models.CharField(max_length=100, verbose_name="תיאור אבן דרך")
    percentage = models.FloatField(default=0.0, verbose_name="אחוז תשלום")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סכום (כולל מע\"מ, מחושב)")

    def save(self, *args, **kwargs):
        if self.opportunity.total_with_vat > 0:
            self.amount = self.opportunity.total_with_vat * (Decimal(self.percentage) / Decimal(100))
        else:
            self.amount = self.opportunity.amount * (Decimal(self.percentage) / Decimal(100))
        super().save(*args, **kwargs)


# --- מודלי יעדים חדשים ---

class GoalType(models.Model):
    """
    מגדיר סוגים שונים של יעדים שניתן להגדיר במערכת.
    לדוגמה: 'שווי עסקאות שנסגרו', 'מספר לידים שנוצרו', 'מספר שיחות שבוצעו'.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="שם סוג היעד")
    description = models.TextField(blank=True, verbose_name="תיאור")
    # האם היעד מבוסס על ערך כספי או כמותי
    is_financial = models.BooleanField(default=False, verbose_name="יעד כספי?")
    # יעד מבוסס על אובייקטים (לדוגמה, מספר עסקאות) או פעילויות
    is_activity_based = models.BooleanField(default=False, verbose_name="מבוסס פעילות?")
    # שדה לקישור לשדה ספציפי במודל אחר, אם רלוונטי
    # לדוגמה: 'amount' עבור Opportunity, 'call_count' עבור Activity
    related_field = models.CharField(max_length=100, blank=True, null=True, 
                                     help_text="שדה במודל קשור לחישוב התקדמות (לדוגמה: 'amount' ב-Opportunity)",
                                     verbose_name="שדה קשור")
    related_model = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="שם המודל הקשור (לדוגמה: 'Opportunity', 'Activity')",
                                     verbose_name="מודל קשור")

    class Meta:
        verbose_name = "סוג יעד"
        verbose_name_plural = "סוגי יעדים"

    def __str__(self):
        return self.name

class Goal(models.Model):
    """
    מודל המייצג יעד ספציפי שהוגדר במערכת.
    יכול להיות יעד אישי, קבוצתי או חברתי.
    """
    GOAL_LEVEL_CHOICES = [
        ('INDIVIDUAL', 'אישי'),
        ('TEAM', 'צוותי'),
        ('COMPANY', 'חברתי'),
    ]
    FREQUENCY_CHOICES = [
        ('DAILY', 'יומי'),
        ('WEEKLY', 'שבועי'),
        ('MONTHLY', 'חודשי'),
        ('QUARTERLY', 'רבעוני'),
        ('YEARLY', 'שנתי'),
    ]

    name = models.CharField(max_length=255, verbose_name="שם היעד")
    goal_type = models.ForeignKey(GoalType, on_delete=models.PROTECT, related_name='goals', verbose_name="סוג יעד")
    
    # הגדרת רמת היעד
    level = models.CharField(max_length=20, choices=GOAL_LEVEL_CHOICES, default='INDIVIDUAL', verbose_name="רמת יעד")
    
    # למי היעד משויך (אם אישי או צוותי)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='goals_owned', 
        verbose_name="בעל יעד (משתמש)"
    )
    # עבור יעדים צוותיים או חברתיים
    # team = models.ForeignKey('management.Team', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="צוות") 
    # (יש להוסיף מודל Team לאפליקציית Management אם רלוונטי)

    target_value = models.DecimalField(max_digits=15, decimal_places=2, 
                                       validators=[MinValueValidator(Decimal('0.00'))],
                                       verbose_name="ערך יעד")
    
    # תקופת היעד
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='MONTHLY', verbose_name="תדירות")
    start_date = models.DateField(verbose_name="תאריך התחלה")
    end_date = models.DateField(verbose_name="תאריך סיום")

    # קישור אופציונלי ל-Pipeline מסוים
    pipeline = models.ForeignKey('Pipeline', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pipeline קשור")

    is_active = models.BooleanField(default=True, verbose_name="פעיל?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="נוצר בתאריך")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="עודכן בתאריך")

    class Meta:
        verbose_name = "יעד"
        verbose_name_plural = "יעדים"
        # וודא שלא נוצרים יעדים כפולים עם אותו סוג, בעלים ותאריכים
        unique_together = ('name', 'goal_type', 'owner', 'pipeline', 'start_date', 'end_date')

    def __str__(self):
        return f"{self.name} ({self.get_level_display()}) - {self.target_value} {self.goal_type.name} by {self.end_date}"

    @property
    def current_progress(self):
        """
        מחשב את ההתקדמות הנוכחית של היעד בהתבסס על סוג היעד.
        """
        progress = Decimal('0.00')
        
        # סינון בסיסי לפי תאריכים, בעלים ו-pipeline
        queryset = Opportunity.objects.filter(
            close_date__range=(self.start_date, self.end_date),
            stage__win_probability=100, # רק עסקאות שנסגרו בהצלחה
        )

        if self.level == 'INDIVIDUAL' and self.owner:
            queryset = queryset.filter(owner=self.owner)
        # אם יש לך מודל Team באפליקציית Management וקישור ל-Goal
        # elif self.level == 'TEAM' and self.team:
        #     queryset = queryset.filter(owner__team=self.team)
        # אם אין מודל Team, ניתן לסנן לפי בעלים של GoalTarget
        elif self.level == 'TEAM':
            # עבור יעדים צוותיים ללא מודל Team מוגדר, נסכם את יעדי המשנה
            # זה דורש ש-GoalTarget יכיל את ההתקדמות האישית
            sub_target_progress = self.sub_targets.aggregate(Sum('current_progress'))['current_progress__sum']
            if sub_target_progress:
                progress += sub_target_progress
            
        if self.pipeline:
            queryset = queryset.filter(opportunity_pipeline=self.pipeline)

        if self.goal_type.related_model == 'Opportunity' and self.goal_type.related_field == 'amount':
            # יעד מבוסס על שווי עסקאות שנסגרו
            sum_amount = queryset.aggregate(Sum('amount'))['amount__sum']
            if sum_amount:
                progress += sum_amount
        elif self.goal_type.related_model == 'Opportunity' and self.goal_type.related_field == 'count':
            # יעד מבוסס על מספר עסקאות שנסגרו
            count_opportunities = queryset.count()
            progress += Decimal(str(count_opportunities))
        # הוסף כאן לוגיקה לסוגי יעדים נוספים (לדוגמה: לידים, פעילויות)
        # elif self.goal_type.related_model == 'Lead' and self.goal_type.related_field == 'count':
        #     from marketing.models import MarketingLead
        #     lead_queryset = MarketingLead.objects.filter(...)
        #     progress += Decimal(str(lead_queryset.count()))
        
        return progress

    @property
    def progress_percentage(self):
        """
        מחשב את אחוז ההתקדמות של היעד.
        """
        if self.target_value and self.target_value > 0:
            return float((self.current_progress / self.target_value) * 100)
        return 0.0

class GoalTarget(models.Model):
    """
    מודל המאפשר לפצל יעד (בדרך כלל יעד צוותי או חברתי) ליעדי משנה אישיים.
    """
    parent_goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='sub_targets', verbose_name="יעד אב")
    # למי יעד המשנה משויך
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_goal_targets',
        verbose_name="משויך ל"
    )
    target_value = models.DecimalField(max_digits=15, decimal_places=2, 
                                       validators=[MinValueValidator(Decimal('0.00'))],
                                       verbose_name="ערך יעד משנה")
    
    is_achieved = models.BooleanField(default=False, verbose_name="הושג?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="נוצר בתאריך")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="עודכן בתאריך")

    class Meta:
        verbose_name = "יעד משנה"
        verbose_name_plural = "יעדי משנה"
        unique_together = ('parent_goal', 'assignee') # כל משתמש יכול להיות משויך ליעד משנה אחד ליעד אב נתון

    def __str__(self):
        return f"{self.parent_goal.name} ל-{self.assignee} ({self.target_value})"

    @property
    def current_progress(self):
        """
        מחשב את ההתקדמות הנוכחית של יעד המשנה, בדומה ל-Goal, אך ממוקד למבצע.
        """
        progress = Decimal('0.00')
        
        # סינון בסיסי לפי תאריכים, מבצע ו-pipeline של יעד האב
        queryset = Opportunity.objects.filter(
            close_date__range=(self.parent_goal.start_date, self.parent_goal.end_date),
            stage__win_probability=100, # רק עסקאות שנסגרו בהצלחה
            owner=self.assignee, # ממוקד למבצע יעד המשנה
        )

        if self.parent_goal.pipeline:
            queryset = queryset.filter(opportunity_pipeline=self.parent_goal.pipeline)

        if self.parent_goal.goal_type.related_model == 'Opportunity' and self.parent_goal.goal_type.related_field == 'amount':
            sum_amount = queryset.aggregate(Sum('amount'))['amount__sum']
            if sum_amount:
                progress += sum_amount
        elif self.parent_goal.goal_type.related_model == 'Opportunity' and self.parent_goal.goal_type.related_field == 'count':
            count_opportunities = queryset.count()
            progress += Decimal(str(count_opportunities))
        
        return progress

    @property
    def progress_percentage(self):
        """
        מחשב את אחוז ההתקדמות של יעד המשנה.
        """
        if self.target_value and self.target_value > 0:
            return float((self.current_progress / self.target_value) * 100)
        return 0.0
