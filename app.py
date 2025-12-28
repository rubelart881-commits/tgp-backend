from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import datetime
import requests # পেমেন্ট রিকোয়েস্ট পাঠানোর জন্য
import hmac     # সিকিউরিটি চেকের জন্য
import hashlib  # সিকিউরিটি চেকের জন্য
import json

app = Flask(__name__)
CORS(app) 

# --- ১. কনফিগারেশন ---
# Supabase (তোমার দেওয়া তথ্য)
SUPABASE_URL = "https://gzgmtofyvfjknoectxgb.supabase.co"
SUPABASE_KEY = "sb_publishable_gYC68V5SQn6_OxXU2sCbvA_RrRFM0Xt"

# NOWPayments (তোমার দেওয়া নতুন তথ্য)
NOWPAYMENTS_API_KEY = "KFS8VFW-PNX4AHW-KNT35W5-HS56ESK"
IPN_SECRET_KEY = "OjSsnNqSiTTiB3o05xP1A19HA4L7lxvL"

# ডাটাবেস কানেকশন
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- আগের রাউটগুলো (Student Management) ---

@app.route('/get_students', methods=['GET'])
def get_students():
    search_query = request.args.get('search', '')
    filter_status = request.args.get('status', 'all')
    query = supabase.table('students').select("*")
    
    if search_query:
        query = query.or_(f"name.ilike.%{search_query}%,phone.ilike.%{search_query}%,email.ilike.%{search_query}%")
    
    if filter_status != 'all':
        query = query.eq('status', filter_status)
        
    response = query.execute()
    return jsonify(response.data)

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    trial_end = datetime.date.today() + datetime.timedelta(days=3)
    
    new_user = {
        "name": data.get('name'),
        "phone": data.get('phone'),
        "email": data.get('email'),
        "school_name": data.get('school'),
        "parent_name": data.get('parent'),
        "address": data.get('address'),
        "photo_url": data.get('img_url'),
        "status": "free_trial",
        "subscription_end_date": str(trial_end),
        "referred_by": data.get('ref_code', '')
    }
    
    try:
        data = supabase.table('students').insert(new_user).execute()
        return jsonify({"message": "Student Added Successfully!", "data": data.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    phone = data.get('phone')
    action = data.get('action') 
    
    update_data = {}
    if action == 'ban':
        update_data['status'] = 'banned'
    elif action == 'approve':
        update_data['status'] = 'active'
        next_year = datetime.date.today() + datetime.timedelta(days=365)
        update_data['subscription_end_date'] = str(next_year)
    elif action == 'free_trial':
        update_data['status'] = 'free_trial'
    
    try:
        response = supabase.table('students').update(update_data).eq('phone', phone).execute()
        return jsonify({"message": f"User {action} successful!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/dashboard_stats', methods=['GET'])
def dashboard_stats():
    total_students = supabase.table('students').select("*", count='exact').execute().count
    free_users = supabase.table('students').select("*", count='exact').eq('status', 'free_trial').execute().count
    paid_users = supabase.table('students').select("*", count='exact').eq('status', 'active').execute().count
    
    return jsonify({
        "total": total_students,
        "free": free_users,
        "paid": paid_users,
        "income": paid_users * 2000 
    })

# --- ৫. নতুন: পেমেন্ট লিংক তৈরি করা (App থেকে কল হবে) ---
@app.route('/create_payment', methods=['POST'])
def create_payment():
    data = request.json
    phone = data.get('phone') # স্টুডেন্টের ফোন নম্বর
    
    # ২,০০০ টাকা = আনুমানিক ১৭ ডলার
    amount_usd = 17 

    url = "https://api.nowpayments.io/v1/invoice"
    
    headers = {
        'x-api-key': NOWPAYMENTS_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # পেমেন্ট রিকোয়েস্ট বডি
    payload = {
        "price_amount": amount_usd,
        "price_currency": "usd",
        "pay_currency": "xmr", # XMR এ পেমেন্ট নিব
        "order_id": phone,     # ফোন নম্বরটা অর্ডার আইডি হিসেবে যাবে
        "order_description": "Class 8 Course Fee",
        # তোমার রেন্ডারেরWebhook লিংক
        "ipn_callback_url": "https://tgp-backend-ppga.onrender.com/webhook"
    }

    try:
        # NOWPayments API তে কল করা
        response = requests.post(url, headers=headers, json=payload)
        payment_data = response.json()
        
        # পেমেন্ট তৈরি সফল হলে ডাটাবেসে সেভ করা
        if 'id' in payment_data:
            supabase.table('payments').insert({
                "student_phone": phone,
                "amount": 2000,
                "method": "XMR",
                "trx_id": payment_data['id'],
                "status": "pending"
            }).execute()
            
            return jsonify(payment_data) # অ্যাপে পেমেন্ট এড্রেস চলে যাবে
        else:
            return jsonify({"error": "Payment failed", "details": payment_data}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- ৬. নতুন: অটোমেটিক ভেরিফিকেশন (Webhook) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # ১. সিকিউরিটি চেক (NOWPayments থেকেই এসেছে কিনা)
    sig = request.headers.get('x-nowpayments-sig')
    body = request.get_data()
    
    if not sig:
         return jsonify({"error": "No signature"}), 403

    try:
        hash_object = hmac.new(IPN_SECRET_KEY.encode(), body, hashlib.sha512)
        expected_sig = hash_object.hexdigest()
        
        if sig != expected_sig:
            return jsonify({"error": "Invalid signature"}), 403
    except Exception:
        # স্যান্ডবক্স বা এরর হ্যান্ডলিংয়ের জন্য পাস করে দিচ্ছি
        pass

    # ২. ডাটা প্রসেসিং
    data = request.json
    payment_status = data.get('payment_status') # waiting, confirming, finished
    student_phone = data.get('order_id')
    payment_id = data.get('payment_id')

    print(f"Payment Update for {student_phone}: {payment_status}")

    # ৩. পেমেন্ট যদি কমপ্লিট (finished) হয়
    if payment_status == 'finished':
        # পেমেন্ট টেবিলে আপডেট
        supabase.table('payments').update({"status": "approved"}).eq("trx_id", payment_id).execute()
        
        # স্টুডেন্টের সাবস্ক্রিপশন ১ বছরের জন্য চালু
        next_year = datetime.date.today() + datetime.timedelta(days=365)
        
        supabase.table('students').update({
            "status": "active",
            "subscription_end_date": str(next_year)
        }).eq("phone", student_phone).execute()

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(debug=True)
