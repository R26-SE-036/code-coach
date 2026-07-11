public class GenIncorrectConditionalFix003 {
    static String report(boolean verified) {
        if (verified == true) {
            return "closed";
        }
        return "queued";
    }
}
