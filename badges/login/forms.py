from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, Group, Achievement, ShopItem

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'custom-input',
            'placeholder': 'Логин'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'custom-input',
            'placeholder': 'Пароль'
        })
    )
class AvatarUploadForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control form-control-sm'}),
        }

class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'birth_date', 'balance', 'rating_points', 'group', 'artel', 'rank',
            'volunteering_points', 'contests_points', 'academic_points',
            'extracurricular_points', 'projects_points',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'rating_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'artel': forms.TextInput(attrs={'class': 'form-control'}),
            'volunteering_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'contests_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'academic_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'extracurricular_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'projects_points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['group'].queryset = Group.objects.filter(teacher=teacher_user)

    def clean(self):
        cleaned_data = super().clean()
        max_val = 100
        point_fields = ['volunteering_points', 'contests_points', 'academic_points', 'extracurricular_points', 'projects_points']
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
    student = forms.ModelChoiceField(queryset=UserProfile.objects.none(), label="Ученик", widget=forms.Select(attrs={'class': 'form-control'}))
    activity = forms.ChoiceField(choices=ACTIVITY_CHOICES, label="Категория", widget=forms.Select(attrs={'class': 'form-control'}))
    points = forms.IntegerField(min_value=1, max_value=100, label="Очки (1–100)", widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}))

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['student'].queryset = UserProfile.objects.filter(role='student', group__teacher=teacher_user).select_related('user', 'group')

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
    student = forms.ModelChoiceField(queryset=UserProfile.objects.none(), label="Ученик", widget=forms.Select(attrs={'class': 'form-control'}))
    achievement = forms.ModelChoiceField(queryset=Achievement.objects.none(), label="Достижение", widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        teacher_user = kwargs.pop('teacher_user', None)
        super().__init__(*args, **kwargs)
        if teacher_user:
            self.fields['student'].queryset = UserProfile.objects.filter(role='student', group__teacher=teacher_user).select_related('user', 'group')
            self.fields['achievement'].queryset = Achievement.objects.all()