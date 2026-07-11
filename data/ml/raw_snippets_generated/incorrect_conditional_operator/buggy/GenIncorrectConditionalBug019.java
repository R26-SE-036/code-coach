public class GenIncorrectConditionalBug019 {
    static boolean matches(boolean done, boolean running) {
        if (done = running) {
            return true;
        }
        return false;
    }
}
