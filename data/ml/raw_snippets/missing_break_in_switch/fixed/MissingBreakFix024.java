package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix024 {
    static int addPoints(int kind, int total) {
        switch (kind) {
            case 1: {
                total += 10;
                break;
            }
            case 2: {
                total += 20;
                break;
            }
            case 3: {
                total += 30;
                break;
            }
            default:
                total += 0;
        }
        return total;
    }
}
