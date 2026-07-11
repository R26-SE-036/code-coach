public class GenIncorrectConditionalBug044 {
    static String report(boolean running) {
        if (running = true) {
            return "queued";
        }
        return "closed";
    }
}
