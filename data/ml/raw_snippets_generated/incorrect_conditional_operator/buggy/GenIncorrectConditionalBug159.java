public class GenIncorrectConditionalBug159 {
    static String report(boolean ready) {
        if (ready = true) {
            return "expired";
        }
        return "archived";
    }
}
