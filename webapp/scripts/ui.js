import { State } from './state.js';
import { reveal, listAnswers } from './api.js';

export function toast(text) {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = 'card';
  t.style.position = 'fixed';
  t.style.right = '12px';
  t.style.bottom = '12px';
  t.style.pointerEvents = 'auto';
  t.textContent = text;
  c.appendChild(t);
  setTimeout(() => t.remove(), 2500);
}

export function confirmModal(text) {
  return new Promise((resolve) => {
    const overlay = document.getElementById('modalContainer');
    document.getElementById('modalText').textContent = text;
    overlay.classList.remove('hidden');
    const onCancel = () => { cleanup(); resolve(false); };
    const onOk = () => { cleanup(); resolve(true); };
    const cancelBtn = document.getElementById('modalCancel');
    const okBtn = document.getElementById('modalOk');
    cancelBtn.onclick = onCancel;
    okBtn.onclick = onOk;
    function cleanup() { overlay.classList.add('hidden'); cancelBtn.onclick = okBtn.onclick = null; }
  });
}

export async function renderAnswers(container, answers) {
  const empty = document.getElementById('emptyAnswers');
  empty.style.display = answers.length ? 'none' : 'block';
  container.innerHTML = '';
  for (const a of answers) {
    const card = document.createElement('div');
    card.className = 'card answer';
    card.dataset.answerId = a.answer_id;
    const inner = document.createElement('div');
    inner.className = 'card-inner';

    const front = document.createElement('div');
    front.className = 'card-face front';
    front.innerHTML = `<div>${escapeHtml(a.text)}</div>
      ${!a.revealed ? `<div class="row" style="margin-top:12px;"><button class="btn danger btn-reveal">Вскрыть</button></div>` : ''}`;

    const back = document.createElement('div');
    back.className = 'card-face back';
    back.innerHTML = a.revealed ? `<b>Автор:</b> ${escapeHtml(a.author_display || '')}` : `<i>Автор будет показан после вскрытия</i>`;

    inner.appendChild(front);
    inner.appendChild(back);
    card.appendChild(inner);
    container.appendChild(card);

    if (!a.revealed) {
      const btn = front.querySelector('.btn-reveal');
      btn.addEventListener('click', async () => {
        if (State.user.super_cards <= 0) { toast('У вас закончились супер-карты'); return; }
        const ok = await confirmModal('Потратить 1 супер-карту, чтобы раскрыть автора?');
        if (!ok) return;
        try {
          const res = await reveal(State.room.id, State.room.round.id, a.answer_id);
          State.user.super_cards -= 1;
          document.getElementById('superCount').textContent = String(State.user.super_cards);
          // Flip animation
          card.classList.add('flip');
          back.innerHTML = `<b>Автор:</b> ${escapeHtml(res.author_display)}`;
          // Refresh list to update other buttons
          const data = await listAnswers(State.room.id, State.room.round.id);
          await renderAnswers(container, data);
        } catch (e) {
          toast(e.message || 'Ошибка');
        }
      });
    } else {
      card.classList.add('flip');
    }
  }
}

export function escapeHtml(str) {
  return (str ?? '').replace(/[&<>"']/g, (m) => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  })[m]);
}
