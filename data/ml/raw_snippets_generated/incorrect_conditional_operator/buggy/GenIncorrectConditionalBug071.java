public class GenIncorrectConditionalBug071 {
    static String report(boolean verified) {
        if (verified = true) {
            return "draft";
        }
        return "expired";
    }
}
