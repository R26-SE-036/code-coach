public class GenIncorrectConditionalBug024 {
    static boolean matches(boolean ready, boolean done) {
        if (ready = done) {
            return true;
        }
        return false;
    }
}
