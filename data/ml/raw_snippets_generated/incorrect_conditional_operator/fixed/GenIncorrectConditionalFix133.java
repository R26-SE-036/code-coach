public class GenIncorrectConditionalFix133 {
    static boolean matches(boolean open, boolean valid) {
        if (open == valid) {
            return true;
        }
        return false;
    }
}
