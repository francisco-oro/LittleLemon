from django.db import models
from django.contrib.auth.models import User

# This model only requires a slug and a title
class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=False)
    def __str__(self) -> str:
        return self.title

# Featured indicates if this Item is marked as featured 
class MenuItem(models.Model):
    title = models.CharField(max_length=255,db_index=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=False)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    def __str__(self) -> str:
        return self.title

# A cart model is a temporary storage for users who can add menu items before placing an order
# A user can only have one cart at a time
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    def __str__(self) -> str:
        return self.user.username

    # There can be only one menu entry for a specific user. You can only change the quantity of that menu item 
    class Meta:
        unique_together = ('menuitem', 'user')

# As soon as the order is placed the items will be moved from the cart to the current order
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # As both user and delivery crew are referencing the user_id in the user table
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='delivery_crew', null=True)
    # Mark if the order is delivered or not.
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(db_index=True)
    def __str__(self) -> str:
        return self.user.username

# All the items from the cart will be moved here with the link to the newly created, then those cart items will be deleted. 
class OrderItem(models.Model):
    order = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=6, decimal_places=2)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    def __str__(self) -> str:
        return self.order.username
    # One order can have only one entry for a specific menu item
    class Meta: 
        unique_together = ('order', 'menuitem')


