public class GenMissingBreakFix044 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "expired";
                break;
            case 5:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
