public class GenIncorrectConditionalBug158 {
    static String report(boolean loaded) {
        if (loaded = true) {
            return "queued";
        }
        return "expired";
    }
}
