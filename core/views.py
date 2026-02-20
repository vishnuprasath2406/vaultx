from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count
from django.contrib.auth.decorators import login_required

import json
import random
from .models import User, Customer, Product, Claim, ClaimHistory, ServiceMessage
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # SELLER / SERVICE LOGIN
        if role in ["seller", "service"]:
            try:
                user = User.objects.get(username=username, password=password, role=role)

                request.session["user_id"] = user.id
                request.session["role"] = user.role
                request.session["username"] = user.username

                return redirect(user.role)

            except User.DoesNotExist:
                return render(request, "login.html", {"error": "Invalid credentials"})

        # CUSTOMER LOGIN WITH OTP
        elif role == "customer":
            try:
                customer = Customer.objects.get(customer_id=username, password=password)

                otp = str(random.randint(100000, 999999))

                request.session["otp"] = otp
                request.session["otp_customer_id"] = customer.customer_id

                send_mail(
                    subject="VaultX Login OTP",
                    message=f"Your OTP is: {otp}",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[customer.email],
                    fail_silently=False
                )

                return redirect("verify_otp")

            except Customer.DoesNotExist:
                return render(request, "login.html", {"error": "Invalid Customer ID or Password"})

    return render(request, "login.html")
def verify_otp(request):

    if request.method == "POST":
        entered = request.POST.get("otp")
        session_otp = request.session.get("otp")

        print("ENTERED:", entered)
        print("SESSION OTP:", session_otp)
        print("SESSION DATA:", dict(request.session))

        if not session_otp:
            return redirect("login")

        if str(entered) == str(session_otp):

            customer_id = request.session.get("otp_customer_id")
            customer = Customer.objects.get(customer_id=customer_id)

            request.session["customer_id"] = customer.customer_id
            request.session["role"] = "customer"
            request.session["username"] = customer.name

            del request.session["otp"]
            del request.session["otp_customer_id"]

            return redirect("customer")

        return render(request, "verify_otp.html", {"error": "Invalid OTP"})

    return render(request, "verify_otp.html")


from .models import ServiceMessage, ClaimHistory

def customer(request):

    if request.session.get("role") != "customer":
        return redirect("login")

    customer = Customer.objects.get(
        customer_id=request.session.get("customer_id")
    )

    products = Product.objects.filter(customer=customer)

    claims = Claim.objects.filter(
        product__customer=customer
    ).order_by("-created_at")

    # 🔥 Service messages linked to this customer
    messages = ServiceMessage.objects.filter(
        claim__product__customer=customer
    ).order_by("-created_at")

    # 🔥 Claim timeline history
    histories = ClaimHistory.objects.filter(
        claim__product__customer=customer
    ).order_by("-created_at")

    return render(request, "customer.html", {
        "customer": customer,
        "products": products,
        "claims": claims,
        "messages": messages,
        "histories": histories,
        "today": timezone.now().date()
    })

def seller(request):
    if request.session.get("role") != "seller":
        return redirect("login")

    products = Product.objects.all()

    return render(request, "seller.html", {
        "username": request.session.get("username"),
        "products": products
    })
def service(request):
    if request.session.get("role") != "service":
        return redirect("login")

    # Approved claims only
    approved_claims = Claim.objects.filter(status="approved")

    # Pending claims → customer requests
    pending_claims = Claim.objects.filter(status="pending")

    return render(request, "service.html", {
        "approved_claims": approved_claims,
        "pending_claims": pending_claims,
        "username": request.session.get("username")
    })
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils import timezone

@csrf_exempt
def service_update_claim(request):

    if request.method == "POST":
        data = json.loads(request.body)

        claim_id = data.get("claim_id")
        status = data.get("status")

        try:
            claim = Claim.objects.get(id=claim_id)

            claim.status = status

            # Auto progress logic
            if status == "in_repair":
                claim.repair_progress = 75
            elif status == "completed":
                claim.repair_progress = 100
            elif status == "approved":
                claim.repair_progress = 50

            claim.save()

            # Save history
            ClaimHistory.objects.create(
                claim=claim,
                status=status,
                updated_at=timezone.now()
            )

            # 🔥 SEND EMAIL
            send_mail(
                subject="Warranty Claim Status Updated",
                message=f"""
Hello {claim.product.customer.name},

Your claim for product "{claim.product.product_name}"
has been updated to: {status.upper()}.

Thank you,
VaultX Service Team
""",
                from_email="pavithrannageswari.123@gmail.com",
                recipient_list=[claim.product.customer.email],
                fail_silently=False,
            )

            return JsonResponse({"success": True})

        except Claim.DoesNotExist:
            return JsonResponse({"success": False})

    return JsonResponse({"success": False})



