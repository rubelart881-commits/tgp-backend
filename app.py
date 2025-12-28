from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import datetime

app = Flask(__name__)
CORS(app) # এটা না দিলে ওয়েবসাইট থেকে ডাটা আসবে না

# --- কনফিগারেশন (Supabase থেকে নিয়ে বসাও) ---
SUPABASE_URL = "https://gzgmtofyvfjknoectxgb.supabase.co"
SUPABASE_KEY = "sb_publishable_gYC68V5SQn6_OxXU2sCbvA_RrRFM0Xt"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- ১. সব স্টুডেন্ট লিস্ট দেখার API (Search সহ) ---
@app.route('/get_students', methods=['GET'])
def get_students():
    search_query = request.args.get('search', '')
    filter_status = request.args.get('status', 'all')
    
    query = supabase.table('students').select("*")
    
    # যদি সার্চ করে
    if search_query:
        # নাম, ফোন বা ইমেইল দিয়ে সার্চ লজিক
        query = query.or_(f"name.ilike.%{search_query}%,phone.ilike.%{search_query}%,email.ilike.%{search_query}%")
    
    # যদি স্ট্যাটাস ফিল্টার করে (যেমন: শুধু free_trial দেখব)
    if filter_status != 'all':
        query = query.eq('status', filter_status)
        
    response = query.execute()
    return jsonify(response.data)

# --- ২. নতুন স্টুডেন্ট অ্যাড করা (App থেকে কল হবে) ---
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    
    # ৩ দিনের ফ্রি ট্রায়াল লজিক
    trial_end = datetime.date.today() + datetime.timedelta(days=3)
    
    new_user = {
        "name": data.get('name'),
        "phone": data.get('phone'),
        "email": data.get('email'),
        "school_name": data.get('school'),
        "parent_name": data.get('parent'),
        "address": data.get('address'),
        "photo_url": data.get('img_url'), # ImgBB লিংক
        "status": "free_trial",
        "subscription_end_date": str(trial_end),
        "referred_by": data.get('ref_code', '')
    }
    
    try:
        data = supabase.table('students').insert(new_user).execute()
        return jsonify({"message": "Student Added Successfully!", "data": data.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- ৩. স্ট্যাটাস কন্ট্রোল (Ban/Approve/Subscription Add) ---
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    phone = data.get('phone')
    action = data.get('action') # ban, approve, extend
    
    update_data = {}
    
    if action == 'ban':
        update_data['status'] = 'banned'
    elif action == 'approve':
        update_data['status'] = 'active'
        # ১ বছরের সাবস্ক্রিপশন সেট করা
        next_year = datetime.date.today() + datetime.timedelta(days=365)
        update_data['subscription_end_date'] = str(next_year)
    elif action == 'free_trial':
        update_data['status'] = 'free_trial'
    
    try:
        response = supabase.table('students').update(update_data).eq('phone', phone).execute()
        return jsonify({"message": f"User {action} successful!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --- ৪. ড্যাশবোর্ড স্ট্যাটস (Income, Total User) ---
@app.route('/dashboard_stats', methods=['GET'])
def dashboard_stats():
    # মোট স্টুডেন্ট
    total_students = supabase.table('students').select("*", count='exact').execute().count
    
    # ফ্রি ট্রায়াল ইউজার
    free_users = supabase.table('students').select("*", count='exact').eq('status', 'free_trial').execute().count
    
    # এক্টিভ পেইড ইউজার
    paid_users = supabase.table('students').select("*", count='exact').eq('status', 'active').execute().count
    
    return jsonify({
        "total": total_students,
        "free": free_users,
        "paid": paid_users,
        # ইনকাম ক্যালকুলেশন পরে পেমেন্ট টেবিল থেকে আসবে
        "income": paid_users * 2000 
    })

if __name__ == '__main__':
    app.run(debug=True)