import { State, setUser, setRoom } from './state.js';
import { upsertUser, createRoom, joinRoom, getRoom, getQuestion, setQuestion, sendAnswer, listAnswers } from './api.js';
import { toast, renderAnswers } from './ui.js';
import { connectWS } from './socket.js';

// Init Telegram WebApp context
(function initTelegram() {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    if (tg?.initDataUnsafe?.user) {
      const u = tg.initDataUnsafe.user;
      setUser({ tg_user_id: String(u.id), name: [u.first_name, u.last_name].filter(Boolean).join(' ') });
    }
    // IMPORTANT: In production, verify initData hash on backend.
    // See: https://core.telegram.org/bots/webapps#initializing-mini-apps
  } else {
    // Dev fallback
    const demoId = localStorage.getItem('demo_tg_id') || String(Math.floor(Math.random()*1e9));
    localStorage.setItem('demo_tg_id', demoId);
    setUser({ tg_user_id: demoId, name: 'Dev User' });
  }
})();

const isRoomPage = location.pathname.endsWith('/room.html') || document.title.includes('Комната');

if (!isRoomPage) {
  // Lobby logic
  const btnCreate = document.getElementById('btnCreate');
  const btnJoin = document.getElementById('btnJoin');
  const inputCode = document.getElementById('roomCode');
  const createResult = document.getElementById('createResult');
  const joinError = document.getElementById('joinError');

  (async () => {
    await upsertUser(State.user.tg_user_id, State.user.name);
  })();

  btnCreate?.addEventListener('click', async () => {
    try {
      const data = await createRoom();
      createResult.textContent = `Код вашей комнаты: ${data.room_code}`;
      // Navigate to room
      location.href = `/room.html#${data.room_id}`;
    } catch (e) {
      toast(e.message || 'Ошибка создания комнаты');
    }
  });

  btnJoin?.addEventListener('click', async () => {
    try {
      const code = (inputCode.value || '').trim().toUpperCase();
      if (code.length !== 6) throw new Error('Код должен состоять из 6 символов');
      const res = await joinRoom(code);
      location.href = `/room.html#${res.room_id}`;
    } catch (e) {
      joinError.textContent = e.message || 'Ошибка входа';
      setTimeout(() => { joinError.textContent = ''; }, 3000);
    }
  });

} else {
  // Room logic
  const roomId = Number(location.hash.replace('#','') || '0');
  if (!roomId) {
    location.href = '/';
    throw new Error('Room ID missing');
  }

  const elCode = document.getElementById('roomCode');
  const elStatus = document.getElementById('roomStatus');
  const elSuper = document.getElementById('superCount');
  const elQ = document.getElementById('questionBlock');
  const inQ = document.getElementById('questionInput');
  const btnSetQ = document.getElementById('btnSetQuestion');
  const inA = document.getElementById('answerInput');
  const btnA = document.getElementById('btnSendAnswer');
  const list = document.getElementById('answersList');

  (async () => {
    await upsertUser(State.user.tg_user_id, State.user.name);
    const room = await getRoom(roomId);
    elCode.textContent = `Код: ${room.room_code}`;
    elStatus.textContent = room.status === 'active' ? '• активна' : '• закрыта';
    State.user.super_cards = room.players.find(p => p.user_id === room.players.user_id)?.super_cards ?? State.user.super_cards;
    elSuper.textContent = String(State.user.super_cards);

    const q = await getQuestion(roomId);
    State.room.round = q.round_id ? { id: q.round_id, text: q.text, status: q.status } : null;
    elQ.textContent = q.text || 'Пока вопрос не задан';

    if (State.room.round?.id) {
      const data = await listAnswers(roomId, State.room.round.id);
      await renderAnswers(list, data);
    }
  })();

  connectWS(async (msg) => {
    if (msg.type === 'answer_added' && State.room.round?.id) {
      const data = await listAnswers(roomId, State.room.round.id);
      await renderAnswers(list, data);
    }
    if (msg.type === 'answer_revealed' && State.room.round?.id) {
      const data = await listAnswers(roomId, State.room.round.id);
      await renderAnswers(list, data);
    }
  });

  btnSetQ.addEventListener('click', async () => {
    try {
      const text = (inQ.value || '').trim();
      if (!text) { toast('Введите вопрос'); return; }
      const res = await setQuestion(roomId, text);
      State.room.round = { id: res.round_id, text: res.text, status: res.status };
      document.getElementById('questionBlock').textContent = res.text;
      inQ.value = '';
      const data = await listAnswers(roomId, State.room.round.id);
      await renderAnswers(list, data);
      toast('Вопрос установлен. Сбор ответов!');
    } catch (e) {
      toast(e.message || 'Ошибка установки вопроса');
    }
  });

  btnA.addEventListener('click', async () => {
    try {
      const text = (inA.value || '').trim();
      if (!text) { toast('Введите ответ'); return; }
      if (!State.room.round?.id) { toast('Сначала задайте вопрос'); return; }
      await sendAnswer(roomId, State.room.round.id, text);
      inA.value = '';
      toast('Ответ отправлен');
    } catch (e) {
      toast(e.message || 'Не удалось отправить ответ');
    }
  });
}
