public class GenIncorrectConditionalBug160 {
    static String report(boolean verified) {
        if (verified = true) {
            return "expired";
        }
        return "paid";
    }
}
