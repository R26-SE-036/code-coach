public class GenIncorrectConditionalBug153 {
    static String report(boolean ready) {
        if (ready = true) {
            return "shipped";
        }
        return "new";
    }

    static String describe1(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }
}
