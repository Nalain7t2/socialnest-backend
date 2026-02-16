from django.db import models
from django.contrib.auth.models import User
from .validators import validate_profile_image

# Create your models here.

class Post(models.Model):
    user = models.ForeignKey(
        User,
        on_delete= models.CASCADE,
        related_name="posts"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(
        upload_to="posts/",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Like(models.Model):    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ('user', 'post')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to="profiles/", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, null=True)  # Add this
    location = models.CharField(max_length=100, blank=True, null=True)  # Add this
    website = models.URLField(blank=True, null=True)  # Add this
    followers = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='following',
        blank=True
    )
    
    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        # Delete old avatar when new one is uploaded
        try:
            old = Profile.objects.get(pk=self.pk)
            if old.avatar and old.avatar != self.avatar:
                old.avatar.delete(save=False)
        except Profile.DoesNotExist:
            pass
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Delete avatar file when profile is deleted
        if self.avatar:
            self.avatar.delete(save=False)
        super().delete(*args, **kwargs)   

    def followers_count(self):
        return self.followers.count();

    def following_count(self):
        return self.following.count();    
    
    def follow(self, profile):
        # follow another user
        if profile != self and not self.followers.filter(id=profile.id).exists():
            self.followers.add(profile)
            return True
        return False
    
    def unfollow(self, profile):
        # unfollow another user 
        if self.followers.filter(id=profile.id).exists():
            self.followers.remove(profile)
            return True
        return False
    
    def is_following(self, profile):

        # check if following a user 
        return self.followers.filter(id=profile.id).exists()
            
