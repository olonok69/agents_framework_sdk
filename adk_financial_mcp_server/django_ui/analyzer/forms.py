import json
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


ENDPOINT_CHOICES = [
    ("technical", "Technical Analysis"),
    ("scanner", "Market Scanner"),
    ("fundamental", "Fundamental Analysis"),
    ("multisector", "Multi-Sector Analysis"),
    ("combined", "Combined Analysis"),
    ("earnings_momentum", "Earnings Momentum"),
    ("trin", "TRIN Breadth"),
    ("overnight_gaps", "Overnight Gaps"),
]


DEFAULT_PAYLOADS = {
    "technical": {"symbol": "AAPL", "period": "1y"},
    "scanner": {"symbols": "AAPL,MSFT,GOOGL,AMZN", "period": "1y"},
    "fundamental": {"symbol": "MSFT", "period": "3y"},
    "multisector": {
        "period": "1y",
        "sectors": [
            {"name": "Banking", "symbols": "JPM,BAC,WFC"},
            {"name": "Technology", "symbols": "AAPL,MSFT,GOOGL"},
        ],
    },
    "combined": {"symbol": "TSLA", "technical_period": "1y", "fundamental_period": "3y"},
    "earnings_momentum": {
        "symbols": "AAPL,MSFT,GOOGL,AMZN,NVDA",
        "period": "6mo",
        "volume_window": 20,
        "volume_multiplier": 2.0,
        "hold_days": 5,
        "max_positions": 3,
    },
    "trin": {"period": "6mo", "window": 20, "band_k": 1.5, "use_log": True},
    "overnight_gaps": {"symbol": "AAPL", "lookback_days": 120, "min_gap_pct": 1.0},
}


class AnalysisForm(forms.Form):
    api_url = forms.CharField(initial="http://localhost:8000", required=True)
    endpoint = forms.ChoiceField(choices=ENDPOINT_CHOICES, required=True)
    payload = forms.CharField(widget=forms.Textarea(attrs={"rows": 12}), required=True)

    def clean_payload(self):
        payload = self.cleaned_data["payload"]
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON payload: {exc}")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
