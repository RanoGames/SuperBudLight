from django import forms
from .models import Achievement
from profile_app.models import UserProfile


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['name', 'description', 'requirements', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'icon': forms.FileInput(attrs={'class': 'form-control', 'accept': '.png'}),
        }

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon and not icon.name.lower().endswith('.png'):
            raise forms.ValidationError("Разрешены только файлы формата PNG.")
        return icon


class AssignAchievementForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=UserProfile.objects.none(), label="Ученик",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    achievement = forms.ModelChoiceField(
        queryset=Achievement.objects.none(), label="Достижение",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['student'].queryset = UserProfile.objects.filter(
                roles__name='student', group__teacher=teacher_user
            ).select_related('user', 'group').distinct()
            self.fields['achievement'].queryset = Achievement.objects.all()
