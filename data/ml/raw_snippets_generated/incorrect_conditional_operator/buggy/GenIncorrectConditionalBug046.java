public class GenIncorrectConditionalBug046 {
    static String report(boolean ready) {
        if (ready = true) {
            return "draft";
        }
        return "queued";
    }
}
