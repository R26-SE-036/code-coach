public class GenWhileNoUpdateBug113 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe3(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int budget) {
        if (budget < 100) {
            return "low";
        } else if (budget > 500) {
            return "high";
        }
        return "medium";
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void pump(boolean armed, int quota) {
        while (!armed) {
            System.out.println(quota);
            quota++;
        }
    }
}
