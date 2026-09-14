from django import forms


class BusinessCardForm(forms.Form):
    LANGUAGE_CHOICES = [
        ('thai', 'Thai'),
        ('english', 'English'),
    ]
    ORIENTATION_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ]
    PHOTO_CHOICES = [
        ('with_photo', 'With photo'),
        ('without_photo', 'Without photo'),
    ]

    primary_language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        label='Primary language',
    )
    name_th = forms.CharField(label='Name (Thai)', required=False)
    name_en = forms.CharField(label='Name (English)', required=False)
    role_th = forms.CharField(label='Role (Thai)', required=False)
    role_en = forms.CharField(label='Role (English)', required=False)
    photo = forms.FileField(label='Photo', required=False)
    company_th = forms.CharField(label='Company name (Thai)', required=False)
    company_en = forms.CharField(label='Company name (English)', required=False)
    address = forms.CharField(
        label='Contact address',
        required=False,
        widget=forms.Textarea,
    )
    phone = forms.CharField(label='Phone number', required=False)
    email = forms.EmailField(label='Email address', required=False)
    social_links = forms.CharField(
        label='Social links',
        required=False,
        widget=forms.Textarea,
    )
    qr_destination_url = forms.URLField(label='QR destination URL')
    orientation = forms.ChoiceField(
        choices=ORIENTATION_CHOICES,
        label='Card orientation',
    )
    photo_choice = forms.ChoiceField(
        choices=PHOTO_CHOICES,
        label='Photo choice',
    )

    def clean(self):
        cleaned_data = super().clean()
        primary_language = cleaned_data.get('primary_language')

        primary_name_field = {
            'thai': 'name_th',
            'english': 'name_en',
        }.get(primary_language)

        if primary_name_field and not cleaned_data.get(primary_name_field):
            self.add_error(
                primary_name_field,
                'Enter the name in the primary language.',
            )

        if not cleaned_data.get('phone') and not cleaned_data.get('email'):
            raise forms.ValidationError(
                'Provide at least one of a phone number or an email address.'
            )

        return cleaned_data
