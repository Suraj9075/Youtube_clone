const form = document.getElementById('searchForm');
const interestsInput = document.getElementById('interests');
const maxInput = document.getElementById('maxResults');
const status = document.getElementById('status');
const runBtn = document.getElementById('runBtn');
const clearBtn = document.getElementById('clearBtn');
const resultsArea = document.getElementById('resultsArea');
const emptyMsg = document.getElementById('emptyMsg');

function setStatus(msg){ status.textContent = msg; }
function clearResults(){
  resultsArea.innerHTML = "";
  resultsArea.appendChild(emptyMsg);
}

function makeVideoCard(v){
  const el = document.createElement('div');
  el.className = 'video card';

  const thumb = document.createElement('div');
  thumb.className = 'thumb';

  const img = document.createElement('img');
  img.src = v.thumbnail;
  thumb.appendChild(img);

  const info = document.createElement('div');
  info.className = 'info';

  const t = document.createElement('h3');
  t.className = 'title';
  t.textContent = v.title;

  const ch = document.createElement('div');
  ch.className = 'channel';
  ch.textContent = v.channel;

  const mr = document.createElement('div');
  mr.className = 'meta-row';
  mr.textContent = `${v.published_at} • ${v.duration} • ${v.view_count} views`;

  const btn = document.createElement('button');
  btn.className = 'watch-btn';
  btn.textContent = 'Watch';
  btn.onclick = () => openPlayer(v.id);

  mr.appendChild(btn);
  info.appendChild(t);
  info.appendChild(ch);
  info.appendChild(mr);
  el.appendChild(thumb);
  el.appendChild(info);

  return el;
}

async function fetchDigest(interests, maxResults){
  setStatus("Loading...");
  runBtn.disabled = true;

  try {
    const res = await fetch(`/digest?interests=${interests}&maxResults=${maxResults}`);
    const data = await res.json();
    runBtn.disabled = false;
    return data;
  } catch(err){
    console.error(err);
    setStatus("Network error.");
    runBtn.disabled = false;
    return null;
  }
}

form.addEventListener('submit', async (e)=>{
  e.preventDefault();

  const interests = interestsInput.value.trim();
  let maxResults = parseInt(maxInput.value, 10);

  const data = await fetchDigest(interests, maxResults);
  if(!data) return;

  resultsArea.innerHTML = "";
  data.videos.forEach(v => resultsArea.appendChild(makeVideoCard(v)));

  setStatus(`Returned ${data.videos.length}`);
});

clearBtn.onclick = ()=>{
  interestsInput.value = "";
  clearResults();
  setStatus("Cleared.");
};

// Modal Player Controls
const playerModal = document.getElementById("playerModal");
const playerIframe = document.getElementById("playerIframe");
const playerClose = document.getElementById("playerClose");
const playerBackdrop = document.getElementById("playerBackdrop");

function openPlayer(id){
  playerIframe.src = `https://www.youtube.com/embed/${id}?autoplay=1`;
  playerModal.classList.add("show");
}

function closePlayer(){
  playerIframe.src = "";
  playerModal.classList.remove("show");
}

playerClose.onclick = closePlayer;
playerBackdrop.onclick = closePlayer;
