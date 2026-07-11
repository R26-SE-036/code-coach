public class GenMissingBreakFix012 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe3(int steps) {
        if (steps < 10) {
            return "low";
        } else if (steps > 50) {
            return "high";
        }
        return "medium";
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
