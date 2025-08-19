async function loadRecent(){
      const countSpan = document.getElementById('recentCount');
      const loading = document.getElementById('recentLoading');
      const table = document.getElementById('recentTable');
      const tbody = document.getElementById('recentTbody');
      const err = document.getElementById('recentError');
      loading.style.display = 'block';
      table.style.display = 'none';
      err.style.display = 'none';
      tbody.innerHTML = '';
      try{
        const url = recentQuery
        // const r = await fetch('/questions?limit=100&offset=0');
        // if(!r.ok) throw new Error('HTTP '+r.status);
        // const rows = await r.json();
        const [r, totalRes] = await Promise.all([
          fetch('/questions?limit=100&offset=0'),
          fetch('/stats/total')
        ]);
        if(!r.ok) throw new Error('HTTP '+r.status);
        const rows = await r.json();
        const total = (totalRes.ok ? (await totalRes.json()).total : null);
        if (countSpan) countSpan.textContent = total !== null ? `(${total})` : '';
        if(!Array.isArray(rows) || rows.length===0){
          tbody.innerHTML = '<tr><td colspan="5" style="padding:8px;color:#aaa;">Kayıt bulunamadı.</td></tr>';
        }else{
          const safe = (s)=> String(s ?? '').replace(/[<>]/g, ch => ({'<':'&lt;','>':'&gt;'}[ch]));
          for(const x of rows){
            tbody.insertAdjacentHTML('beforeend',
              `<tr data-row-id="${x.id ?? ''}">
                 <td style="border-bottom:1px solid #222;padding:8px;">${x.id ?? ''}</td>
                 <td style="border-bottom:1px solid #222;padding:8px;">${safe(x.question)}</td>
                 <td style="border-bottom:1px solid #222;padding:8px;">${safe(x.category)}</td>
                 <td style="border-bottom:1px solid #222;padding:8px;">${safe(x.created_at)}</td>
                 <td style="border-bottom:1px solid #222;padding:8px;">
                    <button class="btn-del" data-id="${x.id ?? ''}" style="background:#933;color:#fff;border:0;padding:6px 10px;cursor:pointer;">Sil</button>
                  </td>
               </tr>`);
          }
        }
        table.style.display = 'table';
      }catch(e){
        err.textContent = 'Hata: ' + e;
        err.style.display = 'block';
      }finally{
        loading.style.display = 'none';
      }
    }
    document.getElementById('btnRecent').onclick = async ()=>{ openRecent(); await loadRecent(); };
    document.getElementById('refreshRecent').onclick = loadRecent;
    document.getElementById('recentTbody').addEventListener('click', async (e) => {
      const btn = e.target.closest('.btn-del');
      if (!btn) return;
      const id = btn.getAttribute('data-id');
      if (!id) return;
      if (!confirm('Bu soruyu silmek istediğinize emin misiniz?')) return;

      try {
        const r = await fetch(`/questions/${id}`, { method: 'DELETE' });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        // satırı DOM'dan kaldır
        const tr = btn.closest('tr');
        if (tr) tr.remove();
      } catch (err) {
        alert('Silme hatası: ' + err);
      }
    });

    const catSel = document.getElementById('categorySel');
    catSel.addEventListener('change', () => {
      if (catSel.value === '__new__') {
        const yeni = prompt('Yeni kategori adı:');
        if (yeni && yeni.trim()) {
          const opt = document.createElement('option');
          opt.value = yeni.trim();
          opt.textContent = yeni.trim();
          catSel.insertBefore(opt, catSel.lastElementChild); // "Yeni ekle" seçeneğinin üstüne koy
          catSel.value = yeni.trim(); // otomatik seç
        } else {
          catSel.value = ''; // boşsa sıfırla
        }
      }
    });