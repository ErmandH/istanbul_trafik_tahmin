from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator

class TrafikForm(forms.Form):
    """Trafik tahmini için kullanıcı girişi formu"""
    tarih = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Tarih",
        help_text="Trafik tahmini yapılacak tarih",
        required=True
    )
    
    saat = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label="Saat",
        help_text="Trafik tahmini yapılacak saat",
        initial="08:00",
        required=True
    )
    
    konum = forms.CharField(
        widget=forms.HiddenInput(),
        label="Konum",
        required=False  # Haritadan seçilebileceği için zorunlu değil
    )
    
    mesafe = forms.FloatField(
        label="Seyahat Mesafesi (km)",
        min_value=0.1,
        max_value=50.0,
        initial=5.0,
        validators=[
            MinValueValidator(0.1, message="Mesafe en az 0.1 km olmalıdır."),
            MaxValueValidator(50.0, message="Mesafe en fazla 50 km olabilir.")
        ],
        help_text="Seyahat etmek istediğiniz tahmini mesafe (km)",
        widget=forms.NumberInput(attrs={'step': '0.1'}),
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        # Ek doğrulamalar burada yapılabilir
        return cleaned_data 