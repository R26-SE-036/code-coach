public class GenIncorrectConditionalFix060 {
    static String report(boolean valid) {
        if (valid == true) {
            return "queued";
        }
        return "expired";
    }
}
