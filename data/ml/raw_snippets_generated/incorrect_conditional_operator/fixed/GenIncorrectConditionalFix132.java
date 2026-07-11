public class GenIncorrectConditionalFix132 {
    static boolean matches(boolean ready, boolean valid) {
        if (ready == valid) {
            return true;
        }
        return false;
    }
}
