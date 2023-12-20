from django import forms
from .models import ChartTable, ReviewTable, PositionTable, TagTable

class ChartForm(forms.ModelForm):
  tags = forms.ModelMultipleChoiceField(
    queryset=TagTable.objects,
    widget=forms.CheckboxSelectMultiple,
    required=False
  )  
  class Meta:
    model = ChartTable
    # fields = ("user", 'name', 'pair', 'rule',"standard_datetime", "minus_delta", "plus_delta", "memo")
    fields = ('name', 'pair', 'rule',"standard_datetime", "minus_delta", "plus_delta", "memo","tags")
    widgets = {
      'memo': forms.Textarea(
        attrs={
          'style': 'width: 100%; height: auto;'
        }
      ),
      'standard_datetime': forms.DateTimeInput(attrs={"type": "datetime-local"})
    }

class ReviewForm(forms.ModelForm):
  class Meta:
    model = ReviewTable
    fields = ("name", "rule", "pair", "dt", "delta", "memo")
    widgets = {
      'name': forms.Textarea(attrs={'rows': 1, 'cols': 50}),
      'memo': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
      'dt': forms.DateTimeInput(attrs={"type": "datetime-local"})
    }

class ReviewUpdateForm(forms.ModelForm):
  class Meta:
    model = ReviewTable
    fields = ("name", "rule", "pair", "delta", "memo")
    widgets = {
      'name': forms.Textarea(attrs={'rows': 1, 'cols': 50}),
      'memo': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
      "delta": forms.NumberInput(attrs={"style":"width:60px"})
    }

class PositionSpeedForm(forms.ModelForm):
  class Meta:
    model = PositionTable
    fields = ("quantity", "limit", "stop", "pair", "position_datetime")
    widgets = {
      'pair': forms.HiddenInput(),
      'position_datetime': forms.HiddenInput(),
      "limit": forms.NumberInput(attrs={"step":"0.001"}),
      "stop": forms.NumberInput(attrs={"step":"0.001"})
    }
    
class PositionMarketForm(forms.ModelForm):
  class Meta:
    model = PositionTable
    fields = ("condition", "limit", "stop","profit", "settlement_datetime", "settlement_rate")
  def __init__(self, *args, **kwargs):
    super(PositionMarketForm, self).__init__(*args, **kwargs)
    self.fields['limit'].initial = None
    self.fields['stop'].initial = None
    self.fields['condition'].initial = "market"
    for field_name in self.fields:
      self.fields[field_name].widget = forms.HiddenInput()

class PositionUpdateForm(forms.ModelForm):
  now_datetime = forms.DateTimeField(widget=forms.HiddenInput())
  now_rate = forms.FloatField(widget=forms.HiddenInput())
  class Meta:
    model = PositionTable
    fields = ("limit", "stop")
    widgets = {
      "limit": forms.NumberInput(attrs={"style":"width:100px", "step":"0.001"}),
      "stop": forms.NumberInput(attrs={"style":"width:100px", "step":"0.001"})
    }

class TagForm(forms.Form):
  class Meta:
    model = TagTable
    fields = ("name","memo","color")
    





