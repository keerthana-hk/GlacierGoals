
with open(r'd:\2026 resolution tracker\templates\vault.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 282-498 (0-indexed: 281-497) are the old lock screens — replace them
new_lock_block = '''    <!-- LOCK SCREENS -->
    {% if not has_pin %}
    <!-- FIRST TIME SETUP -->
    <div class="lock-screen">
        <div style="font-size:5rem;margin-bottom:10px;">🔐</div>
        <h2 style="font-family:'Outfit';font-size:2rem;margin:0 0 10px;">Let\'s Protect Your Diary!</h2>
        <p style="color:var(--text-light);margin-bottom:25px;font-size:0.95rem;line-height:1.7;">
            Create a <strong>secret password or PIN</strong> that only you know.<br>
            You\'ll enter it every time you open your diary. 🔒
        </p>
        <form action="{{ url_for(\'setup_vault_pin\') }}" method="POST">
            <input type="password" name="pin" class="simple-pin-input" placeholder="Create your password or PIN..." required minlength="4" autocomplete="new-password">
            <p style="font-size:0.8rem;color:var(--text-light);margin:8px 0 20px;">💡 Tip: At least 4 characters. A word, numbers, or mix — your choice!</p>
            <button type="submit" class="big-unlock-btn">✅ Save Password &amp; Open My Diary</button>
        </form>
    </div>

    {% elif not unlocked %}
    <!-- MAIN LOCK SCREEN -->
    <div class="lock-screen">
        <div style="font-size:4.5rem;margin-bottom:8px;animation:bounceLock 2.5s infinite ease-in-out;">🔒</div>
        <h2 style="font-family:\'Outfit\';font-size:2rem;margin:0 0 8px;">Your Diary is Locked</h2>
        <p style="color:var(--text-light);margin-bottom:28px;font-size:0.95rem;">Enter your password or PIN to open it.</p>

        <form action="{{ url_for(\'unlock_vault\') }}" method="POST" id="unlock-form">
            <input type="hidden" name="pin" id="unlock-pin-value">

            <!-- PIN PAD MODE (default) -->
            <div id="mode-pin" class="lock-mode">
                <div class="pin-dots-row">
                    <span class="pindot" id="dot-0"></span>
                    <span class="pindot" id="dot-1"></span>
                    <span class="pindot" id="dot-2"></span>
                    <span class="pindot" id="dot-3"></span>
                    <span class="pindot" id="dot-4"></span>
                    <span class="pindot" id="dot-5"></span>
                </div>
                <div class="friendly-numpad">
                    <button type="button" class="np-btn" onclick="np(\'1\')">1</button>
                    <button type="button" class="np-btn" onclick="np(\'2\')">2</button>
                    <button type="button" class="np-btn" onclick="np(\'3\')">3</button>
                    <button type="button" class="np-btn" onclick="np(\'4\')">4</button>
                    <button type="button" class="np-btn" onclick="np(\'5\')">5</button>
                    <button type="button" class="np-btn" onclick="np(\'6\')">6</button>
                    <button type="button" class="np-btn" onclick="np(\'7\')">7</button>
                    <button type="button" class="np-btn" onclick="np(\'8\')">8</button>
                    <button type="button" class="np-btn" onclick="np(\'9\')">9</button>
                    <button type="button" class="np-btn np-del" onclick="npDel()">⌫</button>
                    <button type="button" class="np-btn" onclick="np(\'0\')">0</button>
                    <button type="button" class="np-btn np-ok" onclick="npSubmit()">✓</button>
                </div>
                <button type="button" class="switch-mode-link" onclick="showMode(\'password\')">🔤 Use text password instead</button>
            </div>

            <!-- TEXT PASSWORD MODE -->
            <div id="mode-password" class="lock-mode" style="display:none;">
                <input type="password" id="text-pwd-input" class="simple-pin-input" placeholder="Type your password here..." autocomplete="current-password">
                <button type="button" class="big-unlock-btn" onclick="pwdSubmit()" style="margin-top:15px;">🔓 Open My Diary</button>
                <button type="button" class="switch-mode-link" onclick="showMode(\'pin\')" style="margin-top:10px;">🔢 Use PIN pad instead</button>
            </div>
        </form>

        <div style="margin-top:30px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.15);text-align:center;">
            <button type="button" class="switch-mode-link" style="color:#e74c3c;" onclick="document.getElementById(\'forgot-modal\').classList.add(\'active\')">
                😟 Forgot my password? Click here to reset
            </button>
        </div>
    </div>

    <!-- Forgot Modal -->
    <div class="modal-overlay" id="forgot-modal">
        <div class="modal clay-card" style="max-width:420px;padding:35px;border-radius:28px;text-align:center;">
            <div style="font-size:3.5rem;margin-bottom:10px;">😟</div>
            <h3 style="margin:0 0 10px;font-family:\'Outfit\';font-size:1.6rem;">Forgot Your Diary Password?</h3>
            <p style="color:var(--text-light);font-size:0.95rem;line-height:1.7;margin-bottom:25px;">
                Enter your <strong>GlacierGoals login password</strong><br>
                (the one you use to log in to the app) to reset your diary password.
            </p>
            <form action="{{ url_for(\'forgot_vault_pin\') }}" method="POST">
                <input type="password" name="account_password" class="simple-pin-input" placeholder="Your app login password..." required autocomplete="current-password">
                <button type="submit" class="big-unlock-btn" style="background:linear-gradient(135deg,#e74c3c,#c0392b);margin-top:15px;">🔄 Reset My Diary Password</button>
            </form>
            <button type="button" onclick="document.getElementById(\'forgot-modal\').classList.remove(\'active\')" class="switch-mode-link" style="margin-top:15px;">← Go back to login</button>
        </div>
    </div>

    <script>
    document.addEventListener(\'DOMContentLoaded\', () => {
        let pinStr = \'\';
        const MAX = 6;
        function updateDots() {
            for(let i=0;i<MAX;i++){
                const d=document.getElementById(\'dot-\'+i);
                if(d) d.classList.toggle(\'filled\', i<pinStr.length);
            }
        }
        window.np = function(c){
            if(pinStr.length>=MAX) return;
            pinStr+=c; updateDots();
            if(pinStr.length===MAX) setTimeout(npSubmit,250);
        };
        window.npDel = function(){ pinStr=pinStr.slice(0,-1); updateDots(); };
        window.npSubmit = function(){
            if(!pinStr) return;
            document.getElementById(\'unlock-pin-value\').value=pinStr;
            document.getElementById(\'unlock-form\').submit();
        };
        window.pwdSubmit = function(){
            const val=document.getElementById(\'text-pwd-input\').value;
            if(!val) return;
            document.getElementById(\'unlock-pin-value\').value=val;
            document.getElementById(\'unlock-form\').submit();
        };
        const pwdEl=document.getElementById(\'text-pwd-input\');
        if(pwdEl) pwdEl.addEventListener(\'keydown\',e=>{ if(e.key===\'Enter\') pwdSubmit(); });
        window.showMode=function(mode){
            document.getElementById(\'mode-pin\').style.display=mode===\'pin\'?\'block\':\'none\';
            document.getElementById(\'mode-password\').style.display=mode===\'password\'?\'block\':\'none\';
            if(mode===\'password\' && pwdEl) pwdEl.focus();
        };
    });
    </script>
'''

# Replace lines 282-498 (0-indexed 281-497)
new_lines = lines[:281] + [new_lock_block + '\n'] + lines[498:]

with open(r'd:\2026 resolution tracker\templates\vault.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Done! Patched vault.html lock system.")
print(f"New line count: {len(new_lines)}")
