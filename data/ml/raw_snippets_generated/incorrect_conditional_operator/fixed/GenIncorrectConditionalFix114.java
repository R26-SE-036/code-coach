public class GenIncorrectConditionalFix114 {
    static boolean matches(boolean valid, boolean loaded) {
        if (valid == loaded) {
            return true;
        }
        return false;
    }
}
