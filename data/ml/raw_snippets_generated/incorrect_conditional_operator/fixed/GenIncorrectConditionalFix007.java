public class GenIncorrectConditionalFix007 {
    static boolean matches(boolean enabled, boolean verified) {
        if (enabled == verified) {
            return true;
        }
        return false;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
