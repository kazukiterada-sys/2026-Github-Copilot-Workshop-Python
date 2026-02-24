/**
 * test_timer.js
 * フロントエンドタイマーロジックのJestテスト
 */

const { PomodoroTimer, DURATIONS, LONG_BREAK_INTERVAL } = require("../static/js/timer.js");

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe("PomodoroTimer - 初期状態", () => {
  test("初期セッションタイプは work であること", () => {
    const timer = new PomodoroTimer();
    expect(timer.sessionType).toBe("work");
  });

  test("初期残り時間は 25分 (1500秒) であること", () => {
    const timer = new PomodoroTimer();
    expect(timer.timeRemaining).toBe(DURATIONS.work);
    expect(timer.timeRemaining).toBe(1500);
  });

  test("初期状態は idle であること", () => {
    const timer = new PomodoroTimer();
    expect(timer.state).toBe("idle");
  });

  test("初期の completedCycles は 0 であること", () => {
    const timer = new PomodoroTimer();
    expect(timer.completedCycles).toBe(0);
  });
});

describe("PomodoroTimer - formattedTime", () => {
  test("25:00 と表示されること", () => {
    const timer = new PomodoroTimer();
    expect(timer.formattedTime).toBe("25:00");
  });

  test("0秒のとき 00:00 と表示されること", () => {
    const timer = new PomodoroTimer();
    timer.timeRemaining = 0;
    expect(timer.formattedTime).toBe("00:00");
  });

  test("90秒のとき 01:30 と表示されること", () => {
    const timer = new PomodoroTimer();
    timer.timeRemaining = 90;
    expect(timer.formattedTime).toBe("01:30");
  });
});

describe("PomodoroTimer - progress", () => {
  test("開始前の進捗は 0 であること", () => {
    const timer = new PomodoroTimer();
    expect(timer.progress).toBe(0);
  });

  test("半分経過後の進捗は 0.5 であること", () => {
    const timer = new PomodoroTimer();
    timer.timeRemaining = DURATIONS.work / 2;
    expect(timer.progress).toBeCloseTo(0.5);
  });

  test("残り0秒の進捗は 1 であること", () => {
    const timer = new PomodoroTimer();
    timer.timeRemaining = 0;
    expect(timer.progress).toBe(1);
  });
});

describe("PomodoroTimer - start / pause", () => {
  test("start() 後に state が running になること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    expect(timer.state).toBe("running");
    timer.pause();
  });

  test("pause() 後に state が paused になること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    timer.pause();
    expect(timer.state).toBe("paused");
  });

  test("1秒後に timeRemaining が 1 減ること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(1000);
    expect(timer.timeRemaining).toBe(DURATIONS.work - 1);
    timer.pause();
  });

  test("pause 中はカウントダウンが止まること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(3000);
    timer.pause();
    const timeAfterPause = timer.timeRemaining;
    jest.advanceTimersByTime(3000);
    expect(timer.timeRemaining).toBe(timeAfterPause);
  });

  test("running 中に start() を再度呼んでも重複しないこと", () => {
    const timer = new PomodoroTimer();
    timer.start();
    timer.start();
    jest.advanceTimersByTime(1000);
    expect(timer.timeRemaining).toBe(DURATIONS.work - 1);
    timer.pause();
  });
});

describe("PomodoroTimer - reset", () => {
  test("reset() 後に state が idle になること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    timer.reset();
    expect(timer.state).toBe("idle");
  });

  test("reset() 後に timeRemaining が初期値に戻ること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(5000);
    timer.reset();
    expect(timer.timeRemaining).toBe(DURATIONS[timer.sessionType]);
  });

  test("reset() 後にカウントダウンが止まること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    timer.reset();
    const timeAfterReset = timer.timeRemaining;
    jest.advanceTimersByTime(3000);
    expect(timer.timeRemaining).toBe(timeAfterReset);
  });
});

describe("PomodoroTimer - セッション遷移", () => {
  test("workセッション終了後に shortBreak へ遷移すること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(DURATIONS.work * 1000);
    expect(timer.sessionType).toBe("shortBreak");
  });

  test("shortBreak 終了後に work へ遷移すること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(DURATIONS.work * 1000);
    timer.start();
    jest.advanceTimersByTime(DURATIONS.shortBreak * 1000);
    expect(timer.sessionType).toBe("work");
  });

  test(`${LONG_BREAK_INTERVAL}サイクル後に longBreak へ遷移すること`, () => {
    const timer = new PomodoroTimer();
    for (let i = 0; i < LONG_BREAK_INTERVAL; i++) {
      timer.start();
      jest.advanceTimersByTime(DURATIONS.work * 1000);
      if (i < LONG_BREAK_INTERVAL - 1) {
        timer.start();
        jest.advanceTimersByTime(DURATIONS.shortBreak * 1000);
      }
    }
    expect(timer.sessionType).toBe("longBreak");
  });

  test("workセッション終了後に completedCycles が増えること", () => {
    const timer = new PomodoroTimer();
    timer.start();
    jest.advanceTimersByTime(DURATIONS.work * 1000);
    expect(timer.completedCycles).toBe(1);
  });

  test("onSessionEnd コールバックが呼ばれること", () => {
    const timer = new PomodoroTimer();
    const mockCallback = jest.fn();
    timer.onSessionEnd(mockCallback);
    timer.start();
    jest.advanceTimersByTime(DURATIONS.work * 1000);
    expect(mockCallback).toHaveBeenCalledWith("work", "shortBreak");
  });
});

describe("PomodoroTimer - onTick コールバック", () => {
  test("onTick コールバックが毎秒呼ばれること", () => {
    const timer = new PomodoroTimer();
    const mockTick = jest.fn();
    timer.onTick(mockTick);
    timer.start();
    jest.advanceTimersByTime(5000);
    expect(mockTick).toHaveBeenCalledTimes(5);
    timer.pause();
  });

  test("reset() 時に onTick コールバックが呼ばれること", () => {
    const timer = new PomodoroTimer();
    const mockTick = jest.fn();
    timer.onTick(mockTick);
    timer.reset();
    expect(mockTick).toHaveBeenCalledTimes(1);
  });
});
