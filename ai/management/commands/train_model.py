"""
Management Command: Train Model
================================

Train or retrain an ML model using a specified dataset.

Usage:
    python manage.py train_model <model_name> --dataset <dataset_id> --version <version>
"""
from django.core.management.base import BaseCommand, CommandError
from ai.models import TrainingDataset, MLModel
from ai.services import TrainingService


class Command(BaseCommand):
    help = 'Train or retrain an ML model with specified dataset'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'model_name',
            type=str,
            help='Name of the model to train (e.g., email_daycare_classifier)'
        )
        parser.add_argument(
            '--dataset',
            type=int,
            help='Dataset ID to use for training. If not specified, uses all available data for this model.'
        )
        parser.add_argument(
            '--version',
            type=str,
            default='1.0.0',
            help='Version number for the new model (default: 1.0.0)'
        )
        parser.add_argument(
            '--description',
            type=str,
            default='',
            help='Model description'
        )
        parser.add_argument(
            '--activate',
            action='store_true',
            help='Automatically activate this model version after training'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if retraining is needed (don\'t actually train)'
        )
    
    def handle(self, *args, **options):
        model_name = options['model_name']
        dataset_id = options.get('dataset')
        version = options['version']
        description = options['description']
        activate = options['activate']
        check_only = options['check_only']
        
        self.stdout.write(self.style.SUCCESS(f'\n=== AI Hub: Model Training ==='))
        self.stdout.write(f'Model: {model_name}')
        
        # Check if retraining is needed
        if check_only:
            should_retrain, new_samples, reason = TrainingService.should_retrain(model_name)
            self.stdout.write(f'\nRetrain needed: {should_retrain}')
            self.stdout.write(f'New samples: {new_samples}')
            self.stdout.write(f'Reason: {reason}')
            return
        
        # Get training data
        try:
            data_list, labels_list = TrainingService.get_training_data(
                dataset_id=dataset_id,
                model_name=model_name,
                include_features=False
            )
        except Exception as e:
            raise CommandError(f'Failed to load training data: {e}')
        
        if len(data_list) < 10:
            raise CommandError(
                f'Not enough training samples ({len(data_list)}). Need at least 10 samples.'
            )
        
        self.stdout.write(f'Training samples: {len(data_list)}')
        self.stdout.write(f'Unique labels: {len(set(labels_list))}')
        self.stdout.write(f'Label distribution:')
        from collections import Counter
        for label, count in Counter(labels_list).items():
            self.stdout.write(f'  - {label}: {count}')
        
        # TODO: Initialize classifier and train
        # This is where you would:
        # 1. Import the specific classifier for this model_name
        # 2. Initialize it
        # 3. Call classifier.train(data_list, labels_list)
        # 4. Call classifier.save_model(version, description)
        
        self.stdout.write(self.style.WARNING(
            '\nNote: Actual model training not yet implemented.'
        ))
        self.stdout.write(
            'You need to create a classifier class that extends BaseClassifier '
            'and implements the extract_features() method.'
        )
        
        # Show what would be done
        result = TrainingService.trigger_training(
            model_name=model_name,
            dataset_id=dataset_id,
            version=version,
            description=description
        )
        
        self.stdout.write(f'\nTraining configuration:')
        for key, value in result.items():
            self.stdout.write(f'  {key}: {value}')
        
        if activate:
            self.stdout.write(self.style.SUCCESS(
                '\nModel would be activated after training (--activate flag set)'
            ))
        
        self.stdout.write(self.style.SUCCESS('\n=== Training preparation complete ===\n'))
