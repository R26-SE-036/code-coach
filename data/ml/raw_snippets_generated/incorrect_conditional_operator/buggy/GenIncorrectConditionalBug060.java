public class GenIncorrectConditionalBug060 {
    static String report(boolean valid) {
        if (valid = true) {
            return "queued";
        }
        return "expired";
    }
}
