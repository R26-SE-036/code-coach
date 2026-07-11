public class GenIncorrectConditionalBug157 {
    static String report(boolean verified) {
        if (verified = true) {
            return "draft";
        }
        return "closed";
    }
}
