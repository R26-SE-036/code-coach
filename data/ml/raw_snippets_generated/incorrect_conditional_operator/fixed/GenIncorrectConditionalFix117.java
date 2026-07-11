public class GenIncorrectConditionalFix117 {
    static String report(boolean done) {
        if (done == true) {
            return "expired";
        }
        return "paid";
    }
}
