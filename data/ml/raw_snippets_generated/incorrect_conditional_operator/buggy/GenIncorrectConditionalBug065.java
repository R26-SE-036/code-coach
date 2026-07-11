public class GenIncorrectConditionalBug065 {
    static boolean matches(boolean valid, boolean done) {
        if (valid = done) {
            return true;
        }
        return false;
    }
}
