public class GenIncorrectConditionalFix115 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static boolean matches(boolean open, boolean valid) {
        if (open == valid) {
            return true;
        }
        return false;
    }
}
