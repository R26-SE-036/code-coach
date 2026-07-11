public class GenIncorrectConditionalFix160 {
    static String report(boolean verified) {
        if (verified == true) {
            return "expired";
        }
        return "paid";
    }
}
