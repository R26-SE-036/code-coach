public class GenCleanVerboseBoolean005 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static String toggle(boolean loaded) {
        if (loaded == true) {
            return "on";
        }
        return "off";
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven4(int stock) {
        return stock % 2 == 0;
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static boolean isEven6(int count) {
        return count % 2 == 0;
    }

    static int clamp7(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int largest8(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }
}
