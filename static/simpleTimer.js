function simpleTimer(elementId, options = {}) {
  var type = options.type || "increase"; // increase, decrease
  var time = type === "increase" ? 0 : 60 * 12;
  var ele = document.getElementById(elementId);

  ele.innerHTML = `
  <div class="simple-timer_container">
    <div class="simple-timer_timer">
      <button class="simple-timer_button">
        <div class="simple-timer_min">00</div>
        <div class="simple-timer_div">:</div>
        <div class="simple-timer_sec">00</div>
      </button>
    </div>
    <div class="simple-timer_option">
      <button class="simple-timer_reset-button">
        <span>Reset<span>
      </button>
    </div>
  </div>`;

  var button = ele.getElementsByClassName("simple-timer_button")[0];
  var resetButton = ele.getElementsByClassName("simple-timer_reset-button")[0];
  var minBox = ele.getElementsByClassName("simple-timer_min")[0];
  var secBox = ele.getElementsByClassName("simple-timer_sec")[0];
  var timerInnerHtml = button.children[0];
  var isStart = false;
  var isPaused = false;
  var timer;

  button.addEventListener("click", () => {
    if (!isStart) {
      start();
    } else {
      pause();
    }
  });
  resetButton.addEventListener("click", stop);

  function init() {
    time = type === "increase" ? 0 : 60 * 12;
    isPaused = false;
    isStart = false;
    minBox.innerHTML = "".padStart(2, 0);
    secBox.innerHTML = "".padStart(2, 0);
  }

  function render() {
    if (!isPaused) {
      time = time + (type === "increase" ? 1 : -1);
      var min = Math.floor(time / 60);
      var sec = time % 60;
      minBox.innerHTML = ("" + min).padStart(2, 0);
      secBox.innerHTML = ("" + sec).padStart(2, 0);
    }
  }

  function start() {
    isStart = true;
    timer = setInterval(render, 1000);
  }

  function stop() {
    clearInterval(timer);
    timer = null;
    init();
  }

  function pause() {
    console.log("isPaused", isPaused);
    isPaused = !isPaused;
  }
}
