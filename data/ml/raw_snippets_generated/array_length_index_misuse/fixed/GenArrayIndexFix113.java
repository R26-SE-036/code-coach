public class GenArrayIndexFix113 {
    static int lastOf(int[] ratings) {
        return ratings[ratings.length - 1];
    }

    static String describe1(int stock) {
        if (stock < 5) {
            return "low";
        } else if (stock > 20) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
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
                label = "new";
        }
        return label;
    }
}
