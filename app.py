<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TGP Admin Panel</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #6366f1; --bg: #f3f4f6; --white: #ffffff; --text: #1f2937; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Hind Siliguri', sans-serif; }
        body { background: var(--bg); display: flex; min-height: 100vh; }
        .sidebar { width: 260px; background: var(--white); height: 100vh; position: fixed; border-right: 1px solid #e5e7eb; z-index: 1000; }
        .brand { font-size: 24px; font-weight: 700; color: var(--primary); padding: 25px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f3f4f6; }
        .menu { padding: 20px; }
        .menu-item { display: flex; align-items: center; padding: 14px 20px; color: #4b5563; text-decoration: none; margin-bottom: 8px; border-radius: 10px; cursor: pointer; transition: 0.3s; font-weight: 500; }
        .menu-item:hover, .menu-item.active { background: var(--primary); color: white; }
        .menu-item i { margin-right: 15px; width: 20px; text-align: center; }
        .main-content { margin-left: 260px; padding: 30px; width: calc(100% - 260px); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .card h3 { color: #6b7280; font-size: 15px; margin-bottom: 10px; }
        .card p { font-size: 28px; font-weight: 700; color: var(--text); }
        .table-container { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow-x: auto; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; }
        th { background: #f9fafb; padding: 16px; text-align: left; border-bottom: 2px solid #e5e7eb; font-weight: 600; }
        td { padding: 16px; border-bottom: 1px solid #f3f4f6; color: #4b5563; }
        .status-badge { padding: 6px 12px; border-radius: 50px; font-size: 13px; font-weight: 600; display: inline-block; }
        .status-active, .status-approved { background: #dcfce7; color: #15803d; }
        .status-free, .status-pending { background: #fef3c7; color: #b45309; }
        .status-banned, .status-rejected { background: #fee2e2; color: #b91c1c; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; color: white; background: var(--primary); }
        .btn-success { background: #22c55e; } .btn-danger { background: #ef4444; }
        .page-section { display: none; } .active-page { display: block; }
        .student-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="brand"><i class="fas fa-graduation-cap"></i> TGP Admin</div>
        <div class="menu">
            <div class="menu-item active" onclick="showPage('dashboard')"><i class="fas fa-home"></i> ড্যাশবোর্ড</div>
            <div class="menu-item" onclick="showPage('students')"><i class="fas fa-users"></i> স্টুডেন্ট লিস্ট</div>
            <div class="menu-item" onclick="showPage('payments')"><i class="fas fa-wallet"></i> পেমেন্ট রিকোয়েস্ট</div>
            <div class="menu-item" onclick="showPage('settings')"><i class="fas fa-cog"></i> সেটিংস</div>
        </div>
    </div>

    <div class="main-content">
        
        <!-- ড্যাশবোর্ড -->
        <div id="dashboard-page" class="page-section active-page">
            <div class="header"><h2>📊 ব্যবসার অবস্থা</h2><button class="btn" onclick="loadDashboard()"><i class="fas fa-sync"></i> রিফ্রেশ</button></div>
            <div class="stats-grid">
                <div class="card"><h3>মোট স্টুডেন্ট</h3><p id="total-users">0</p></div>
                <div class="card"><h3>ফ্রি ট্রায়াল</h3><p id="free-users">0</p></div>
                <div class="card"><h3>পেইড মেম্বার</h3><p id="paid-users">0</p></div>
                <div class="card"><h3>মোট ইনকাম</h3><p style="color: #10b981;">৳ <span id="total-income">0</span></p></div>
            </div>
        </div>

        <!-- স্টুডেন্ট লিস্ট -->
        <div id="students-page" class="page-section">
            <div class="header"><h2>👥 সব স্টুডেন্ট</h2><input type="text" id="search-input" placeholder="🔍 খুঁজুন..." onkeyup="searchStudent()" style="padding:10px; border:1px solid #ddd; border-radius:5px;"></div>
            <div class="table-container">
                <table>
                    <thead><tr><th>ছবি</th><th>নাম & ফোন</th><th>স্কুল</th><th>স্ট্যাটাস</th><th>অ্যাকশন</th></tr></thead>
                    <tbody id="student-table-body"></tbody>
                </table>
            </div>
        </div>

        <!-- পেমেন্ট পেজ -->
        <div id="payments-page" class="page-section">
            <div class="header"><h2>💸 পেমেন্ট হিস্ট্রি</h2><button class="btn" onclick="fetchPayments()"><i class="fas fa-sync"></i> চেক করুন</button></div>
            <div class="table-container">
                <table>
                    <thead><tr><th>ফোন নম্বর</th><th>মেথড</th><th>TRX ID</th><th>পরিমাণ</th><th>স্ট্যাটাস</th></tr></thead>
                    <tbody id="payment-table-body">
                        <tr><td colspan="5" style="text-align:center">লোডিং...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- সেটিংস পেজ -->
        <div id="settings-page" class="page-section">
            <div class="header"><h2>⚙️ সেটিংস</h2></div>
            <div class="card"><h3>ওয়ালেট কনফিগারেশন</h3><p style="font-size:16px; font-weight:400;">সব পেমেন্ট অটোমেটিক NOWPayments এর মাধ্যমে আপনার Cake Wallet এ জমা হচ্ছে।</p></div>
        </div>

    </div>

    <script>
        // 👇 আপনার রেন্ডার লিংক
        const API_BASE_URL = "https://tgp-backend-ppga.onrender.com"; 

        function showPage(pageId) {
            document.querySelectorAll('.page-section').forEach(el => el.classList.remove('active-page'));
            document.getElementById(pageId + '-page').classList.add('active-page');
            document.querySelectorAll('.menu-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
            if(pageId === 'students') fetchStudents();
            if(pageId === 'payments') fetchPayments();
        }

        async function loadDashboard() {
            try {
                const res = await fetch(`${API_BASE_URL}/dashboard_stats`);
                const data = await res.json();
                document.getElementById('total-users').innerText = data.total || 0;
                document.getElementById('free-users').innerText = data.free || 0;
                document.getElementById('paid-users').innerText = data.paid || 0;
                document.getElementById('total-income').innerText = data.income || 0;
            } catch (e) { console.error(e); }
        }

        async function fetchStudents(query = '') {
            const tbody = document.getElementById('student-table-body');
            try {
                const res = await fetch(`${API_BASE_URL}/get_students?search=${query}`);
                const students = await res.json();
                let html = '';
                students.forEach(std => {
                    let badge = std.status === 'active' ? 'status-active' : (std.status === 'banned' ? 'status-banned' : 'status-free');
                    let img = std.photo_url || 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png';
                    html += `<tr>
                        <td><img src="${img}" class="student-img"></td>
                        <td><b>${std.name}</b><br><small>${std.phone}</small></td>
                        <td>${std.school_name || '-'}</td>
                        <td><span class="status-badge ${badge}">${std.status}</span></td>
                        <td><button class="btn-success" onclick="upStatus('${std.phone}','approve')" style="padding:5px; border-radius:4px;"><i class="fas fa-check"></i></button> 
                            <button class="btn-danger" onclick="upStatus('${std.phone}','ban')" style="padding:5px; border-radius:4px;"><i class="fas fa-ban"></i></button></td>
                    </tr>`;
                });
                tbody.innerHTML = html || '<tr><td colspan="5" align="center">No Data</td></tr>';
            } catch (e) { tbody.innerHTML = '<tr><td colspan="5" align="center">Error Loading</td></tr>'; }
        }

        async function fetchPayments() {
            const tbody = document.getElementById('payment-table-body');
            try {
                const res = await fetch(`${API_BASE_URL}/get_payments`);
                const payments = await res.json();
                let html = '';
                payments.forEach(pay => {
                    let badge = pay.status === 'approved' ? 'status-approved' : 'status-pending';
                    html += `<tr>
                        <td>${pay.student_phone}</td>
                        <td><span style="color:#f7931a; font-weight:bold;">${pay.method}</span></td>
                        <td>${pay.trx_id}</td>
                        <td>৳ ${pay.amount}</td>
                        <td><span class="status-badge ${badge}">${pay.status.toUpperCase()}</span></td>
                    </tr>`;
                });
                tbody.innerHTML = html || '<tr><td colspan="5" align="center">No Payments Yet</td></tr>';
            } catch (e) { tbody.innerHTML = '<tr><td colspan="5" align="center">Error Loading</td></tr>'; }
        }

        async function upStatus(phone, action) {
            if(!confirm("Are you sure?")) return;
            await fetch(`${API_BASE_URL}/update_status`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({phone, action}) });
            fetchStudents();
        }

        function searchStudent() { fetchStudents(document.getElementById('search-input').value); }
        loadDashboard();
    </script>
</body>
</html>
