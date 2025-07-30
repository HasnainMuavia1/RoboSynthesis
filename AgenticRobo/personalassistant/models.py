from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class SubjectContext(models.Model):
    """Model to store subject-specific context data uploaded by users"""
    SUBJECT_CHOICES = [
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('programming', 'Programming'),
        ('language', 'Language Arts'),
        ('history', 'History'),
        ('custom', 'Custom Subject')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subject_contexts')
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    context_text = models.TextField(blank=True, null=True)
    context_file = models.FileField(upload_to='subject_contexts/', blank=True, null=True)
    file_type = models.CharField(max_length=10, blank=True, null=True)  # pdf, docx, txt
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'subject']
        verbose_name_plural = 'Subject Contexts'
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_subject_display()} Context"
