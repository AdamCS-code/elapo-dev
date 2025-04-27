from django.test import TestCase

# Create your tests here.
# HAPPY PATH 
# authenticated user : login_wallet (request) when (user is authenticated)
# authenticated user : register_wallet(request) when (user is authenticated)
# authenticated user and wallet : topup_wallet(request) when amount is positive and using app's form
# authenticated user and wallet : pay_order(request, id(order_id)) when order is exist, not paid and own by this user.


# UNHAPPY PATH
# unauthenticated user : login_wallet(request)
# authenticated user : login_wallet(request) when (login other wallet)
# authenticate user : register_wallet when (wallet already exist)
# unauthenticated user : register_wallet (request)
# authenticated user and wallet : pay_order(request, id(order_id)) when order is not exist 
# authenticated user and wallet : pay_order(request, id(order_id)) when other then unpaid
# authenticated user and wallet : pay_order(request, id(order_id)) not own by this user
# OWASP PATH
