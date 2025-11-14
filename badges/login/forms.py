# login/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Group

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )


class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'birth_date',
            'balance',
            'rating_points',
            'group',
            'artel',
            # 'rank',  # ← закомментируй, если звание только автоматическое
            'volunteering_points',
            'contests_points',
            'academic_points',
            'extracurricular_points',
            'projects_points',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'artel': forms.TextInput(attrs={'class': 'form-control'}),
            # 'rank': forms.TextInput(attrs={'class': 'form-control'}),

            # Поля очков — от 0 до 100
            'volunteering_points': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
            'contests_points': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
            'academic_points': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
            'extracurricular_points': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
            'projects_points': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100}
            ),
        }

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['group'].queryset = Group.objects.filter(teacher=teacher_user)

    def clean(self):
        cleaned_data = super().clean()
        max_val = 100
        point_fields = [
            'volunteering_points',
            'contests_points',
            'academic_points',
            'extracurricular_points',
            'projects_points'
        ]
        for field in point_fields:
            val = cleaned_data.get(field)
            if val is not None and (val < 0 or val > max_val):
                self.add_error(field, f"Значение должно быть от 0 до {max_val}.")
        return cleaned_data


class AwardPointsForm(forms.Form):
    ACTIVITY_CHOICES = [
        ('volunteering', 'Волонтёрство'),
        ('contests', 'Участие в конкурсах'),
        ('academic', 'Учебная активность'),
        ('extracurricular', 'Внеучебная активность'),
        ('projects', 'Проектная деятельность'),
    ]

    student = forms.ModelChoiceField(
        queryset=UserProfile.objects.none(),
        label="Ученик",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    activity = forms.ChoiceField(
        choices=ACTIVITY_CHOICES,
        label="Категория",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    points = forms.IntegerField(
        min_value=1,
        max_value=100,
        label="Очки (1–100)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100})
    )

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['student'].queryset = UserProfile.objects.filter(
                role='student',
                group__teacher=teacher_user
            ).select_related('user', 'group')