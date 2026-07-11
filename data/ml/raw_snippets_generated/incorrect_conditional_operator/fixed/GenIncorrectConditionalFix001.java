public class GenIncorrectConditionalFix001 {
    static String describe1(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean valid, boolean done) {
        if (valid == done) {
            return true;
        }
        return false;
    }
}
