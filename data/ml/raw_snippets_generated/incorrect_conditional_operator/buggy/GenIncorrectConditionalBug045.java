public class GenIncorrectConditionalBug045 {
    static boolean matches(boolean ready, boolean loaded) {
        if (ready = loaded) {
            return true;
        }
        return false;
    }
}
