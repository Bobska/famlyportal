from django import forms

from .models import Expense, Income, Payee


class TransactionFormBase(forms.ModelForm):
    """Base form that adds payee selection and shared validation."""

    payee_empty_label: str = 'Select a payee...'
    payee_required_message: str = 'Please select a payee.'

    payee_choice = forms.ModelChoiceField(
        queryset=Payee.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-select',
                'id': 'id_payee_choice',
            }
        ),
    )

    class Meta:
        fields = ['date', 'amount', 'notes']
        widgets = {
            'date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'amount': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '0.00',
                    'pattern': r'[\d,]+\.?\d{0,2}',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control form-control-sm',
                    'rows': 2,
                    'placeholder': 'Optional details...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        field = self.fields['payee_choice']
        field.empty_label = self.payee_empty_label
        if self.user:
            # Scope payees to the current user to avoid data leakage across families.
            field.queryset = Payee.objects.filter(user=self.user).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        payee = cleaned_data.get('payee_choice')
        if not payee:
            raise forms.ValidationError(self.payee_required_message)
        cleaned_data['payee'] = payee.name
        return cleaned_data

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be positive.')
        return amount


class IncomeForm(TransactionFormBase):
    """Form for creating and editing income entries."""

    payee_empty_label = 'Select existing payee...'
    payee_required_message = 'Please select a payee.'

    class Meta(TransactionFormBase.Meta):
        model = Income


class ExpenseForm(TransactionFormBase):
    """Form for creating and editing expense entries."""

    payee_empty_label = 'Select existing merchant...'
    payee_required_message = 'Please select a merchant.'

    class Meta(TransactionFormBase.Meta):
        model = Expense
