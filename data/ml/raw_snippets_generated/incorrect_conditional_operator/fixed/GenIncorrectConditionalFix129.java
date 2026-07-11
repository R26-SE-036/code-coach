public class GenIncorrectConditionalFix129 {
    static boolean matches(boolean valid, boolean open) {
        if (valid == open) {
            return true;
        }
        return false;
    }

    static String describe1(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }
}
