"""
Classify Emails Management Command
===================================

Django management command for batch email classification.
"""
from django.core.management.base import BaseCommand, CommandError
from gmail_integration.models import EmailMessage
from ai.services.email_classification_service import EmailClassificationService
from ai.models import Prediction
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Classify emails using the daycare invoice classifier'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Classify all emails in database'
        )
        
        parser.add_argument(
            '--unclassified-only',
            action='store_true',
            help='Only classify emails without existing predictions'
        )
        
        parser.add_argument(
            '--retrain',
            action='store_true',
            help='Retrain model before classifying'
        )
        
        parser.add_argument(
            '--email-ids',
            nargs='+',
            type=int,
            help='Specific email IDs to classify'
        )
    
    def handle(self, *args, **options):
        try:
            # Check if model exists
            stats = EmailClassificationService.get_training_statistics()
            if not stats.get('model_version'):
                raise CommandError(
                    'No trained model found. Please train the model first using: '
                    'python manage.py train_daycare_classifier'
                )
            
            # Retrain if requested
            if options['retrain']:
                self.stdout.write('Retraining model...')
                try:
                    result = EmailClassificationService.train_from_samples(min_samples=10)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Model retrained successfully. Version: {result["model_version"]}, '
                            f'Accuracy: {result["metrics"].get("accuracy", 0):.3f}'
                        )
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Retraining failed: {e}'))
                    raise CommandError(f'Cannot proceed without trained model: {e}')
            
            # Determine which emails to classify
            if options['email_ids']:
                # Specific emails
                emails = EmailMessage.objects.filter(id__in=options['email_ids'])
                self.stdout.write(f'Classifying {len(options["email_ids"])} specific emails...')
                
            elif options['unclassified_only']:
                # Only emails without predictions
                email_ct = ContentType.objects.get_for_model(EmailMessage)
                classified_email_ids = Prediction.objects.filter(
                    content_type=email_ct
                ).values_list('object_id', flat=True)
                
                emails = EmailMessage.objects.exclude(id__in=classified_email_ids)
                self.stdout.write(f'Found {emails.count()} unclassified emails...')
                
            elif options['all']:
                # All emails
                emails = EmailMessage.objects.all()
                self.stdout.write(f'Classifying all {emails.count()} emails...')
                
            else:
                raise CommandError(
                    'Please specify --all, --unclassified-only, or --email-ids'
                )
            
            # Classify emails
            success_count = 0
            error_count = 0
            invoice_count = 0
            not_invoice_count = 0
            
            for email in emails:
                try:
                    result = EmailClassificationService.classify_email(
                        email.id,
                        save_prediction=True
                    )
                    
                    success_count += 1
                    
                    if result['prediction'] == 'daycare_invoice':
                        invoice_count += 1
                    else:
                        not_invoice_count += 1
                    
                    # Show progress
                    if success_count % 10 == 0:
                        self.stdout.write(
                            f'Processed {success_count} emails... '
                            f'(Invoices: {invoice_count}, Not Invoices: {not_invoice_count})'
                        )
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Failed to classify email {email.id}: {e}')
                    )
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Classification complete!\n'
                    f'Total processed: {success_count}\n'
                    f'Daycare invoices found: {invoice_count}\n'
                    f'Not invoices: {not_invoice_count}\n'
                    f'Errors: {error_count}'
                )
            )
            
            # Show next steps
            if success_count > 0:
                self.stdout.write(
                    '\nNext steps:\n'
                    '1. Review predictions: python manage.py runserver → /ai/emails/review/\n'
                    '2. Confirm or reject predictions to improve the model\n'
                    '3. Model will automatically retrain after enough feedback'
                )
        
        except Exception as e:
            raise CommandError(f'Classification failed: {e}')
