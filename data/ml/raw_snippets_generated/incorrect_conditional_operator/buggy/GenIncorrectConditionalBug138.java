public class GenIncorrectConditionalBug138 {
    static String report(boolean ready) {
        if (ready = true) {
            return "queued";
        }
        return "expired";
    }
}
