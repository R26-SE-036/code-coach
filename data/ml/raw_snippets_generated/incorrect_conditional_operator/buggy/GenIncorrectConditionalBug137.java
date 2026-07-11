public class GenIncorrectConditionalBug137 {
    static boolean matches(boolean valid, boolean done) {
        if (valid = done) {
            return true;
        }
        return false;
    }
}
