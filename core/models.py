
from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('service', 'Service Center'),
    ]
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)



class Customer(models.Model):
    customer_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    mobile = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Product(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=200)
    warranty_start = models.DateField()
    warranty_end = models.DateField()
   
    def __str__(self):
        return self.product_name
from django.db import models


class Claim(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, default="pending")
    attachment = models.FileField(upload_to="claims/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
     return f"Claim {self.id}"
     
    
 

class ClaimHistory(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.claim.id} - {self.status}"
class Notification(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
class ServiceMessage(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE)
    sender_role = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

