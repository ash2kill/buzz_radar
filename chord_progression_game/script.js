const KEYS = {
  C: ["C", "Dm", "Em", "F", "G", "Am", "Bdim"],
  G: ["G", "Am", "Bm", "C", "D", "Em", "F#dim"],
  D: ["D", "Em", "F#m", "G", "A", "Bm", "C#dim"],
  A: ["A", "Bm", "C#m", "D", "E", "F#m", "G#dim"],
  F: ["F", "Gm", "Am", "Bb", "C", "Dm", "Edim"],
};

const PROGRESSIONS = [
  { name: "王道進行", numerals: [6, 4, 1, 5] },
  { name: "カノン進行", numerals: [1, 5, 6, 3, 4, 1, 4, 5] },
  { name: "小室進行", numerals: [6, 4, 5, 1] },
  { name: "循環進行", numerals: [1, 6, 2, 5] },
  { name: "I-V-vi-IV", numerals: [1, 5, 6, 4] },
  { name: "4-5-3-6", numerals: [4, 5, 3, 6] },
];

let score = 0;
let streak = 0;
let questionCount = 0;
let currentAnswer = "";
let locked = false;

const scoreEl = document.getElementById("score");
const streakEl = document.getElementById("streak");
const questionCountEl = document.getElementById("question-count");
const promptEl = document.getElementById("prompt");
const choicesEl = document.getElementById("choices");
const feedbackEl = document.getElementById("feedback");
const nextBtn = document.getElementById("next-btn");

function randomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function numeralsToChords(keyName, numerals) {
  const scale = KEYS[keyName];
  return numerals.map((degree) => scale[degree - 1]).join(" - ");
}

function allCandidateAnswers() {
  const all = [];
  for (const keyName of Object.keys(KEYS)) {
    for (const progression of PROGRESSIONS) {
      all.push(numeralsToChords(keyName, progression.numerals));
    }
  }
  return all;
}

function shuffle(array) {
  const copied = [...array];
  for (let i = copied.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copied[i], copied[j]] = [copied[j], copied[i]];
  }
  return copied;
}

function renderStats() {
  scoreEl.textContent = String(score);
  streakEl.textContent = String(streak);
  questionCountEl.textContent = String(questionCount);
}

function disableChoices() {
  for (const btn of choicesEl.querySelectorAll("button")) {
    btn.disabled = true;
  }
}

function handleAnswer(btn) {
  if (locked) return;
  locked = true;

  const selected = btn.dataset.answer;
  const isCorrect = selected === currentAnswer;

  if (isCorrect) {
    score += 10;
    streak += 1;
    btn.classList.add("correct");
    feedbackEl.textContent = "✅ 正解！グッドボイスリーディング！";
  } else {
    score = Math.max(0, score - 5);
    streak = 0;
    btn.classList.add("wrong");
    feedbackEl.textContent = `❌ 不正解。正解は ${currentAnswer}`;

    for (const other of choicesEl.querySelectorAll("button")) {
      if (other.dataset.answer === currentAnswer) {
        other.classList.add("correct");
      }
    }
  }

  disableChoices();
  renderStats();
}

function createChoice(answerText) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "choice-btn";
  btn.textContent = answerText;
  btn.dataset.answer = answerText;
  btn.addEventListener("click", () => handleAnswer(btn));
  return btn;
}

function nextQuestion() {
  const keyName = randomItem(Object.keys(KEYS));
  const progression = randomItem(PROGRESSIONS);

  questionCount += 1;
  locked = false;
  feedbackEl.textContent = "";

  promptEl.textContent = `キー: ${keyName} / ${progression.name} (${progression.numerals
    .map((n) => `${n}`)
    .join("-")})`;

  currentAnswer = numeralsToChords(keyName, progression.numerals);

  const pool = allCandidateAnswers().filter((candidate) => candidate !== currentAnswer);
  const options = shuffle([currentAnswer, ...shuffle(pool).slice(0, 3)]);

  choicesEl.innerHTML = "";
  for (const option of options) {
    choicesEl.appendChild(createChoice(option));
  }

  renderStats();
}

nextBtn.addEventListener("click", nextQuestion);
renderStats();
