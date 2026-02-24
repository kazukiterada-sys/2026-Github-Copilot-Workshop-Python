const test = require("node:test");
const assert = require("node:assert/strict");
const { formatTime, getNextPhase, createTimerEngine } = require("../timer.js");

test("formatTime は mm:ss 形式を返す", () => {
    assert.equal(formatTime(0), "00:00");
    assert.equal(formatTime(65), "01:05");
});

test("作業終了時は短休憩に遷移する", () => {
    const next = getNextPhase("work", 0, 4, { work: 1500, shortBreak: 300, longBreak: 900 });
    assert.equal(next.state, "short_break");
    assert.equal(next.currentCycle, 1);
    assert.equal(next.remainingSeconds, 300);
});

test("指定サイクル到達時は長休憩に遷移する", () => {
    const next = getNextPhase("work", 3, 4, { work: 1500, shortBreak: 300, longBreak: 900 });
    assert.equal(next.state, "long_break");
    assert.equal(next.currentCycle, 4);
    assert.equal(next.remainingSeconds, 900);
});

test("engine の tick で状態が進む", () => {
    const engine = createTimerEngine({ workMinutes: 0, shortBreakMinutes: 1, longBreakMinutes: 2, cycles: 2 });
    const stateBefore = engine.getState();
    assert.equal(stateBefore.status, "stopped");

    engine.start();
    engine.tick();

    const stateAfter = engine.getState();
    assert.equal(stateAfter.phase, "short_break");
    assert.equal(stateAfter.currentCycle, 1);
});
