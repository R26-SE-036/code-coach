public class GenIncorrectConditionalFix088 {
    static boolean matches(boolean loaded, boolean valid) {
        if (loaded == valid) {
            return true;
        }
        return false;
    }
}
