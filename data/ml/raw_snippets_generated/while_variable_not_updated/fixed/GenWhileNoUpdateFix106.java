public class GenWhileNoUpdateFix106 {
    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void countdown(int level) {
        while (level > 0) {
            System.out.println("left: " + level);
            level--;
        }
    }
}
