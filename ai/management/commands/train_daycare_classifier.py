"""
Train Daycare Classifier Management Command
============================================

Django management command for training the daycare invoice classifier.
"""
from django.core.management.base import BaseCommand, CommandError
from ai.services.email_classification_service import EmailClassificationService


class Command(BaseCommand):
    help = 'Train the daycare invoice email classifier from labeled samples'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--min-samples',
            type=int,
            default=10,
            help='Minimum number of training samples required (default: 10)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force training even if below minimum samples'
        )
    
    def handle(self, *args, **options):
        min_samples = options['min_samples']
        force = options['force']
        
        try:
            # Get current training statistics
            stats = EmailClassificationService.get_training_statistics()
            
            self.stdout.write('Training Data Statistics:')
            self.stdout.write(f'  Total samples: {stats["total_samples"]}')
            self.stdout.write(f'  Daycare invoices: {stats["positive_samples"]}')
            self.stdout.write(f'  Not invoices: {stats["negative_samples"]}')
            
            # Check if enough samples
            if stats['total_samples'] < min_samples and not force:
                raise CommandError(
                    f'\n❌ Insufficient training samples!\n'
                    f'Need at least {min_samples} samples, currently have {stats["total_samples"]}.\n\n'
                    f'To label training samples:\n'
                    f'1. Run the development server: python manage.py runserver\n'
                    f'2. Go to: http://localhost:8000/ai/emails/manual-select/\n'
                    f'3. Label at least {min_samples - stats["total_samples"]} more emails\n\n'
                    f'Or use --force to train anyway (not recommended for accuracy)'
                )
            
            # Check for class imbalance
            if stats['positive_samples'] == 0 or stats['negative_samples'] == 0:
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠️  Warning: Class imbalance detected!\n'
                        'You need examples of BOTH daycare invoices and non-invoices.\n'
                        'For best results, aim for balanced samples of each class.\n'
                    )
                )
                
                if not force:
                    raise CommandError('Training cancelled due to class imbalance. Use --force to override.')
            
            # Train the model
            self.stdout.write('\n🔄 Training model...\n')
            
            result = EmailClassificationService.train_from_samples(
                min_samples=1 if force else min_samples
            )
            
            # Display results
            metrics = result['metrics']
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Training successful!\n\n'
                    f'Model Details:\n'
                    f'  Version: {result["model_version"]}\n'
                    f'  Training samples: {result["samples_used"]}\n\n'
                    f'Performance Metrics:\n'
                    f'  Accuracy: {metrics.get("accuracy", 0):.1%}\n'
                    f'  Precision: {metrics.get("precision", 0):.1%}\n'
                    f'  Recall: {metrics.get("recall", 0):.1%}\n'
                    f'  F1 Score: {metrics.get("f1_score", 0):.1%}\n'
                )
            )
            
            # Recommendations based on accuracy
            accuracy = metrics.get('accuracy', 0)
            if accuracy < 0.7:
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠️  Model accuracy is below 70%. Recommendations:\n'
                        '  - Add more diverse training examples\n'
                        '  - Ensure samples represent different email types\n'
                        '  - Balance positive and negative samples\n'
                    )
                )
            elif accuracy >= 0.9:
                self.stdout.write(
                    self.style.SUCCESS(
                        '\n🎉 Excellent accuracy! Model is ready for production use.\n'
                    )
                )
            else:
                self.stdout.write(
                    '\n👍 Good accuracy. Model will improve with more feedback.\n'
                )
            
            # Next steps
            self.stdout.write(
                '\nNext Steps:\n'
                '1. Classify emails: python manage.py classify_emails --all\n'
                '2. Review predictions: http://localhost:8000/ai/emails/review/\n'
                '3. Provide feedback to improve accuracy\n'
                '4. Model will automatically retrain after 20 feedback samples\n'
            )
        
        except Exception as e:
            if isinstance(e, CommandError):
                raise
            raise CommandError(f'Training failed: {e}')
