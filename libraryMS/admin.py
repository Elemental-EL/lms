from datetime import timezone

from django.contrib import admin
from .tasks import generate_report

from libraryMS.models import BorrowingTransaction, Reservation, Book, Borrower, Report, Notification, Review, Author

# Register your models here.
admin.site.register(BorrowingTransaction)
admin.site.register(Reservation)
admin.site.register(Book)
admin.site.register(Borrower)
admin.site.register(Notification)
admin.site.register(Review)
admin.site.register(Author)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'status', 'created_at', 'generated_by', 'file')

    def generate_report(self, request, queryset):
        for report in queryset:
            # Trigger Celery task to generate the report
            generate_report.delay(report.id)
            report.status = "pending"
            report.save()

        self.message_user(request, "Reports generation initiated.")

    actions = [generate_report]

    def save_model(self, request, obj, form, change):
        if not obj.id:
            obj.generated_by = request.user  # Automatically set the admin who created the report
        super().save_model(request, obj, form, change)


admin.site.register(Report, ReportAdmin)
