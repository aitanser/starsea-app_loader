let score = 0;
let timeLeft = 10;
let timer = null;
let running = false;

const scoreEl = document.getElementById('score');
const timerEl = document.getElementById('timer');
const clickBtn = document.getElementById('clickBtn');
const resetBtn = document.getElementById('resetBtn');

function updateDisplay() {
    scoreEl.textContent = score;
    timerEl.innerHTML = `<i class="fas fa-clock"></i> ${timeLeft} 秒`;
    if (timeLeft <= 3) timerEl.style.color = '#ff8866';
    else timerEl.style.color = '#8870b0';
}

function startGame() {
    if (running) return;
    running = true;
    score = 0;
    timeLeft = 10;
    updateDisplay();
    clickBtn.disabled = false;
    clickBtn.style.opacity = '1';
    timer = setInterval(() => {
        timeLeft--;
        updateDisplay();
        if (timeLeft <= 0) {
            clearInterval(timer);
            running = false;
            clickBtn.disabled = true;
            clickBtn.style.opacity = '0.5';
            timerEl.innerHTML = '<i class="fas fa-clock"></i> 时间到！';
            timerEl.style.color = '#ffdd70';
            scoreEl.classList.add('flash');
            setTimeout(() => scoreEl.classList.remove('flash'), 300);
        }
    }, 1000);
}

clickBtn.addEventListener('click', function() {
    if (!running) {
        startGame();
        return;
    }
    score++;
    scoreEl.textContent = score;
    scoreEl.classList.add('flash');
    setTimeout(() => scoreEl.classList.remove('flash'), 200);
});

resetBtn.addEventListener('click', function() {
    clearInterval(timer);
    running = false;
    score = 0;
    timeLeft = 10;
    clickBtn.disabled = false;
    clickBtn.style.opacity = '1';
    timerEl.style.color = '#8870b0';
    updateDisplay();
});

updateDisplay();
console.log('游戏已加载');