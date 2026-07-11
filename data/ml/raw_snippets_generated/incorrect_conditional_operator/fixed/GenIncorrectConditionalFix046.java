public class GenIncorrectConditionalFix046 {
    static String report(boolean ready) {
        if (ready == true) {
            return "draft";
        }
        return "queued";
    }
}
