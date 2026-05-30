from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class SavedReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_reports")
    title = models.CharField(max_length=255)
    analysis_type = models.CharField(max_length=64)
    symbol = models.CharField(max_length=255, blank=True)
    duration_seconds = models.FloatField(default=0.0)
    agent_type = models.CharField(max_length=64, default="adk_agentic")
    markdown_report = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username}: {self.title}"
