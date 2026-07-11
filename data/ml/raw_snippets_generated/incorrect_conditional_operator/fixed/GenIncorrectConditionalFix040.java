public class GenIncorrectConditionalFix040 {
    static boolean matches(boolean valid, boolean armed) {
        if (valid == armed) {
            return true;
        }
        return false;
    }

    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }
}
