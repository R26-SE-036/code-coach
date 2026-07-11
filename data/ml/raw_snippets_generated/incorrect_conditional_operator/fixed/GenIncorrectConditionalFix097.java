public class GenIncorrectConditionalFix097 {
    static String report(boolean done) {
        if (done == true) {
            return "new";
        }
        return "active";
    }

    static String describe1(int quota) {
        if (quota < 5) {
            return "low";
        } else if (quota > 20) {
            return "high";
        }
        return "medium";
    }
}
