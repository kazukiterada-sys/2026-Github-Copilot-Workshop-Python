/**
 * Frontend timer display logic for Pomodoro Timer.
 * Pure functions and classes that can be tested with Jest.
 */

/**
 * Formats seconds into MM:SS string.
 * @param {number} seconds
 * @returns {string}
 */
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
}

/**
 * Manages the display of the Pomodoro timer in the UI.
 */
class TimerDisplay {
    constructor() {
        this.timeRemaining = 0;
        this.isBreak = false;
        this.cycleCount = 0;
    }

    /**
     * Updates the display state.
     * @param {number} timeRemaining
     * @param {boolean} isBreak
     * @param {number} cycleCount
     */
    update(timeRemaining, isBreak, cycleCount) {
        this.timeRemaining = timeRemaining;
        this.isBreak = isBreak;
        this.cycleCount = cycleCount;
    }

    /**
     * Returns formatted display text for the given time.
     * @param {number} timeRemaining
     * @returns {string}
     */
    getDisplayText(timeRemaining) {
        return formatTime(timeRemaining);
    }
}

// Export for Jest testing (Node.js environment)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatTime, TimerDisplay };
}
