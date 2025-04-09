from django import forms
from .models import WalletAccount, Wallet

class WalletAccountForm(forms.ModelForm):
    raw_pin = forms.CharField(
        max_length=6, 
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='PIN'
    )

    class Meta:
        model = WalletAccount
        fields = ['raw_pin']

    def save(self, commit=True):
        wallet_account = super().save(commit=False)
        raw_pin = self.cleaned_data['raw_pin']
        wallet_account.set_pin(raw_pin)
        if commit:
            wallet_account.save()
        return wallet_account


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['saldo']
        widgets = {
            'saldo': forms.NumberInput(attrs={'readonly': 'readonly'})  # make it read-only in form
        }

class LoginWalletForm(forms.Form):
    pin = forms.CharField(
        max_length=6,
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='Wallet PIN'
    )

    def __init__(self, *args, **kwargs):
        self.wallet_account = kwargs.pop('wallet_account', None)
        print(self.wallet_account)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')

        if self.wallet_account is None:
            raise forms.ValidationError("Wallet account not found.")

        if not self.wallet_account.check_pin(pin):
            raise forms.ValidationError("Invalid PIN.")

        return cleaned_data

class TopUpForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=1,
        label='Top-up Amount'
    )
