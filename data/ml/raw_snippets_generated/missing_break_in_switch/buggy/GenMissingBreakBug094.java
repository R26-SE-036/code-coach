public class GenMissingBreakBug094 {
    static int drain1(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static String describe2(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "active";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