def raise_claim(request):
    if request.method == "POST":
        product = Product.objects.get(id=request.POST.get("product_id"))

        Claim.objects.create(
            product=product,
            description=request.POST.get("description"),
            attachment=request.FILES.get("attachment"),
            status="pending"
        )

    return redirect("customer")
@csrf_exempt
def add_product(request):
    if request.method == "POST":
        data = json.loads(request.body)

        customer, created = Customer.objects.get_or_create(
            customer_id=data["customer_id"],
            defaults={
                "name": data["name"],
                "password": data["password"],
                "email": data["email"],
                "address": data["address"],
                "mobile": data["mobile"],
            }
        )

        Product.objects.create(
            customer=customer,
            product_name=data["product_name"],
            serial_number=data["serial_number"],
            warranty_start=data["warranty_start"],
            warranty_end=data["warranty_end"]
        )

        return JsonResponse({"message": "Saved"})

    return JsonResponse({"error": "Invalid"})
def dashboard_stats(request):
    return JsonResponse({
        "customers": Customer.objects.count(),
        "products": Product.objects.count()
    })



import json
import requests
from django.http import JsonResponse
from django.conf import settings

import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def chatbot_api(request):

    if request.method != "POST":
        return JsonResponse({"reply": "POST only"})

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")

        if not user_message:
            return JsonResponse({"reply": "Empty message"})

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "You are VaultX warranty assistant."},
                {"role": "user", "content": user_message}
            ]
        }

        r = requests.post(url, headers=headers, json=payload)
        result = r.json()

        reply = result["choices"][0]["message"]["content"]

        return JsonResponse({"reply": reply})

    except Exception as e:
        print("ERROR:", e)
        return JsonResponse({"reply": "Backend error"})


def logout_view(request):
    request.session.flush()
    return redirect("login")
def service_send_message(request, claim_id):
    if request.session.get("role") != "service":
        return redirect("login")

    if request.method == "POST":
        claim = Claim.objects.get(id=claim_id)
        msg = request.POST.get("message")

        ServiceMessage.objects.create(
            claim=claim,
            sender_role="service",
            message=msg
        )

    return redirect("service")
def search_customer(request, cid):
    try:
        customer = Customer.objects.get(customer_id=cid)
        products = Product.objects.filter(customer=customer)

        return JsonResponse({
            "name": customer.name,
            "email": customer.email,
            "mobile": customer.mobile,
            "products": [
                {
                    "product_name": p.product_name,
                    "serial_number": p.serial_number
                } for p in products
            ]
        })
    except:
        return JsonResponse({"error": "Not Found"})
from django.http import JsonResponse
from .models import Claim

@csrf_exempt
def service_update_claim(request):

    if request.method == "POST":
        data = json.loads(request.body)

        claim_id = data.get("claim_id")
        status = data.get("status")

        try:
            claim = Claim.objects.select_related("product__customer").get(id=claim_id)

            claim.status = status

            # Auto progress logic
            if status == "in_repair":
                claim.repair_progress = 75
            elif status == "completed":
                claim.repair_progress = 100
            elif status == "approved":
                claim.repair_progress = 50
            elif status == "rejected":
                claim.repair_progress = 0

            claim.save()

            # Save history
            ClaimHistory.objects.create(
                claim=claim,
                status=status,
                updated_at=timezone.now()
            )

            # 🔥 EMAIL NOTIFICATION
            send_mail(
                subject="VaultX Claim Status Updated",
                message=f"""
Hello {claim.product.customer.name},

Your claim for "{claim.product.product_name}"
has been updated to: {status.upper()}.

Thank you,
VaultX Service Team
""",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[claim.product.customer.email],
                fail_silently=False,
            )

            return JsonResponse({"success": True})

        except Claim.DoesNotExist:
            return JsonResponse({"success": False})

    return JsonResponse({"success": False})


    return JsonResponse({"claims": data})
from django.views.decorators.csrf import csrf_exempt
import json

from django.core.mail import send_mail
from django.http import JsonResponse
import json


