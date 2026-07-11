public class GenIncorrectConditionalFix071 {
    static String report(boolean verified) {
        if (verified == true) {
            return "draft";
        }
        return "expired";
    }
}
