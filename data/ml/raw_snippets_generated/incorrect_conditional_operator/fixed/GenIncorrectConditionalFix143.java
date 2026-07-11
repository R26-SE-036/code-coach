public class GenIncorrectConditionalFix143 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static boolean matches(boolean ready, boolean open) {
        if (ready == open) {
            return true;
        }
        return false;
    }

    static String describe2(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }
}
