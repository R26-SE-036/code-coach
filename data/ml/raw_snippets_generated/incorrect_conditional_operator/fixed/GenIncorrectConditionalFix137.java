public class GenIncorrectConditionalFix137 {
    static boolean matches(boolean valid, boolean done) {
        if (valid == done) {
            return true;
        }
        return false;
    }
}
