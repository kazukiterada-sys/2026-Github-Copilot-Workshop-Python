const { formatTime, TimerDisplay } = require('./timer');

describe('formatTime', () => {
    test('formats 0 seconds as 00:00', () => {
        expect(formatTime(0)).toBe('00:00');
    });

    test('formats 25 minutes as 25:00', () => {
        expect(formatTime(25 * 60)).toBe('25:00');
    });

    test('formats 90 seconds as 01:30', () => {
        expect(formatTime(90)).toBe('01:30');
    });

    test('formats 5 minutes as 05:00', () => {
        expect(formatTime(5 * 60)).toBe('05:00');
    });

    test('formats 1 second as 00:01', () => {
        expect(formatTime(1)).toBe('00:01');
    });

    test('formats 59 seconds as 00:59', () => {
        expect(formatTime(59)).toBe('00:59');
    });

    test('formats 61 seconds as 01:01', () => {
        expect(formatTime(61)).toBe('01:01');
    });
});

describe('TimerDisplay', () => {
    let display;

    beforeEach(() => {
        display = new TimerDisplay();
    });

    test('initializes with default values', () => {
        expect(display.timeRemaining).toBe(0);
        expect(display.isBreak).toBe(false);
        expect(display.cycleCount).toBe(0);
    });

    test('getDisplayText returns formatted time', () => {
        expect(display.getDisplayText(1500)).toBe('25:00');
    });

    test('getDisplayText returns 00:00 for 0 seconds', () => {
        expect(display.getDisplayText(0)).toBe('00:00');
    });

    test('update sets timeRemaining', () => {
        display.update(300, false, 1);
        expect(display.timeRemaining).toBe(300);
    });

    test('update sets isBreak', () => {
        display.update(300, true, 1);
        expect(display.isBreak).toBe(true);
    });

    test('update sets cycleCount', () => {
        display.update(300, false, 3);
        expect(display.cycleCount).toBe(3);
    });

    test('getDisplayText returns 01:30 for 90 seconds', () => {
        expect(display.getDisplayText(90)).toBe('01:30');
    });
});
