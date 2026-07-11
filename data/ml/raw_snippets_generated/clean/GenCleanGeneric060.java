public class GenCleanGeneric060 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int drain4(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