def search_customer_api(request):
    customer_id = request.GET.get("customer_id")

    try:
        customer = Customer.objects.get(customer_id=customer_id)

        products = Product.objects.filter(customer=customer)

        product_list = []
        for p in products:
            product_list.append({
                "product_name": p.product_name,
                "serial": p.serial_number
            })

        return JsonResponse({
            "found": True,
            "name": customer.name,
            "email": customer.email,
            "mobile": customer.mobile,
            "address": customer.address,
            "products": product_list
        })

    except Customer.DoesNotExist:
        return JsonResponse({"found": False})
def customer_claims_api(request):
    customer_id = request.session.get("customer_id")

    claims = Claim.objects.filter(
        product__customer_id=customer_id
    ).order_by("-id")

    data = []

    for claim in claims:
        data.append({
            "product": claim.product.product_name,
            "description": claim.description,
            "status": claim.status,
            "attachment": claim.attachment.url if claim.attachment else None
        })

    return JsonResponse({"claims": data})
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Customer, Product, Claim

def customer_dashboard_api(request):
    customer = Customer.objects.get(user=request.user)

    products = Product.objects.filter(customer=customer)
    claims = Claim.objects.filter(customer=customer)

    return JsonResponse({
        "customer": {
            "name": customer.name,
            "email": customer.email,
            "mobile": customer.mobile,
        },
        "products": [
            {
                "id": p.id,
                "product_name": p.product_name,
                "serial": p.serial_number,
                "start": str(p.warranty_start),
                "end": str(p.warranty_end),
            } for p in products
        ],
        "claims": [
            {
                "product": c.product.product_name,
                "description": c.description,
                "status": c.status
            } for c in claims
        ]
    })


@csrf_exempt
def raise_claim_api(request):
    data = json.loads(request.body)
    customer = Customer.objects.get(user=request.user)
    product = Product.objects.get(id=data["product_id"])

    Claim.objects.create(
        customer=customer,
        product=product,
        description=data["description"],
        status="pending"
    )

    return JsonResponse({"success": True})
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Customer, Product, Claim

def customer_dashboard_api(request):
    customer = Customer.objects.get(user=request.user)

    products = Product.objects.filter(customer=customer)
    claims = Claim.objects.filter(customer=customer)

    return JsonResponse({
        "customer": {
            "name": customer.name,
            "email": customer.email,
            "mobile": customer.mobile,
        },
        "products": [
            {
                "id": p.id,
                "product_name": p.product_name,
                "serial": p.serial_number,
                "start": str(p.warranty_start),
                "end": str(p.warranty_end),
            } for p in products
        ],
        "claims": [
            {
                "product": c.product.product_name,
                "description": c.description,
                "status": c.status
            } for c in claims
        ]
    })


@csrf_exempt
def raise_claim_api(request):
    data = json.loads(request.body)
    customer = Customer.objects.get(user=request.user)
    product = Product.objects.get(id=data["product_id"])

    Claim.objects.create(
        customer=customer,
        product=product,
        description=data["description"],
        status="pending"
    )

    return JsonResponse({"success": True})
from django.shortcuts import render
from datetime import date

from django.http import JsonResponse
from .models import Claim

def service_claims_data(request):
    claims = Claim.objects.select_related("product__customer").all().order_by("-id")

    data = []

    for claim in claims:
        data.append({
            "id": claim.id,
            "customer": claim.product.customer.name,
            "customer_id": claim.product.customer.customer_id,
            "product": claim.product.product_name,
            "serial": claim.product.serial_number,
            "status": claim.status,
        })

    return JsonResponse({"claims": data})
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count

def service_dashboard_api(request):

    today = timezone.now().date()

    pending = Claim.objects.filter(status="pending").count()
    approved = Claim.objects.filter(status="approved").count()
    repair = Claim.objects.filter(status="in_repair").count()
    completed_today = Claim.objects.filter(status="completed", updated_at__date=today).count()

    total_this_month = Claim.objects.filter(
        created_at__month=today.month,
        created_at__year=today.year
    ).count()

    expiring = Product.objects.filter(
        warranty_end__lte=today + timedelta(days=7),
        warranty_end__gte=today
    ).count()

    return JsonResponse({
        "pending": pending,
        "approved": approved,
        "repair": repair,
        "completed_today": completed_today,
        "monthly_total": total_this_month,
        "expiring": expiring
    })

