public class GenIncorrectConditionalBug028 {
    static boolean matches(boolean done, boolean valid) {
        if (done = valid) {
            return true;
        }
        return false;
    }
}
