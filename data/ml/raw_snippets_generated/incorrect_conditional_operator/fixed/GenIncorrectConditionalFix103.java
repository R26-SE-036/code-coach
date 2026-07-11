public class GenIncorrectConditionalFix103 {
    static boolean matches(boolean open, boolean done) {
        if (open == done) {
            return true;
        }
        return false;
    }
}
