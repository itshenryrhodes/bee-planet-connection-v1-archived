<script>
(function(){
  const sel = (s, r=document) => r.querySelector(s);
  const endpointFromConfig = async () => {
    try{
      const r = await fetch('/data/newsletter.json', {cache:'no-store'});
      if(!r.ok) return "";
      const j = await r.json();
      return (j.endpoint||"").trim();
    }catch(_){ return ""; }
  };

  async function boot(){
    const form = sel('[data-nl-form]');
    if(!form) return;
    const msg = sel('[data-nl-msg]');
    const btn = sel('[data-nl-btn]');
    const email = sel('input[type="email"]', form);
    const consent = sel('input[name="consent"]', form);
    let endpoint = form.getAttribute('data-endpoint') || "";
    if(!endpoint) endpoint = await endpointFromConfig();

    let hp = sel('input[name="website"]', form);
    if(!hp){
      hp = document.createElement('input');
      hp.type = 'text'; hp.name = 'website'; hp.autocomplete = 'off';
      hp.style.position='absolute'; hp.style.left='-9999px';
      form.appendChild(hp);
    }

    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      msg.className = 'nl-msg'; msg.textContent = '';
      if(hp.value){ return; }
      if(!endpoint){ msg.className='nl-msg err'; msg.textContent='Signup temporarily unavailable.'; return; }
      if(!email.value || !/.+@.+\..+/.test(email.value)){ msg.className='nl-msg err'; msg.textContent='Please enter a valid email address.'; return; }
      if(consent && !consent.checked){ msg.className='nl-msg err'; msg.textContent='Please confirm consent.'; return; }

      btn.disabled = true; btn.textContent = 'Subscribing…';
      try{
        const res = await fetch(endpoint, {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ email: email.value, consent: true, ref: document.referrer || location.href })
        });
        const data = await res.json().catch(()=>({}));
        if(data.ok && (data.confirmed || data.already)){
          msg.className = 'nl-msg ok';
          msg.textContent = 'You’re subscribed! Redirecting…';
          setTimeout(()=>{ location.href = (data.redirect || '/newsletter/thanks.html'); }, 800);
          form.reset();
        }else if(data.ok && data.pending){
          msg.className = 'nl-msg ok';
          msg.textContent = 'Please check your inbox to confirm.';
          form.reset();
        }else{
          msg.className = 'nl-msg err';
          msg.textContent = data.error || 'Sorry, something went wrong.';
        }
      }catch(err){
        msg.className = 'nl-msg err';
        msg.textContent = 'Network error. Please try again.';
      }finally{
        btn.disabled = false; btn.textContent = 'Subscribe';
      }
    });
  }
  document.addEventListener('DOMContentLoaded', boot);
})();
</script>
