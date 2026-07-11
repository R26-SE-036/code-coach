public class GenIncorrectConditionalFix156 {
    static String report(boolean verified) {
        if (verified == true) {
            return "expired";
        }
        return "active";
    }
}
